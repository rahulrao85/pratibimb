"""
Decider Agent for Pratibimb.

The mandate (agents/mandate.py, read from mandate.json) sets a floor: the least restrictive verdict the
senior's delegation of authority allows. Gemini then decides what Meera would decide, but may only be
stricter than the floor, never looser. Every citation is checked against the data before it is returned.

decide_rules() is the deterministic baseline used when PRATIBIMB_LLM=off (and for the back-test ablation).
"""
import re
from typing import Dict, List, Set

from agents import llm
from agents.mandate import STRICTNESS, MandateResult
from agents.models import (ChallengeItem, DeciderOutput, LessonJudgement, MandateCheck, PrecedentItem,
                           VendorRequest, VerdictResponse)

CONDITION_TEXT = {
    "service_credit_clause": "Service credit of 5% per SLA breach",
    "90_day_exit": "90-day termination for convenience",
    "competing_quote": "At least one competing quote before signing",
    "benchmark_review": "Market benchmark review of the proposed price",
    "data_location": "Verified in-country data location",
    "approved_subprocessors": "Approved sub-processor list in the contract",
    "dpa_signed": "Signed Data Processing Addendum (DPA)",
    "breach_notification_24h": "24-hour security incident notification",
    "right_to_audit": "Right to audit the vendor",
}

SYSTEM_T = (
    "You are the Decider agent of Pratibimb, an AI junior that gives the verdict {name} ({title}) would give on a "
    "{noun}. {first} always makes the final call; you recommend.\n"
    "Rules:\n"
    "1. The verdict MUST be one of the ALLOWED VERDICTS. They come from {pos} delegation-of-authority mandate; you may "
    "be stricter than the mandate, never looser.\n"
    "2. Apply every applicable lesson and learn from how similar past decisions turned out.\n"
    "3. Verdict meanings: 'approve' only for a clean, routine case; 'approve_with_conditions' when it can go ahead "
    "only with protective clauses; 'ask' when material facts are missing and the requester can supply them; "
    "'escalate' when it needs {first}'s own authority; 'refuse' when it is out of scope.{label_note}\n"
    "4. Cite evidence using only the IDs listed under VALID CITATION IDS.\n"
    "5. headline: at most 20 words, starting with the verb. reasoning: 2-3 plain sentences, the way {first} would "
    "explain it to the requester. Conditions: concrete clauses, at most 5."
)


def allowed_verdicts(floor: str) -> List[str]:
    if floor == "refuse":
        return ["refuse"]
    if floor in ("ask", "escalate"):
        return ["ask", "escalate", "refuse"]
    return STRICTNESS[STRICTNESS.index(floor):]


CONDITION_KEYWORDS = {
    "service_credit_clause": ["service credit", "penalt"],
    "90_day_exit": ["90-day", "90 day", "termination for convenience", "exit"],
    "competing_quote": ["competing", "quote"],
    "benchmark_review": ["benchmark"],
    "data_location": ["residency", "data location", "in-country"],
    "approved_subprocessors": ["sub-processor", "subprocessor"],
    "dpa_signed": ["dpa", "data processing addendum"],
    "breach_notification_24h": ["24-hour", "24 hour", "24h"],
    "right_to_audit": ["audit"],
}


def _mandate_conditions(m: MandateResult) -> List[str]:
    return [CONDITION_TEXT.get(c, c) for c in m.required_conditions + m.required_checklist]


def _keywords(code: str) -> List[str]:
    if code in CONDITION_KEYWORDS:
        return CONDITION_KEYWORDS[code]
    return [w for w in re.findall(r"[a-z0-9-]{5,}", code.lower())][:4] or [code.lower()]


def _merge(llm_conditions: List[str], m: MandateResult) -> List[str]:
    """Keep Gemini's wording; add any mandate-required condition it left out."""
    out = list(llm_conditions)
    text = " ".join(out).lower()
    for code in m.required_conditions + m.required_checklist:
        kws = _keywords(code)
        hits = sum(k in text for k in kws)
        if not (hits >= 1 if code in CONDITION_KEYWORDS else hits >= min(2, len(kws))):
            out.append(CONDITION_TEXT.get(code, code))
    return out


