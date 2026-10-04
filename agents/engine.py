"""
Pratibimb Agent Engine, orchestrated with a Google ADK Workflow (graph of nodes):

    START → mandate → ┌ precedent   ┐ → gather (join) → decider
                      ├ challenger  ┤
                      └ interviewer ┘

  mandate      deterministic guardrails from mandate.json: the floor the verdict may never go below
  precedent    Gemini judges which past decisions and lessons apply     ┐
  challenger   Gemini reads the contract clauses and the request         ├ run in parallel by the workflow
  interviewer  Gemini asks what Meera would ask                          ┘
  decider      Gemini gives the verdict inside the mandate; citations validated
  (Learner runs separately when the senior overrides a verdict.)

The same graph runs with PRATIBIMB_LLM=off: every node then uses its deterministic rules (the back-test baseline).
What a sandbox has been taught (lessons, override precedents) comes from the Store (Firestore on Cloud Run).
"""
import asyncio
import contextvars
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from google.adk.agents.context import Context
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.workflow import START, JoinNode, Workflow, node
from google.genai import types

from agents import llm
from agents.decider import DeciderAgent
from agents.domain import GenericRequest, make_domain
from agents.interviewer import InterviewerAgent
from agents.learner import LearnerAgent
from agents.mandate import MandateResult
from agents.models import VendorRequest, VerdictResponse
from agents.precedent import PrecedentAgent
from agents.store import make_store

ORCHESTRATOR = "Google ADK Workflow"
ROOT = Path(__file__).resolve().parent.parent


@dataclass
class _Run:
    """Everything one verdict needs, shared by the workflow's nodes."""
    engine: "PratibimbEngine"
    req: Any  # VendorRequest or GenericRequest, depending on the pack
    sandbox: str
    lessons: Dict[str, Dict[str, Any]]
    overrides: List[Dict[str, Any]]
    mode: str                                   # "llm" or "rules"
    t0: float = field(default_factory=time.perf_counter)
    m: Optional[MandateResult] = None
    case: str = ""
    rule_precedents: list = field(default_factory=list)
    rule_lessons: list = field(default_factory=list)
    precedents: list = field(default_factory=list)
    lessons_applied: list = field(default_factory=list)
    challenges: list = field(default_factory=list)
    clause_cits: list = field(default_factory=list)
    questions: list = field(default_factory=list)
    cap_hit: bool = False
    verdict: Optional[VerdictResponse] = None
    trace: List[dict] = field(default_factory=list)
    trace_id: str = ""


_RUN: contextvars.ContextVar = contextvars.ContextVar("pratibimb_run")


def _timed(name: str):
    """Record each node's start and duration for the timeline shown on the decision file."""
    def wrap(fn):
        async def inner(ctx: Context, node_input: Any):  # ADK binds parameters by this signature: no functools.wraps
            run: _Run = _RUN.get()
            start = time.perf_counter()
            try:
                return await fn(run, ctx)
            finally:
                run.trace.append({"node": name, "start_ms": int((start - run.t0) * 1000),
                                  "ms": int((time.perf_counter() - start) * 1000)})
        return node(inner, name=name)
    return wrap


async def _llm(run: _Run, fn, *args):
    """Run a blocking Gemini call off the event loop (so the parallel branches really overlap)."""
    try:
        return await asyncio.to_thread(fn, *args)  # copies context: cost meter + trace span follow the call
    except llm.CapReached:
        run.cap_hit = True
        return None


@_timed("mandate")
async def _mandate(run: _Run, ctx: Context):
    e = run.engine
    run.rule_precedents, run.rule_lessons = e.precedent_agent.retrieve(run.req, overrides=run.overrides)
    has_precedent = any(p.similarity >= 0.5 for p in run.rule_precedents)
    run.m = e.mandate.evaluate(run.req, has_precedent=has_precedent, auto_renewal=e.challenger_agent.has_auto_renewal(run.req))
    if run.m.floor == "refuse":
        run.mode = "rules"  # out of scope: no model call at all
    run.case = e._case_text(run.req)
    ctx.state["mandate_floor"] = run.m.floor
    return {"floor": run.m.floor, "rules": run.m.rule_ids}


