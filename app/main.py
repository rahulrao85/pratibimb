"""
Pratibimb FastAPI application (one port: the API under /api, the built React UI at /).

One fictional company, Meridian Global Services (Mumbai), and three seniors, each with their own Pratibimb.
Every endpoint takes ?pack= (default vendor):

  vendor  Meera Nair, Head of Delivery Operations — vendor approvals
  leads   Vikram Sethi, Head of Sales (India & APAC) — lead qualification
  spend   Kavya Iyer, Financial Controller — spend & payment exceptions

GET  /api/packs             the three packs (senior, labels, request fields)
GET  /api/health            engine status: model, LLM on/off, store, today's Gemini calls vs the daily cap
GET  /api/senior | mandate | entities | documents | decisions | lessons | requests
POST /api/decide            verdict (ADK Workflow: Mandate → Precedent ∥ Challenger ∥ Interviewer → Decider)
GET  /api/backtest          the last saved back-test for the pack; never re-runs on a page load
POST /api/backtest/run      re-run it (costs Gemini calls; only when ALLOW_BACKTEST_RUN=true)
POST /api/learner/override  the senior overrides a verdict → a new lesson + an override precedent
POST /api/demo/reset        forget what this visitor taught (the baseline stays)
GET  /api/usage             Gemini spend so far (from the local usage log)

Every browser gets its own sandbox (cookie pratibimb_sid): lessons and overrides it creates live in the Store
(Firestore on Cloud Run), survive restarts and redeploys, and never leak into another visitor's demo.
"""
import json
import os
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Body, Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents import llm
from agents.backtest import load_results, run_backtest
from agents.domain import PACK_IDS
from agents.engine import ORCHESTRATOR, PratibimbEngine
from agents.models import VerdictResponse
from agents.store import SID_PATTERN, make_store

app = FastAPI(
    title="Pratibimb API",
    description="The AI mirror of a senior decision-maker. Google Cloud AI Builder Cup 2026.",
    version="0.5.0",
)

# The UI is served from the same origin in production; only the Vite dev server needs CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

ROOT = Path(__file__).parent.parent
STORE = make_store(ROOT / ".cache" / "state")
ENGINES = {p: PratibimbEngine(pack=p, store=STORE) for p in PACK_IDS}
engine = ENGINES["vendor"]  # kept for callers that only know the vendor pack
SID_COOKIE = "pratibimb_sid"


def sandbox(request: Request, response: Response) -> str:
    """This visitor's sandbox id (cookie). New visitors get a fresh one."""
    sid = request.cookies.get(SID_COOKIE)
    if not sid or not SID_PATTERN.match(sid):
        sid = uuid.uuid4().hex
        response.set_cookie(SID_COOKIE, sid, max_age=90 * 24 * 3600, httponly=True, samesite="lax",
                            secure=request.url.scheme == "https")
    return sid


def get_engine(pack: str = Query("vendor")) -> PratibimbEngine:
    if pack not in ENGINES:
        raise HTTPException(status_code=404, detail=f"Unknown pack '{pack}'. Packs: {', '.join(PACK_IDS)}")
    return ENGINES[pack]


def box(sid: str, e: PratibimbEngine) -> str:
    """The visitor's sandbox for this pack (vendor keeps the plain id)."""
    return sid if e.pack == "vendor" else f"{e.pack}-{sid}"


_trace_provider = None


def _flush_traces() -> None:
    """Cloud Run throttles CPU once a response is sent, so export this request's spans before returning."""
    if _trace_provider is not None:
        try:
            _trace_provider.force_flush(timeout_millis=3000)
        except Exception:
            pass


def _setup_tracing() -> None:
    """Export ADK and Gemini spans to Cloud Trace (PRATIBIMB_TRACE=cloud on Cloud Run)."""
    global _trace_provider
    if os.getenv("PRATIBIMB_TRACE", "").lower() != "cloud":
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(resource=Resource.create({"service.name": "pratibimb"}))
        provider.add_span_processor(BatchSpanProcessor(CloudTraceSpanExporter(project_id=llm.PROJECT)))
        trace.set_tracer_provider(provider)
        _trace_provider = provider
    except Exception as e:  # tracing must never stop the app
        print(f"Cloud Trace disabled: {e}")


@app.on_event("startup")
def _startup() -> None:
    _setup_tracing()
    if llm.enabled():
        threading.Thread(target=llm.warm_up, daemon=True).start()  # first verdict after a cold start isn't slow


def _json(e: PratibimbEngine, filename: str) -> Dict[str, Any]:
    path = e.data_dir / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{filename} not found for pack {e.pack}")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/packs")
def get_packs():
    return {"packs": [ENGINES[p].domain.meta for p in PACK_IDS], "company": "Meridian Global Services (Mumbai)"}


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "pratibimb-engine",
        "orchestrator": ORCHESTRATOR,
        "llm_enabled": llm.enabled(),
        "model": llm.MODEL if llm.enabled() else "rules",
        "fallback_models": llm.FALLBACK_MODELS,
        "backend": "vertex-ai" if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true" else "gemini-api",
        "store": STORE.kind,
        "gemini_calls_today": llm.calls_today(),
        "seniors": {p: ENGINES[p].senior.get("name") for p in PACK_IDS},
        "senior": engine.senior.get("name"),
    }


@app.get("/api/senior")
def get_senior(e: PratibimbEngine = Depends(get_engine)):
    return e.senior


@app.get("/api/mandate")
def get_mandate(e: PratibimbEngine = Depends(get_engine)):
    return _json(e, "mandate.json")


@app.get("/api/entities")
def get_entities(e: PratibimbEngine = Depends(get_engine)):
    """Vendors, prospects or suppliers, with their history."""
    if e.pack == "vendor":
        return {"entities": _json(e, "vendors.json")["vendors"]}
    return _json(e, "entities.json")


