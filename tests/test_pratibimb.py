"""
Pratibimb test suite. Runs free: no Gemini calls (rules mode, or Gemini replaced by a stub).

    uv run pytest -q

What it proves:
  - the data is consistent and the back-test is blind (holdouts never in memory, no answer fields in requests);
  - the mandate floor: Gemini can make a verdict stricter, never looser, and the record shows what it wanted;
  - invented citations are dropped and listed;
  - the ADK workflow really runs the three agents in parallel, and records a timeline;
  - an override writes a lesson + precedent that the next verdict sees, per sandbox; it survives a restart
    (a new engine on the same store) and never leaks into another sandbox; reset restores the baseline;
  - the API serves no answers, gives every browser its own sandbox, never re-runs the paid back-test on request.
"""
import json
import shutil
import time
from pathlib import Path

import pytest

from agents import llm
from agents.backtest import REQUEST_KEYS, build_request
from agents.decider import DeciderAgent, allowed_verdicts
from agents.engine import PratibimbEngine
from agents.mandate import STRICTNESS, Mandate
from agents.models import DeciderOutput, LessonJudgement, VendorRequest
from agents.store import FileStore

DATA = Path(__file__).resolve().parent.parent / "data"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


@pytest.fixture
def rules_only(monkeypatch):
    monkeypatch.setenv("PRATIBIMB_LLM", "off")


@pytest.fixture
def sandbox(tmp_path):
    """A private copy of data/, so tests never touch the real files."""
    for f in DATA.glob("*.json"):
        if not f.name.startswith("backtest_results"):
            shutil.copy(f, tmp_path / f.name)
    return tmp_path


def make_engine(data_dir):
    return PratibimbEngine(data_dir=data_dir, store=FileStore(data_dir / "state"))


# ---------- data and blindness ----------

def test_data_counts():
    decisions = load("decisions.json")["decisions"]
    assert len(decisions) == 45
    assert sum(d["holdout"] for d in decisions) == 15
    assert sum(d["mistake"] for d in decisions) == 4
    assert {l["id"] for l in load("lessons.json")["lessons"]} == {f"L0{i}" for i in range(1, 7)}


def test_holdouts_never_in_memory(sandbox):
    engine = make_engine(sandbox)
    holdout_ids = {d["id"] for d in load("decisions.json")["decisions"] if d["holdout"]}
    assert not holdout_ids & set(engine.precedent_agent.by_id())


def test_backtest_requests_carry_no_answers():
    decisions = {d["id"]: d for d in load("decisions.json")["decisions"]}
    for case in load("backtest.json")["backtest_cases"]:
        req = build_request(decisions[case["decision_id"]], case)
        assert set(req) <= set(REQUEST_KEYS) | {"id", "description"}
        assert not req["id"].startswith("DEC-")
        text = req["description"].lower()
        assert case["expected_verdict"].replace("_", " ") not in text  # the requester never states the verdict


def test_demo_requests_exist_and_validate():
    for r in load("requests.json")["requests"]:
        VendorRequest(**{k: v for k, v in r.items() if k in VendorRequest.model_fields})


# ---------- mandate floor ----------

@pytest.mark.parametrize("req, floor", [
    ({"type": "vendor_renewal", "vendor_id": "V-PRINTPRO", "value_inr": 280000}, "approve"),
    ({"type": "vendor_renewal", "vendor_id": "V-NORTHGATE", "value_inr": 300000, "sla_breaches_12m": 1}, "approve_with_conditions"),
    ({"type": "vendor_renewal", "vendor_id": "V-BRIGHTLINE", "value_inr": 400000, "sla_breaches_12m": 2}, "escalate"),
    ({"type": "vendor_renewal", "vendor_id": "V-ZENITH", "value_inr": 600000}, "escalate"),           # above ₹5L
    ({"type": "vendor_renewal", "vendor_id": "V-ZENITH", "value_inr": 400000, "price_increase_pct": 10}, "escalate"),
    ({"type": "vendor_renewal", "vendor_id": "V-ZENITH", "value_inr": 400000, "term_months": 24}, "escalate"),
    ({"type": "vendor_renewal", "vendor_id": "V-UNKNOWN", "value_inr": 100000}, "escalate"),          # no history
    ({"type": "vendor_onboarding", "vendor_id": "V-PARLO", "value_inr": 750000, "handles_client_data": True}, "escalate"),
    ({"type": "one_time_spend", "vendor_id": "V-CLEARDESK", "value_inr": 30000}, "approve"),
    ({"type": "out_of_scope", "vendor_id": "OUT_OF_SCOPE", "value_inr": 0}, "refuse"),
])
def test_mandate_floor(req, floor):
    m = Mandate(DATA).evaluate(VendorRequest(id="T", **req), has_precedent=True)
    assert m.floor == floor


