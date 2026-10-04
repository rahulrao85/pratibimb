"""
Interviewer Agent for Pratibimb.
Asks the questions the senior would ask before deciding, for information that is missing and material.
Gemini version (default) + the original keyword rules as the deterministic baseline.
"""
from typing import Any, Dict, List

from agents import llm
from agents.models import ChallengeItem, QuestionList, VendorRequest

SYSTEM_T = (
    "You are the Interviewer agent of Pratibimb, an AI junior that mirrors how {name} decides {nouns}. "
    "List only the questions {first} would put to the requester before {subj} could decide, about information that is "
    "missing from the request and would change the decision. Use {pos} voice and prefer {pos} standard questions where "
    "they fit. Do not ask about facts already stated. At most 4 questions; return an empty list when nothing "
    "material is missing ({clean_example})."
)


class InterviewerAgent:
    def __init__(self, persona: Dict[str, str] = None):
        from agents.domain import VENDOR_PERSONA

        self.persona = persona or VENDOR_PERSONA
        self.system = SYSTEM_T.format(**self.persona)

    def formulate_questions_llm(self, case: str, senior: Dict[str, Any], lessons: Dict[str, Dict[str, Any]] = None) -> List[str]:
        style = senior.get("decision_style", {})
        lesson_text = "\n".join(f"- {l['id']}: {l['rule']}" for l in (lessons or {}).values())
        prompt = (
            f"{case}\n\nQUESTIONS {self.persona['first'].upper()} ALWAYS ASKS\n- " + "\n- ".join(style.get("questions_she_always_asks", []))
            + f"\n\n{self.persona['pos'].upper()} LESSONS (ask what a lesson needs confirmed if the request does not already confirm it)\n{lesson_text}"
        )
        out: QuestionList = llm.generate_json("interviewer", self.system, prompt, QuestionList)
        return [q.strip() for q in out.questions if q.strip()][:4]

    def formulate_questions(self, req: VendorRequest, challenges: List[ChallengeItem]) -> List[str]:
        """Deterministic baseline (keyword rules)."""
        questions: List[str] = []
        if req.handles_client_data:
            questions.append("Where specifically will client data reside geographically, and is in-country data residency guaranteed?")
            questions.append("Has an approved sub-processor registry and formal Data Processing Addendum (DPA) been executed?")
            questions.append("Will the vendor commit contractually to notify Meridian within 24 hours of any suspected security incident?")
        if (req.sla_breaches_12m or 0) > 0:
            questions.append("What concrete process or staffing changes has the vendor implemented to resolve past SLA breaches?")
            questions.append("Has a competing benchmark quote been obtained from an alternate supplier within the last 12 months?")
        if req.term_months > 12 or any("auto-renewal" in c.finding.lower() or "evergreen" in c.finding.lower() for c in challenges):
            questions.append("Can this agreement be restructured to a 12-month duration with a unilateral 90-day termination for convenience?")
        if (req.advance_pct or 0) > 30:
            questions.append("Why does this vendor require advance payment exceeding 30%, and can milestone-based billing be substituted?")
        return questions
