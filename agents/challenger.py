"""
Challenger Agent for Pratibimb.
Conducts adversarial scrutiny of contracts, vendor risk flags, commercial traps,
and operational vulnerability patterns.
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from agents.models import VendorRequest, ChallengeItem

class ChallengerAgent:
    def __init__(self, data_dir: Path = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = data_dir
        self.contracts = self._load_contracts()
        self.vendors = self._load_vendors()

    def _load_contracts(self) -> Dict[str, Dict[str, Any]]:
        path = self.data_dir / "contracts.json"
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {c["id"]: c for c in data.get("contracts", [])}

    def _load_vendors(self) -> Dict[str, Dict[str, Any]]:
        path = self.data_dir / "vendors.json"
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {v["id"]: v for v in data.get("vendors", [])}

    def challenge(self, req: VendorRequest) -> Tuple[List[ChallengeItem], List[str]]:
        challenges: List[ChallengeItem] = []
        clause_citations: List[str] = []

        vendor = self.vendors.get(req.vendor_id, {})
        contract_id = req.contract_id or (
            "CN-KESTREL-2025" if req.vendor_id == "V-KESTREL" else
            "CN-BRIGHTLINE-2026" if req.vendor_id == "V-BRIGHTLINE" else
            "CN-PARLO-DRAFT" if req.vendor_id == "V-PARLO" else None
        )
        contract = self.contracts.get(contract_id, {}) if contract_id else {}

        # 1. Check for Auto-Renewal Evergreen clauses
        if contract:
            for clause in contract.get("clauses", []):
                cl_num = clause.get("number")
                cl_text = clause.get("text", "").lower()
                citation = f"{contract_id} §{cl_num}"

                if "automatically renew" in cl_text or "renewal term" in cl_text:
                    if "twenty-four" in cl_text or "24" in cl_text or req.term_months > 12:
                        challenges.append(
                            ChallengeItem(
                                finding=f"Clause {cl_num} locks Meridian into an evergreen 24-month automatic renewal without fee reduction",
                                source=citation,
                                severity="high"
                            )
                        )
                        clause_citations.append(citation)

                # Check for lack of SLA penalties
                if ("no financial deductions" in cl_text or "no penalty" in cl_text) and (req.sla_breaches_12m or 0) > 0:
                    challenges.append(
                        ChallengeItem(
                            finding=f"Clause {cl_num} explicitly exempts vendor from financial penalties or service credits despite SLA breaches",
                            source=citation,
                            severity="high"
                        )
                    )
                    clause_citations.append(citation)

                # Check for lack of termination for convenience
                if "neither party may terminate for convenience" in cl_text:
                    challenges.append(
                        ChallengeItem(
                            finding=f"Clause {cl_num} removes right to terminate for convenience during renewal term",
                            source=citation,
                            severity="high"
                        )
                    )
                    clause_citations.append(citation)

                # Check for loose sub-processor or data provisions
                if "third-party model inference providers" in cl_text and req.handles_client_data:
                    challenges.append(
                        ChallengeItem(
                            finding=f"Clause {cl_num} permits unvetted third-party compute nodes without an approved sub-processor list",
                            source=citation,
                            severity="high"
                        )
                    )
                    clause_citations.append(citation)

                # Check for unacceptable breach notification window (>24 hours)
                if "fourteen (14) business days" in cl_text:
                    challenges.append(
                        ChallengeItem(
                            finding=f"Clause {cl_num} permits a 14-day delay in security compromise notification (violates required 24h standard)",
                            source=citation,
                            severity="high"
                        )
                    )
                    clause_citations.append(citation)

        # 2. Check vendor operational risk flags
        risk_flags = vendor.get("risk_flags", [])
        if "month_end_breaches" in risk_flags and (req.sla_breaches_12m or 0) > 0:
            challenges.append(
                ChallengeItem(
                    finding="Past SLA failures clustered during critical month-end operational close",
                    source=f"Vendor Risk Audit ({req.vendor_id})",
                    severity="high"
                )
            )

        # 3. Check commercial terms: Advance payment on young vendor
        rel_months = vendor.get("relationship_months", 0)
        advance_pct = req.advance_pct or 0
        if advance_pct > 30 and rel_months < 24:
            challenges.append(
                ChallengeItem(
                    finding=f"Requested advance payment of {advance_pct}% exceeds the 30% cap for suppliers with <24 months relationship",
                    source="Commercial Mandate L06",
                    severity="medium"
                )
            )

        # 4. Check price increase > 8%
        if req.price_increase_pct and req.price_increase_pct > 8.0:
            challenges.append(
                ChallengeItem(
                    finding=f"Proposed fee hike of {req.price_increase_pct}% exceeds 8% ceiling without documented market benchmark",
                    source="Commercial Mandate L02",
                    severity="medium"
                )
            )

        return challenges, clause_citations