def test_allowed_verdicts_never_looser_than_floor():
    for floor in STRICTNESS:
        for v in allowed_verdicts(floor):
            assert STRICTNESS.index(v) >= STRICTNESS.index(floor) or floor in ("ask", "escalate")
        assert "approve" not in allowed_verdicts(floor) or floor == "approve"


def test_gemini_cannot_loosen_the_floor_or_invent_citations(monkeypatch):
    """Stub Gemini to answer 'approve' with a made-up citation on a case whose floor is escalate."""
    monkeypatch.setattr(llm, "generate_json", lambda *a, **k: DeciderOutput(
        verdict="approve", headline="Approve it", confidence="high", reasoning="Looks fine.",
        recommended_conditions=[], citations=["DEC-9999", "M-R3"]))
    req = VendorRequest(id="T", type="vendor_renewal", vendor_id="V-BRIGHTLINE", value_inr=400000, sla_breaches_12m=2)
    m = Mandate(DATA).evaluate(req)
    assert m.floor == "escalate"
    v = DeciderAgent().decide_llm("case", req, m, [], [], {}, [], [], [], valid_ids={"M-R3", "DEC-0087"})
    assert v.verdict == "escalate"            # forced back inside the allowed set
    assert v.llm_verdict == "approve"         # ...and the record shows what the model wanted
    assert "DEC-9999" not in v.citations      # invented ID dropped
    assert v.dropped_citations == ["DEC-9999"]
    assert "M-R3" in v.citations


def test_lessons_and_conditions_survive_the_decider(monkeypatch):
    monkeypatch.setattr(llm, "generate_json", lambda *a, **k: DeciderOutput(
        verdict="approve_with_conditions", headline="Approve with conditions", confidence="high", reasoning="One breach.",
        recommended_conditions=[], citations=[]))
    req = VendorRequest(id="T", type="vendor_renewal", vendor_id="V-NORTHGATE", value_inr=300000, sla_breaches_12m=1)
    m = Mandate(DATA).evaluate(req)
    lessons = {"L01": {"rule": "r", "action_required": "a"}}
    v = DeciderAgent().decide_llm("case", req, m, [], [LessonJudgement(lesson_id="L01", why="breach")], lessons, [], [], [],
                                  valid_ids={"M-R2", "L01"})
    assert "L01" in v.citations and v.lessons_applied == ["L01"]
    text = " ".join(v.recommended_conditions).lower()
    assert "service credit" in text and "90-day" in text   # mandate-required conditions merged in


# ---------- engine (ADK workflow) ----------

def test_rules_engine_decides_demo_requests(rules_only, sandbox):
    engine = make_engine(sandbox)
    verdicts = {r["id"]: engine.decide(r) for r in load("requests.json")["requests"]}
    assert verdicts["REQ-001"].verdict == "approve"
    assert verdicts["REQ-002"].verdict == "escalate"
    assert all(v.engine == "rules" and v.citations and v.cost_usd == 0 for v in verdicts.values())
    v = verdicts["REQ-002"]
    assert v.orchestrator == "Google ADK Workflow"
    assert {t["node"] for t in v.agent_trace} == {"mandate", "precedent", "challenger", "interviewer", "decider"}


def test_adk_workflow_runs_agents_in_parallel(monkeypatch, sandbox):
    """Three agents that each take 0.4 s must finish together, well under the 1.2 s of running them in turn."""
    monkeypatch.setenv("PRATIBIMB_LLM", "on")
    engine = make_engine(sandbox)

    def slow(result):
        def f(*a, **k):
            time.sleep(0.4)
            return result
        return f
    monkeypatch.setattr(engine.precedent_agent, "reason", slow(([], [])))
    monkeypatch.setattr(engine.challenger_agent, "challenge_llm", slow(([], [])))
    monkeypatch.setattr(engine.interviewer_agent, "formulate_questions_llm", slow([]))
    monkeypatch.setattr(llm, "generate_json", lambda *a, **k: DeciderOutput(
        verdict="escalate", headline="Escalate", confidence="high", reasoning="r", recommended_conditions=[], citations=[]))
    v = engine.decide(load("requests.json")["requests"][1])
    branches = [t for t in v.agent_trace if t["node"] in ("precedent", "challenger", "interviewer")]
    assert len(branches) == 3 and v.engine == llm.MODEL
    span = max(t["start_ms"] + t["ms"] for t in branches) - min(t["start_ms"] for t in branches)
    assert span < 900, f"branches ran one after another ({span} ms)"