@_timed("precedent")
async def _precedent(run: _Run, ctx: Context):
    if run.mode == "llm":
        out = await _llm(run, run.engine.precedent_agent.reason, run.case, run.req, run.lessons, 6, run.overrides)
        if out:
            run.precedents, run.lessons_applied = out
    return {"precedents": [p.decision_id for p in run.precedents]}


@_timed("challenger")
async def _challenger(run: _Run, ctx: Context):
    e = run.engine
    if run.mode == "llm":
        out = await _llm(run, e.challenger_agent.challenge_llm, run.case, run.req)
        if out:
            run.challenges, run.clause_cits = out
    else:
        run.challenges, run.clause_cits = e.challenger_agent.challenge(run.req)
    return {"findings": len(run.challenges)}


@_timed("interviewer")
async def _interviewer(run: _Run, ctx: Context):
    if run.mode == "llm":
        out = await _llm(run, run.engine.interviewer_agent.formulate_questions_llm, run.case, run.engine.senior, run.lessons)
        run.questions = out or []
    return {"questions": len(run.questions)}


@_timed("decider")
async def _decider(run: _Run, ctx: Context):
    e = run.engine
    if run.mode == "llm" and not run.cap_hit:
        run.verdict = await _llm(
            run, e.decider_agent.decide_llm, run.case, run.req, run.m, run.precedents, run.lessons_applied, run.lessons,
            run.challenges, run.questions, run.clause_cits, e._valid_ids(run.lessons, run.overrides))
    if run.verdict is None:
        run.verdict = e._decide_rules(run)
        if run.cap_hit:
            run.verdict.engine = "rules (daily Gemini cap reached)"
    ctx.state["verdict"] = run.verdict.verdict
    return {"verdict": run.verdict.verdict}


WORKFLOW = Workflow(
    name="pratibimb",
    edges=[(START, _mandate, (_precedent, _challenger, _interviewer), JoinNode(name="gather"), _decider)],
)