class DeciderAgent:
    def __init__(self, persona: Dict[str, str] = None, headline=None):
        from agents.domain import VENDOR_PERSONA

        self.persona = persona or VENDOR_PERSONA
        self.system = SYSTEM_T.format(**self.persona)
        self._headline = headline

    def decide_rules(self, req: VendorRequest, m: MandateResult, precedents: List[PrecedentItem],
                     challenges: List[ChallengeItem], questions: List[str], cited_lessons: List[str],
                     clause_citations: List[str]) -> VerdictResponse:
        verdict = m.floor
        if self._headline:
            headline = self._headline(req, verdict)
        else:
            name = req.vendor_name or req.vendor_id
            headline = {
                "approve": f"Approve {name} for ₹{req.value_inr:,}: inside the mandate, clean record",
                "approve_with_conditions": f"Approve {name} only with protective conditions",
                "escalate": f"Escalate {name} to Meera: outside the mandate",
                "ask": f"Hold {name}: information missing",
                "refuse": "Refuse: out of scope",
            }[verdict]
        citations = m.rule_ids + [p.decision_id for p in precedents] + clause_citations + cited_lessons
        return VerdictResponse(
            request_id=req.id, verdict=verdict, headline=headline, confidence="high",
            mandate_check=MandateCheck(within_limits=m.within_limits, breaches=m.breaches),
            precedents=precedents, challenges=challenges,
            questions_for_requester=questions if verdict not in ("approve", "refuse") else [],
            recommended_conditions=_mandate_conditions(m) if verdict != "refuse" else [],
            citations=list(dict.fromkeys(citations)) or ["M-R5"], reasoning="Decided by mandate rules alone.",
            lessons_applied=cited_lessons, engine="rules", mandate_floor=m.floor,
        )

    def decide_llm(self, case: str, req: VendorRequest, m: MandateResult, precedents: List[PrecedentItem],
                   lessons_applied: List[LessonJudgement], lessons: Dict[str, Dict], challenges: List[ChallengeItem],
                   questions: List[str], clause_citations: List[str], valid_ids: Set[str]) -> VerdictResponse:
        allowed = allowed_verdicts(m.floor)
        rules_txt = "\n".join(f"{r['id']} → {r['then']}: {r['reason']}" for r in m.triggered) or "No rule allows this request."
        prec_txt = "\n".join(f"{p.decision_id} (outcome {p.outcome_status}): {p.takeaway}" for p in precedents) or "None relevant."
        les_txt = "\n".join(
            f"{l.lesson_id}: {lessons[l.lesson_id]['rule']} — action: {lessons[l.lesson_id].get('action_required', '')} (why here: {l.why})"
            for l in lessons_applied
        ) or "None applies."
        ch_txt = "\n".join(f"[{c.severity}] {c.finding} ({c.source})" for c in challenges) or "No material risks found."
        q_txt = "\n".join(f"- {q}" for q in questions) or "None."
        prompt = (
            f"{case}\n\nMANDATE CHECK (floor: {m.floor})\n{rules_txt}\n"
            f"Required conditions from the mandate: {', '.join(_mandate_conditions(m)) or 'none'}\n\n"
            f"ALLOWED VERDICTS: {', '.join(allowed)}\n\n"
            f"RELEVANT PRECEDENTS\n{prec_txt}\n\nAPPLICABLE LESSONS\n{les_txt}\n\n"
            f"CHALLENGER FINDINGS\n{ch_txt}\n\nOPEN QUESTIONS FOR THE REQUESTER\n{q_txt}\n\n"
            f"VALID CITATION IDS\n{', '.join(sorted(valid_ids))}"
        )
        out: DeciderOutput = llm.generate_json("decider", self.system, prompt, DeciderOutput)

        verdict = out.verdict if out.verdict in allowed else ("escalate" if m.floor == "ask" else m.floor)
        lesson_ids = [l.lesson_id for l in lessons_applied]
        dropped = [c for c in out.citations if c not in valid_ids]
        citations = [c for c in m.rule_ids + out.citations + clause_citations + lesson_ids if c in valid_ids]
        citations = list(dict.fromkeys(citations)) or (m.rule_ids or ["M-R5"])
        conditions = [] if verdict in ("approve", "refuse") else _merge(out.recommended_conditions[:5], m)
        if verdict == "ask" and not questions:
            questions = [q for q in out.questions_if_asking if q.strip()][:4]
        return VerdictResponse(
            request_id=req.id, verdict=verdict, headline=out.headline, confidence=out.confidence,
            mandate_check=MandateCheck(within_limits=m.within_limits, breaches=m.breaches),
            precedents=precedents, challenges=challenges,
            questions_for_requester=questions if verdict in ("ask", "escalate", "approve_with_conditions") else [],
            recommended_conditions=conditions, citations=citations, reasoning=out.reasoning,
            lessons_applied=lesson_ids, engine=llm.MODEL,
            mandate_floor=m.floor, llm_verdict=out.verdict, dropped_citations=list(dict.fromkeys(dropped)),
        )