def test_daily_cap_falls_back_to_rules(monkeypatch, sandbox):
    monkeypatch.setenv("PRATIBIMB_LLM", "on")

    def capped(*a, **k):
        raise llm.CapReached("cap")
    monkeypatch.setattr(llm, "generate_json", capped)
    v = make_engine(sandbox).decide(load("requests.json")["requests"][0])
    assert v.engine.startswith("rules") and "cap" in v.engine


# ---------- learning loop ----------

def test_override_creates_lesson_and_precedent_then_reset(rules_only, sandbox):
    engine = make_engine(sandbox)
    req = load("requests.json")["requests"][0]
    lesson = engine.learner_agent.record_override(
        request_id=req["id"], engine_verdict="approve", senior_decision="ask",
        senior_override_note="Key account manager left; hold until a replacement is named.", request=req, sandbox="judge-a")
    assert lesson["id"] == "L07"
    assert "L07" in engine.lessons_for("judge-a")
    assert "OVR-001" in {d["id"] for d in engine.memory_for("judge-a")}     # her override is now precedent
    assert "L07" not in engine.lessons_for("judge-b")                       # never leaks to another visitor
    restarted = make_engine(sandbox)                                         # a new revision on the same store
    assert "L07" in restarted.lessons_for("judge-a")
    assert engine.learner_agent.reset("judge-a") == 6
    assert "OVR-001" not in {d["id"] for d in engine.memory_for("judge-a")}
    assert "L07" not in engine.lessons_for("judge-a")
    assert len(load("lessons.json")["lessons"]) == 6                         # baseline file untouched


# ---------- API ----------

@pytest.fixture
def client(rules_only):
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


def test_api_serves_no_answers(client):
    for r in client.get("/api/requests").json()["requests"]:
        assert not any(k.startswith("expected") for k in r)
    ids = {d["id"] for d in client.get("/api/decisions").json()["decisions"]}
    assert not any(d["id"] in ids for d in load("decisions.json")["decisions"] if d["holdout"])


def test_api_backtest_is_served_not_rerun(client):
    res = client.get("/api/backtest")
    assert res.status_code == 200 and len(res.json()["cases"]) == 15
    assert client.post("/api/backtest/run").status_code == 403


def test_api_gives_each_browser_its_own_sandbox(rules_only):
    from fastapi.testclient import TestClient
    from app.main import app
    a, b = TestClient(app), TestClient(app)
    req = load("requests.json")["requests"][0]
    assert "__session" in a.get("/api/lessons").cookies
    r = a.post("/api/learner/override", json={"request_id": req["id"], "engine_verdict": "approve",
                                             "senior_decision": "ask", "senior_override_note": "Key person left."})
    lesson_id = r.json()["lesson"]["id"]
    assert lesson_id in {l["id"] for l in a.get("/api/lessons").json()["lessons"]}
    assert lesson_id not in {l["id"] for l in b.get("/api/lessons").json()["lessons"]}
    assert a.post("/api/demo/reset").json()["lessons"] == 6
    assert lesson_id not in {l["id"] for l in a.get("/api/lessons").json()["lessons"]}


def test_api_decide_and_health(client):
    req = load("requests.json")["requests"][1]
    body = {k: v for k, v in req.items() if k in VendorRequest.model_fields}
    v = client.post("/api/decide", json=body).json()
    assert v["verdict"] == "escalate" and v["engine"] == "rules"
    assert v["orchestrator"] == "Google ADK Workflow"
    h = client.get("/api/health").json()
    assert h["status"] == "healthy" and h["llm_enabled"] is False and h["store"] in ("file", "firestore")


# ---------- decision packs: Vikram (leads) and Kavya (spend) ----------

PACKS = {"leads": DATA / "packs" / "leads", "spend": DATA / "packs" / "spend"}


def pack_engine(pack, tmp_path):
    return PratibimbEngine(pack=pack, store=FileStore(tmp_path / "state"))


@pytest.mark.parametrize("pack", ["leads", "spend"])
def test_pack_data_is_complete_and_blind(pack):
    d = PACKS[pack]
    decisions = json.loads((d / "decisions.json").read_text(encoding="utf-8"))["decisions"]
    assert sum(not x["holdout"] for x in decisions) == 30 and sum(x["holdout"] for x in decisions) == 15
    assert sum(x["mistake"] for x in decisions) == 4
    cases = json.loads((d / "backtest.json").read_text(encoding="utf-8"))["backtest_cases"]
    assert [c["decision_id"] for c in cases] == [x["id"] for x in decisions if x["holdout"]]
    for r in json.loads((d / "requests.json").read_text(encoding="utf-8"))["requests"]:
        assert not any(k.startswith("expected") for k in r)


