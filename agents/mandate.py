"""
Mandate guardrails for Pratibimb, read from data/mandate.json.

Deterministic on purpose: the senior's delegation of authority is a hard boundary that the LLM
may tighten (ask / escalate) but never loosen. Editing mandate.json changes behaviour.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.models import VendorRequest

# How restrictive each verdict is; a verdict can only move rightwards from the rule floor.
STRICTNESS = ["approve", "approve_with_conditions", "ask", "escalate", "refuse"]


@dataclass
class MandateResult:
    triggered: List[Dict[str, Any]] = field(default_factory=list)  # rules that fired
    floor: str = "approve"           # least restrictive verdict the mandate allows
    breaches: List[str] = field(default_factory=list)
    required_conditions: List[str] = field(default_factory=list)
    required_checklist: List[str] = field(default_factory=list)

    @property
    def rule_ids(self) -> List[str]:
        return [r["id"] for r in self.triggered]

    @property
    def within_limits(self) -> bool:
        return STRICTNESS.index(self.floor) <= STRICTNESS.index("approve_with_conditions")


def stricter(a: str, b: str) -> str:
    return a if STRICTNESS.index(a) >= STRICTNESS.index(b) else b


class Mandate:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.reload()

    def reload(self) -> None:
        with open(self.data_dir / "mandate.json", encoding="utf-8") as f:
            self.doc = json.load(f)
        self.rules = self.doc["rules"]
        vendors = json.load(open(self.data_dir / "vendors.json", encoding="utf-8")).get("vendors", [])
        self.vendors = {v["id"]: v for v in vendors}

    def signature_limit(self) -> int:
        for r in self.rules:
            if r["id"] == "M-R4":
                return int(r["when"].get("min_value_inr", 500000))
        return 500000

    def _relationship_months(self, req: VendorRequest) -> Optional[int]:
        v = self.vendors.get(req.vendor_id)
        return v.get("relationship_months") if v else None

    def _matches(self, rule: Dict[str, Any], req: VendorRequest, has_precedent: bool, auto_renewal: bool) -> bool:
        w = rule.get("when", {})
        applies = rule.get("applies_to")
        rel = self._relationship_months(req)
        breaches = req.sla_breaches_12m or 0

        if applies in ("vendor_renewal", "vendor_onboarding", "one_time_spend", "out_of_scope"):
            if req.type != applies:
                return False
        if applies == "out_of_scope":
            return True
        if applies == "contract_term":
            if w.get("auto_renewal"):
                return auto_renewal
            if "min_term_months_exceeding" in w:
                return req.term_months > w["min_term_months_exceeding"]
        if applies == "price_increase":
            return (req.price_increase_pct or 0) > w.get("min_increase_pct", 8)
        if applies == "advance_payment":
            young = rel is None or rel < w.get("max_relationship_months", 24)
            return (req.advance_pct or 0) > w.get("min_advance_pct", 30) and young

        if "max_value_inr" in w and req.value_inr > w["max_value_inr"]:
            return False
        if "min_value_inr" in w and req.value_inr <= w["min_value_inr"]:
            return False
        if "max_sla_breaches_12m" in w and breaches > w["max_sla_breaches_12m"]:
            return False
        if "sla_breaches_12m" in w and breaches != w["sla_breaches_12m"]:
            return False
        if "min_sla_breaches_12m" in w and breaches < w["min_sla_breaches_12m"]:
            return False
        if "min_relationship_months" in w and (rel is None or rel < w["min_relationship_months"]):  # no history = not proven
            return False
        if "handles_client_data" in w and bool(req.handles_client_data) != bool(w["handles_client_data"]):
            return False
        if w.get("has_precedent") and not has_precedent:
            return False
        if w.get("no_precedent") and has_precedent:
            return False
        return True

    def evaluate(self, req: VendorRequest, has_precedent: bool = True, auto_renewal: bool = False) -> MandateResult:
        res = MandateResult(floor="escalate")  # nothing explicitly allows it -> escalate
        approvals, restrictions = [], []
        for rule in self.rules:
            if self._matches(rule, req, has_precedent, auto_renewal):
                (approvals if rule["then"] in ("approve", "approve_with_conditions") else restrictions).append(rule)

        # An approve rule lowers the floor from the default "escalate"; any escalate/refuse rule
        # overrides it again ("Any escalate/refuse rule overrides an earlier approve").
        if approvals:
            res.floor = max((r["then"] for r in approvals), key=STRICTNESS.index)
        for r in restrictions:
            res.floor = stricter(res.floor, r["then"])
        if not approvals and not restrictions:
            res.breaches.append("No mandate rule allows this request; default is to escalate to the senior.")

        res.triggered = approvals + restrictions
        for r in restrictions:
            res.breaches.append(f"{r['id']}: {r['reason']}")
        for r in res.triggered:
            res.required_conditions += [c for c in r.get("requires_conditions", []) if c not in res.required_conditions]
            res.required_checklist += [c for c in r.get("requires_checklist", []) if c not in res.required_checklist]
        return res
