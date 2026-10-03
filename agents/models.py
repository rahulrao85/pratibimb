"""
Pydantic schemas for Pratibimb agentic verdict engine.
Conforms strictly to data-model.md frozen verdict contract.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

VerdictType = Literal["approve", "approve_with_conditions", "escalate", "ask", "refuse"]
ConfidenceType = Literal["high", "medium", "low"]
OutcomeStatusType = Literal["good", "mixed", "bad", "pending"]

class MandateCheck(BaseModel):
    within_limits: bool = Field(..., description="Whether request falls entirely within senior signature limits")
    breaches: List[str] = Field(default_factory=list, description="List of specific mandate conditions triggered or breached")

class PrecedentItem(BaseModel):
    decision_id: str = Field(..., description="Citable ID of past decision (e.g. DEC-0087)")
    similarity: float = Field(..., description="Relevance score (0.0 to 1.0)")
    outcome_status: OutcomeStatusType = Field(..., description="Outcome of the past decision")
    takeaway: str = Field(..., description="Core lesson or operational takeaway from the precedent")

class ChallengeItem(BaseModel):
    finding: str = Field(..., description="Risk or adversarial finding identified")
    source: str = Field(..., description="Source citation (e.g. CN-KESTREL-2025 §9.2 or Vendor History)")
    severity: Literal["high", "medium", "low"] = Field(..., description="Risk severity")

class VerdictResponse(BaseModel):
    request_id: str = Field(..., description="Incoming request ID")
    verdict: VerdictType = Field(..., description="Formal recommendation: approve, approve_with_conditions, escalate, ask, refuse")
    headline: str = Field(..., description="Executive summary of the verdict")
    confidence: ConfidenceType = Field(..., description="Confidence level: high, medium, low")
    mandate_check: MandateCheck = Field(..., description="Evaluation against delegation of authority rules")
    precedents: List[PrecedentItem] = Field(default_factory=list, description="Top matching past decisions")
    challenges: List[ChallengeItem] = Field(default_factory=list, description="Contractual and operational risks identified")
    questions_for_requester: List[str] = Field(default_factory=list, description="Interviewer questions for missing information")
    recommended_conditions: List[str] = Field(default_factory=list, description="Required clauses or stipulations attached to decision")
    citations: List[str] = Field(default_factory=list, description="Mandatory list of all cited decisions, rules, clauses, and lessons")

class VendorRequest(BaseModel):
    id: str
    date: Optional[str] = None
    type: str = Field(..., description="vendor_renewal | vendor_onboarding | one_time_spend | contract_amendment | out_of_scope")
    vendor_id: str
    vendor_name: Optional[str] = None
    value_inr: int = Field(0, description="Annual or total spend amount in INR")
    term_months: int = Field(12, description="Proposed contract term in months")
    sla_breaches_12m: int = Field(0, description="Number of SLA breaches recorded in prior 12 months")
    handles_client_data: bool = Field(False, description="Whether vendor processes or stores client confidential data")
    advance_pct: int = Field(0, description="Percentage of advance payment requested")
    price_increase_pct: float = Field(0.0, description="Proposed fee increase percentage")
    contract_id: Optional[str] = None
    requested_by: Optional[str] = None
    description: Optional[str] = None