@app.get("/api/vendors")
def get_vendors():
    return _json(engine, "vendors.json")


@app.get("/api/documents")
def get_documents(e: PratibimbEngine = Depends(get_engine)):
    return {"documents": list(e.challenger_agent.contracts.values())}


@app.get("/api/contracts")
def get_contracts():
    return _json(engine, "contracts.json")


@app.get("/api/decisions")
def get_decisions(sid: str = Depends(sandbox), e: PratibimbEngine = Depends(get_engine)):
    # Holdouts are the senior's back-test answers; they are never served or retrieved.
    decisions = e.memory_for(box(sid, e))
    return {"decisions": decisions, "total": len(decisions)}


@app.get("/api/lessons")
def get_lessons(sid: str = Depends(sandbox), e: PratibimbEngine = Depends(get_engine)):
    return {"lessons": list(e.lessons_for(box(sid, e)).values())}


@app.get("/api/sources")
def get_sources(sid: str = Depends(sandbox), e: PratibimbEngine = Depends(get_engine)):
    """Every citable ID for this senior, resolved to readable text: rules, lessons, past decisions, document clauses."""
    out: Dict[str, Dict[str, str]] = {}
    for r in e.mandate.rules:
        out[r["id"]] = {"kind": "Mandate rule", "title": f"{r['id']} → {r['then'].replace('_', ' ')}", "text": r.get("reason", "")}
    for lid, l in e.lessons_for(box(sid, e)).items():
        taught = " (taught by an override)" if l.get("override") else ""
        out[lid] = {"kind": "Lesson" + taught, "title": l.get("title", lid),
                    "text": f"{l.get('rule', '')} When: {l.get('trigger', '')}. Action: {l.get('action_required', '')}"}
    for d in e.memory_for(box(sid, e)):
        name = d.get("vendor_name") or d.get("entity_name") or ""
        text = f"{d.get('decision', '').replace('_', ' ').capitalize()}: {d.get('decision_note', '')} Outcome: {d.get('outcome', '')}"
        if d.get("mistake"):
            text += f" Lesson learnt: {d.get('mistake_note', '')}"
        out[d["id"]] = {"kind": "Past decision" + (" (a mistake)" if d.get("mistake") else ""), "title": f"{d['id']} · {name} · {d.get('date', '')}", "text": text}
    for did, doc in e.challenger_agent.contracts.items():
        for c in doc.get("clauses", []):
            out[f"{did} §{c['number']}"] = {"kind": "Document clause", "title": f"{doc.get('title', did)} — §{c['number']} {c.get('title', '')}",
                                            "text": c.get("text", "")}
    return {"sources": out}


@app.get("/api/requests")
def get_requests(e: PratibimbEngine = Depends(get_engine)):
    # The demo inbox shows requests only; expected verdicts stay out of the UI.
    data = _json(e, "requests.json")
    return {"requests": [{k: v for k, v in r.items() if k in e.request_fields} for r in data.get("requests", [])]}


@app.post("/api/decide", response_model=VerdictResponse)
def decide(request: Dict[str, Any] = Body(...), sid: str = Depends(sandbox), e: PratibimbEngine = Depends(get_engine)):
    try:
        e.domain.request_model(**{k: v for k, v in request.items() if k in e.request_fields})  # validate
    except Exception as err:
        raise HTTPException(status_code=422, detail=str(err))
    try:
        return e.decide(request, sandbox=box(sid, e))
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        _flush_traces()


@app.get("/api/backtest")
def get_backtest(e: PratibimbEngine = Depends(get_engine)):
    res = load_results(e.pack)
    if not res:
        raise HTTPException(status_code=404, detail=f"No back-test results yet. Run: python -m agents.backtest --pack {e.pack}")
    return res


@app.post("/api/backtest/run")
def rerun_backtest(e: PratibimbEngine = Depends(get_engine)):
    if os.getenv("ALLOW_BACKTEST_RUN", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="Re-running the back-test is disabled on this deployment.")
    return run_backtest(verbose=False, pack=e.pack)


class OverridePayload(BaseModel):
    request_id: str
    engine_verdict: str
    senior_decision: str
    senior_override_note: str
    proposed_rule: str = ""
    senior_name: Optional[str] = None
    request: Optional[Dict[str, Any]] = None  # the request overridden; looked up by id when omitted


@app.post("/api/learner/override")
def record_override(payload: OverridePayload, sid: str = Depends(sandbox), e: PratibimbEngine = Depends(get_engine)):
    req = payload.request
    if req is None:
        req = next((r for r in _json(e, "requests.json").get("requests", []) if r["id"] == payload.request_id), None)
    if req is not None:
        req = {k: v for k, v in req.items() if k in e.request_fields}
    try:
        lesson = e.learner_agent.record_override(
            request_id=payload.request_id,
            engine_verdict=payload.engine_verdict,
            senior_decision=payload.senior_decision,
            senior_override_note=payload.senior_override_note,
            proposed_rule=payload.proposed_rule,
            senior_name=payload.senior_name or e.senior.get("name"),
            request=req,
            sandbox=box(sid, e),
        )
        return {"status": "success", "lesson": lesson}
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        _flush_traces()


@app.post("/api/demo/reset")
def reset_demo(sid: str = Depends(sandbox), e: PratibimbEngine = Depends(get_engine)):
    return {"status": "reset", "lessons": e.learner_agent.reset(box(sid, e))}


@app.get("/api/usage")
def usage():
    return {"total": llm.cost_report(), "today": llm.calls_today()}


UI_DIST = ROOT / "ui" / "dist"
if UI_DIST.exists():
    app.mount("/", StaticFiles(directory=str(UI_DIST), html=True), name="ui")
