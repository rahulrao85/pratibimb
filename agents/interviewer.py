"""
Interviewer Agent for Pratibimb.
Formulates targeted questions for requesters, embodying Meera Nair's instinctual
operational inquiry habits when information is missing or risk is elevated.
"""
from typing import List
from agents.models import VendorRequest, ChallengeItem

class InterviewerAgent:
    def formulate_questions(self, req: VendorRequest, challenges: List[ChallengeItem]) -> List[str]:
        questions: List[str] = []

        # Client data handling inquiry (Lesson L03)
        if req.handles_client_data:
            questions.append("Where specifically will client data reside geographically, and is in-country data residency guaranteed?")
            questions.append("Has an approved sub-processor registry and formal Data Processing Addendum (DPA) been executed?")
            questions.append("Will the vendor commit contractually to notify Meridian within 24 hours of any suspected security incident?")

        # SLA breach inquiry (Brightline lesson L01)
        if (req.sla_breaches_12m or 0) > 0:
            questions.append("What concrete process or staffing changes has the vendor implemented to resolve past SLA breaches?")
            questions.append("Has a competing benchmark quote been obtained from an alternate supplier within the last 12 months?")

        # Long term or auto-renewal inquiry
        if req.term_months > 12 or any("auto-renewal" in c.finding.lower() or "evergreen" in c.finding.lower() for c in challenges):
            questions.append("Can this agreement be restructured to a 12-month duration with a unilateral 90-day termination for convenience?")

        # High advance payment inquiry (Lesson L06)
        if (req.advance_pct or 0) > 30:
            questions.append("Why does this vendor require advance payment exceeding 30%, and can milestone-based billing be substituted?")

        return questions