class PratibimbEngine:
    """One senior's Pratibimb. pack = vendor (Meera Nair) | leads (Vikram Sethi) | spend (Kavya Iyer)."""

    def __init__(self, data_dir: Path = None, store=None, pack: str = "vendor"):
        self.pack = pack
        self.domain = make_domain(pack, data_dir)
        self.data_dir = self.domain.data_dir
        self.store = store or make_store(ROOT / ".cache" / "state")
        persona = self.domain.persona
        self.mandate = self.domain.mandate
        self.precedent_agent = PrecedentAgent(data_dir=self.data_dir, persona=persona,
                                              scorer=self.domain.score, briefer=self.domain.brief)
        self.challenger_agent = self.domain.challenger
        self.interviewer_agent = InterviewerAgent(persona)
        self.decider_agent = DeciderAgent(persona, headline=None if pack == "vendor" else self.domain.rules_headline)
        self.learner_agent = LearnerAgent(data_dir=self.data_dir, store=self.store, domain=self.domain)
        self.senior = self.domain.senior
        if self.domain.request_model is GenericRequest:
            self.request_fields = {"id", "description"} | set(self.domain.request_keys)
        else:
            self.request_fields = set(VendorRequest.model_fields)

    # ---------- memory for one sandbox ----------

    def lessons_for(self, sandbox: str) -> Dict[str, Dict[str, Any]]:
        return self.precedent_agent.load_lessons(self.store.lessons(sandbox))

    def memory_for(self, sandbox: str) -> List[Dict[str, Any]]:
        return self.precedent_agent.memory(self.store.overrides(sandbox))

    def _valid_ids(self, lessons: Dict[str, Any], overrides: List[Dict[str, Any]] = ()) -> Set[str]:
        ids = {r["id"] for r in self.mandate.rules} | set(lessons) | set(self.precedent_agent.by_id(overrides))
        for cid, c in self.challenger_agent.contracts.items():
            ids |= {f"{cid} §{cl['number']}" for cl in c.get("clauses", [])}
        return ids

    def _case_text(self, req) -> str:
        return self.domain.case_text(req)

    # ---------- deciding ----------

    def _decide_rules(self, run: _Run) -> VerdictResponse:
        m, req = run.m, run.req
        if m.floor == "refuse":
            v = self.decider_agent.decide_rules(req, m, [], [], [], [], [])
            v.headline = "Refuse: rating people's performance is outside Pratibimb's scope"
            v.reasoning = "Pratibimb never rates people (mandate rule M-R13)."
            return v
        if not run.challenges and not run.clause_cits:
            run.challenges, run.clause_cits = self.challenger_agent.challenge(req)
        questions = self.domain.rules_questions(req, run.challenges)
        return self.decider_agent.decide_rules(req, m, run.rule_precedents, run.challenges, questions,
                                               run.rule_lessons, run.clause_cits)

    async def _run_workflow(self, run: _Run) -> VerdictResponse:
        _RUN.set(run)
        runner = Runner(app_name="pratibimb", node=WORKFLOW, session_service=InMemorySessionService(),
                        auto_create_session=True)
        message = types.Content(role="user", parts=[types.Part(text=run.req.model_dump_json())])
        with llm._tracer().start_as_current_span("pratibimb.workflow") as span:
            span.set_attribute("pratibimb.request_id", run.req.id)
            ctx_ = span.get_span_context()
            run.trace_id = format(ctx_.trace_id, "032x") if ctx_ and ctx_.trace_id else ""
            async for _ in runner.run_async(user_id=run.sandbox, session_id=uuid.uuid4().hex, new_message=message):
                pass
        return run.verdict

    def decide(self, request_data: Dict[str, Any], sandbox: str = "local") -> VerdictResponse:
        meter = llm.start_meter()
        # Only real request fields reach the agents (never expected_* answers or grading notes).
        req = self.domain.request_model(**{k: v for k, v in request_data.items() if k in self.request_fields})
        taught, overrides = self.store.lessons(sandbox), self.store.overrides(sandbox)
        run = _Run(engine=self, req=req, sandbox=sandbox, lessons=self.precedent_agent.load_lessons(taught),
                   overrides=overrides, mode="llm" if llm.enabled() else "rules")
        try:
            v = asyncio.run(self._run_workflow(run))
            if v is None:
                raise RuntimeError("workflow finished without a verdict")
        except Exception as e:  # never leave the user with an error page: fall back to the mandate rules
            if run.m is None:
                run.rule_precedents, run.rule_lessons = self.precedent_agent.retrieve(req, overrides=overrides)
                run.m = self.mandate.evaluate(req, has_precedent=any(p.similarity >= 0.5 for p in run.rule_precedents),
                                              auto_renewal=self.challenger_agent.has_auto_renewal(req))
            run.challenges, run.clause_cits = [], []
            v = self._decide_rules(run)
            v.engine = f"rules (Gemini unavailable: {type(e).__name__})"
        cost = llm.meter_total(meter)
        v.cost_usd, v.cost_inr = cost["cost_usd"], cost["cost_inr"]
        v.elapsed_ms = int((time.perf_counter() - run.t0) * 1000)
        v.agent_trace = sorted(run.trace, key=lambda t: (t["start_ms"], t["node"]))
        v.orchestrator = ORCHESTRATOR
        v.trace_id = run.trace_id
        try:
            self.store.log_verdict(sandbox, {"pack": self.pack, "request_id": req.id, "verdict": v.verdict,
                                             "engine": v.engine, "cost_usd": v.cost_usd, "elapsed_ms": v.elapsed_ms})
        except Exception:
            pass  # the log must never break a verdict
        return v

    def evaluate_live_requests(self) -> Dict[str, Any]:
        with open(self.data_dir / "requests.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        results = []
        for r in data.get("requests", []):
            v = self.decide(r)
            results.append({
                "request_id": r["id"], "vendor_name": r.get("vendor_name"), "expected_verdict": r.get("expected_verdict"),
                "actual_verdict": v.verdict, "headline": v.headline, "citations": v.citations,
                "matches_expected": v.verdict == r.get("expected_verdict"),
            })
        return {"live_demo_results": results}
