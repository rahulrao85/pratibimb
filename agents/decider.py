"""
Decider Agent for Pratibimb.
Evaluates delegation of authority rules from mandate.json, integrates findings from
Precedent, Challenger, and Interviewer agents, and synthesizes an audit-ready verdict.
"""
from typing import List, Dict, Any, Tuple
from agents.models import (
    VendorRequest,
    VerdictResponse,
    MandateCheck,
    PrecedentItem,
    ChallengeItem,
)

class DeciderAgent:
    SIGNATURE_LIMIT_INR = 500000

    def evaluate(
        self,
        req: VendorRequest,
        precedents: List[PrecedentItem],
        challenges: List[ChallengeItem],
        questions: List[str],
        cited_lessons: List[str],
        clause_citations: List[str],
    ) -> VerdictResponse:
        citations: List[str] = []
        mandate_breaches: List[str] = []
        recommended_conditions: List[str] = []

        # Default confidence
        confidence = "high"

        # 1. OUT OF SCOPE CHECK (M-R13)
        if req.type == "out_of_scope" or "appraisal" in (req.description or "").lower():
            citations.append("M-R13")
            return VerdictResponse(
                request_id=req.id,
                verdict="refuse",
                headline="Refuse request: employee performance appraisal scoring is strictly out of scope",
                confidence="high",
                mandate_check=MandateCheck(within_limits=False, breaches=["Out of scope under rule M-R13 (EU AI Act high-risk safeguard)"]),
                precedents=[],
                challenges=[],
                questions_for_requester=[],
                recommended_conditions=[],
                citations=citations
            )

        # 2. VENDOR ONBOARDING WITH CLIENT DATA (M-R6 & L03)
        if req.type == "vendor_onboarding" and req.handles_client_data:
            citations.append("M-R6")
            if "L03" not in citations:
                citations.append("L03")
            mandate_breaches.append("New vendor handling confidential client data without established precedent")
            if req.value_inr > self.SIGNATURE_LIMIT_INR:
                mandate_breaches.append(f"Spend ₹{req.value_inr:,} exceeds signature limit of ₹5,00,000")
            
            # If questions are pending, verdict is 'ask' (holding until answers provided) or 'escalate'
            verdict = "ask" if questions else "escalate"
            headline = f"Hold onboarding: interrogate data residency, sub-processor registry and DPA terms before escalation"

            recommended_conditions.extend([
                "Mandatory signed Data Processing Addendum (DPA)",
                "Explicit contractual guarantee of in-country data residency",
                "Approved third-party sub-processor registry",
                "24-hour security incident notification obligation"
            ])

            for p in precedents:
                citations.append(p.decision_id)
            for c in clause_citations:
                if c not in citations:
                    citations.append(c)

            return VerdictResponse(
                request_id=req.id,
                verdict=verdict,
                headline=headline,
                confidence="high",
                mandate_check=MandateCheck(within_limits=False, breaches=mandate_breaches),
                precedents=precedents,
                challenges=challenges,
                questions_for_requester=questions,
                recommended_conditions=recommended_conditions,
                citations=list(dict.fromkeys(citations))
            )

        # 3. GENERAL VENDOR ONBOARDING (M-R5)
        if req.type == "vendor_onboarding":
            citations.append("M-R5")
            mandate_breaches.append("New vendor onboarding requires senior review")
            return VerdictResponse(
                request_id=req.id,
                verdict="escalate",
                headline=f"Escalate onboarding of new vendor {req.vendor_name or req.vendor_id} to Meera Nair",
                confidence="high",
                mandate_check=MandateCheck(within_limits=False, breaches=mandate_breaches),
                precedents=precedents,
                challenges=challenges,
                questions_for_requester=questions,
                recommended_conditions=[],
                citations=citations
            )

        # 4. ONE-TIME SPEND CHECKS (M-R11 & M-R12)
        if req.type == "one_time_spend":
            if req.value_inr <= 50000:
                citations.append("M-R11")
                if precedents:
                    citations.append(precedents[0].decision_id)
                return VerdictResponse(
                    request_id=req.id,
                    verdict="approve",
                    headline=f"Approve one-time spend of ₹{req.value_inr:,} (within ₹50k threshold with precedent)",
                    confidence="high",
                    mandate_check=MandateCheck(within_limits=True, breaches=[]),
                    precedents=precedents,
                    challenges=challenges,
                    questions_for_requester=[],
                    recommended_conditions=[],
                    citations=citations
                )
            else:
                citations.append("M-R12")
                mandate_breaches.append(f"One-time spend ₹{req.value_inr:,} exceeds ₹50,000 threshold")
                return VerdictResponse(
                    request_id=req.id,
                    verdict="escalate",
                    headline=f"Escalate one-time spend of ₹{req.value_inr:,} exceeding ₹50k threshold",
                    confidence="high",
                    mandate_check=MandateCheck(within_limits=False, breaches=mandate_breaches),
                    precedents=precedents,
                    challenges=challenges,
                    questions_for_requester=questions,
                    recommended_conditions=["Itemized all-inclusive bill of materials", "No open-ended consumables (L04)"],
                    citations=citations
                )

        # 5. VENDOR RENEWALS
        # Check rule triggers
        is_above_limit = req.value_inr > self.SIGNATURE_LIMIT_INR
        breaches_count = req.sla_breaches_12m or 0
        has_2_plus_breaches = breaches_count >= 2
        has_1_breach = breaches_count == 1
        has_auto_renewal = any("evergreen" in c.finding.lower() or "auto-renewal" in c.finding.lower() for c in challenges) or req.term_months > 12

        if is_above_limit:
            mandate_breaches.append(f"Spend ₹{req.value_inr:,} exceeds signature authority threshold of ₹5,00,000 (M-R4)")
            citations.append("M-R4")

        if has_2_plus_breaches:
            mandate_breaches.append(f"Vendor has {breaches_count} SLA breaches in prior 12m (M-R3 / Brightline Lesson L01)")
            citations.append("M-R3")
            if "L01" not in citations:
                citations.append("L01")

        if has_auto_renewal:
            mandate_breaches.append("Agreement contains auto-renewal or term exceeding 12 months (M-R7 / M-R8)")
            citations.append("M-R7")

        # Decision synthesis
        if is_above_limit or has_2_plus_breaches or has_auto_renewal:
            verdict = "escalate"
            
            # Formulate headline
            if has_2_plus_breaches and has_auto_renewal:
                headline = f"Escalate {req.vendor_name or req.vendor_id} renewal: restrict to 12 months, mandate service credits and 90-day exit"
            elif has_2_plus_breaches:
                headline = f"Escalate {req.vendor_name or req.vendor_id} renewal to Meera due to {breaches_count} SLA breaches (Lesson L01)"
            elif is_above_limit:
                headline = f"Escalate {req.vendor_name or req.vendor_id} renewal: spend ₹{req.value_inr:,} exceeds ₹5L signature limit"
            else:
                headline = f"Escalate {req.vendor_name or req.vendor_id} renewal for senior contract review"

            if has_2_plus_breaches or has_auto_renewal or is_above_limit:
                recommended_conditions.extend([
                    "Cap contract duration strictly to 12 months",
                    "Mandatory 5% service credit per SLA breach",
                    "Unilateral 90-day termination for convenience without penalty",
                    "Obtain at least one competing benchmark quote"
                ])

        elif has_1_breach:
            citations.append("M-R2")
            if "L01" not in citations:
                citations.append("L01")
            verdict = "approve_with_conditions"
            headline = f"Approve {req.vendor_name or req.vendor_id} renewal conditionally with service credit and 90-day exit clauses"
            recommended_conditions.extend([
                "5% service credit penalty for any subsequent SLA failure",
                "90-day termination for convenience clause"
            ])

        else:
            # Clean renewal inside limit
            citations.append("M-R1")
            verdict = "approve"
            headline = f"Approve {req.vendor_name or req.vendor_id} renewal for ₹{req.value_inr:,} (12 months, clean record)"

        # Merge citations
        for p in precedents:
            citations.append(p.decision_id)
        for c in clause_citations:
            if c not in citations:
                citations.append(c)
        for lid in cited_lessons:
            if lid not in citations:
                citations.append(lid)

        # Ensure all citations are unique while preserving order
        deduped_citations = list(dict.fromkeys(citations))

        within_limits = len(mandate_breaches) == 0

        return VerdictResponse(
            request_id=req.id,
            verdict=verdict,
            headline=headline,
            confidence=confidence,
            mandate_check=MandateCheck(within_limits=within_limits, breaches=mandate_breaches),
            precedents=precedents,
            challenges=challenges,
            questions_for_requester=questions,
            recommended_conditions=recommended_conditions,
            citations=deduped_citations
        )
