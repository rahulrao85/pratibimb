"""
Learner Agent for Pratibimb.
Turns a senior override into a versioned lesson. Gemini rewrites Meera's note into a reusable rule with a
trigger. The lesson, and her overridden decision as a new precedent, are saved to the Store for this sandbox (Firestore on
Cloud Run), so the very next similar case is decided differently, and that survives restarts and redeploys.
The baseline lessons in data/lessons.json are never modified.
"""
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents import llm
from agents.models import LessonDraft

SYSTEM_T = (
    "You are the Learner agent of Pratibimb. {name} has just overridden the AI junior's verdict on a request. "
    "Turn {pos} note into a lesson the junior can apply to future {nouns}: a short title, a one-sentence rule, "
    "a trigger that says when it applies, and the action required. The trigger MUST cover the request {subj} just "
    "overrode (that same request, unchanged, must trigger it) and similar future requests; it must not depend on "
    "facts the requester would not normally state. Keep {pos} intent; do not add new requirements."
)


class LearnerAgent:
    def __init__(self, data_dir: Path = None, store=None, domain=None):
        from agents.domain import VENDOR_PERSONA

        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = data_dir
        self.store = store
        self.domain = domain
        self.persona = domain.persona if domain else VENDOR_PERSONA
        self.system = SYSTEM_T.format(**self.persona)

    def baseline_lessons(self) -> List[Dict[str, Any]]:
        return json.loads((self.data_dir / "lessons.json").read_text(encoding="utf-8")).get("lessons", [])

    def record_override(self, request_id: str, engine_verdict: str, senior_decision: str,
                        senior_override_note: str, proposed_rule: str = "", senior_name: str = "Meera Nair",
                        request_summary: str = "", request: Optional[Dict[str, Any]] = None,
                        sandbox: str = "local") -> Dict[str, Any]:
        lessons = self.baseline_lessons() + self.store.lessons(sandbox)
        parsed = [re.match(r"^([A-Z]+)(\d+)$", l["id"]) for l in lessons]
        parsed = [m for m in parsed if m]
        prefix = parsed[0].group(1) if parsed else "L"  # L01… for Meera, SL01… for Vikram, FL01… for Kavya
        nums = [int(m.group(2)) for m in parsed if m.group(1) == prefix]
        new_id = f"{prefix}{(max(nums) + 1) if nums else 1:02d}"

        if request and not request_summary:
            if self.domain:
                request_summary = self.domain.summary(request)
            else:
                request_summary = (
                    f"{request.get('type')} · {request.get('vendor_name')} · ₹{int(request.get('value_inr') or 0):,} · "
                    f"{request.get('term_months')} months · breaches {request.get('sla_breaches_12m')} · "
                    f"client data {request.get('handles_client_data')} · {request.get('description') or ''}"
                )
        if llm.enabled():
            prompt = (
                f"REQUEST: {request_id} {request_summary}\nJUNIOR'S VERDICT: {engine_verdict}\n"
                f"{self.persona['first'].upper()}'S DECISION: {senior_decision}\n"
                f"{self.persona['first'].upper()}'S NOTE: {senior_override_note}\n"
                f"RULE {self.persona['subj'].upper()} PROPOSED (may be empty): {proposed_rule}"
            )
            try:
                d: LessonDraft = llm.generate_json("learner", self.system, prompt, LessonDraft)
                title, rule, trigger, action = d.title, d.rule, d.trigger, d.action_required
            except llm.CapReached:
                title = None
        if not llm.enabled() or title is None:  # keep Meera's own words as the lesson
            title = f"Rule from override ({request_id})"
            rule, trigger, action = proposed_rule or senior_override_note, f"Similar to request {request_id}", senior_override_note

        lesson = {
            "id": new_id, "version": 1, "status": "approved", "title": title, "rule": rule, "trigger": trigger,
            "action_required": action, "source_decision_ids": [request_id],
            "override": {"engine_verdict": engine_verdict, "senior_decision": senior_decision, "note": senior_override_note},
            "created": dt.date.today().isoformat(), "approved_by": senior_name, "half_life_days": 540,
        }
        self.store.add_lesson(sandbox, lesson)
        if request:
            self._record_precedent(sandbox, request, engine_verdict, senior_decision, senior_override_note, new_id)
        return lesson

    def _record_precedent(self, sandbox: str, req: Dict[str, Any], engine_verdict: str, senior_decision: str, note: str,
                          lesson_id: str) -> None:
        """Meera's override becomes part of her decision memory, like any other past decision."""
        rec = {
            "id": f"OVR-{len(self.store.overrides(sandbox)) + 1:03d}", "date": dt.date.today().isoformat(),
            **(self.domain.precedent_record(req) if self.domain else {
                "type": req.get("type"), "vendor_id": req.get("vendor_id"), "vendor_name": req.get("vendor_name"),
                "value_inr": int(req.get("value_inr") or 0), "term_months": int(req.get("term_months") or 12),
                "sla_breaches_12m": int(req.get("sla_breaches_12m") or 0), "handles_client_data": bool(req.get("handles_client_data"))}),
            "decision": senior_decision, "decision_note": f"{self.persona['first']} overrode Pratibimb's '{engine_verdict}': {note}",
            "reasons": [note], "conditions": [], "outcome": "Senior override recorded; lesson created.",
            "outcome_status": "pending", "mistake": False, "mistake_note": "", "lesson_ids": [lesson_id],
            "source_request_id": req.get("id"), "holdout": False,
        }
        self.store.add_override(sandbox, rec)

    def reset(self, sandbox: str = "local") -> int:
        """Forget what was taught in this sandbox; the baseline lessons remain. Returns the lesson count."""
        self.store.reset(sandbox)
        return len(self.baseline_lessons())