@pytest.mark.parametrize("pack, req, floor", [
    ("leads", {"type": "inbound_enquiry", "entity_id": "A-COBALT", "amount_inr": 3000000, "service_line": "it_service_desk",
               "budget_confirmed": True, "decision_maker_engaged": True, "payment_terms_days": 45, "government_entity": False}, "approve"),
    ("leads", {"type": "inbound_enquiry", "entity_id": "A-COBALT", "amount_inr": 3000000, "service_line": "it_service_desk",
               "budget_confirmed": False, "decision_maker_engaged": True, "payment_terms_days": 45, "government_entity": False}, "ask"),
    ("leads", {"type": "rfp_invitation", "entity_id": "A-HELIOS", "amount_inr": 9000000, "service_line": "customer_support",
               "budget_confirmed": True, "decision_maker_engaged": True, "payment_terms_days": 45, "government_entity": False}, "escalate"),
    ("leads", {"type": "inbound_enquiry", "entity_id": "A-ZEPHYR", "amount_inr": 3000000, "service_line": "customer_support",
               "budget_confirmed": True, "decision_maker_engaged": True, "payment_terms_days": 45, "government_entity": False}, "refuse"),
    ("spend", {"type": "invoice_without_po", "entity_id": "P-COOLAIR", "amount_inr": 80000, "grn_matched": True, "gst_in_2b": True}, "approve_with_conditions"),
    ("spend", {"type": "invoice_without_po", "entity_id": "P-COOLAIR", "amount_inr": 180000, "grn_matched": True, "gst_in_2b": True}, "escalate"),
    ("spend", {"type": "price_variance", "entity_id": "P-PRINTEX", "amount_inr": 20000, "variance_pct": 2, "grn_matched": False, "gst_in_2b": True}, "ask"),
    ("spend", {"type": "price_variance", "entity_id": "P-PRINTEX", "amount_inr": 20000, "variance_pct": 2, "grn_matched": True, "gst_in_2b": True,
               "supplier_msme": True, "days_since_invoice": 38}, "approve_with_conditions"),   # MSME 45-day rule
    ("spend", {"type": "expense_exception", "entity_id": "P-EMPLOYEE", "amount_inr": 5000, "receipt_attached": True,
               "requester_is_approver": True}, "refuse"),                                       # segregation of duties
    ("spend", {"type": "advance_payment", "entity_id": "P-CLOUDNINE", "amount_inr": 100000, "advance_pct": 20}, "escalate"),  # < 12 months
])
def test_pack_mandate_floor(pack, req, floor, tmp_path):
    from agents.domain import GenericRequest
    e = pack_engine(pack, tmp_path)
    assert e.mandate.evaluate(GenericRequest(id="T", **req)).floor == floor


def test_pack_personas_speak_for_the_right_senior(tmp_path):
    v, k = pack_engine("leads", tmp_path), pack_engine("spend", tmp_path)
    assert "Vikram Sethi" in v.decider_agent.system and "his delegation-of-authority mandate" in v.decider_agent.system
    assert "Qualify" in v.decider_agent.system and "Meera" not in v.decider_agent.system
    assert "Kavya Iyer" in k.precedent_agent.system and "spend exceptions" in k.precedent_agent.system


def test_pack_override_lessons_use_the_pack_prefix_and_stay_separate(rules_only, tmp_path):
    store = FileStore(tmp_path / "state")
    leads = PratibimbEngine(pack="leads", store=store)
    req = json.loads((PACKS["leads"] / "requests.json").read_text(encoding="utf-8"))["requests"][0]
    lesson = leads.learner_agent.record_override(req["id"], "approve", "ask", "Delivery must confirm Hindi capacity.",
                                                 request=req, sandbox="leads-judge")
    assert lesson["id"] == "SL05"                                    # Vikram's lessons continue SL01–SL04
    assert "SL05" in leads.lessons_for("leads-judge")
    assert "SL05" not in leads.lessons_for("leads-other")
    assert "OVR-001" in {d["id"] for d in leads.memory_for("leads-judge")}


@pytest.mark.parametrize("pack", ["leads", "spend"])
def test_pack_rules_engine_and_api(pack, rules_only):
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    assert pack in {p["id"] for p in c.get("/api/packs").json()["packs"]}
    reqs = c.get(f"/api/requests?pack={pack}").json()["requests"]
    v = c.post(f"/api/decide?pack={pack}", json=reqs[0]).json()
    assert v["verdict"] == "approve" and v["orchestrator"] == "Google ADK Workflow"
    assert len(c.get(f"/api/backtest?pack={pack}").json()["cases"]) == 15
    assert c.get("/api/decide?pack=nope").status_code in (404, 405)
