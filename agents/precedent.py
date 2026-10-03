"""
Precedent Agent for Pratibimb.
Searches episodic decision memory (excluding holdouts), identifies matching historical
outcomes, surfaces mistakes and lessons, and returns grounded precedent items.
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from agents.models import VendorRequest, PrecedentItem

class PrecedentAgent:
    def __init__(self, data_dir: Path = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = data_dir
        self.decisions = self._load_decisions()
        self.lessons = self._load_lessons()

    def _load_decisions(self) -> List[Dict[str, Any]]:
        path = self.data_dir / "decisions.json"
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # HARD RULE: NEVER retrieve holdout: true decisions during inference!
            return [d for d in data.get("decisions", []) if not d.get("holdout", False)]

    def _load_lessons(self) -> Dict[str, Dict[str, Any]]:
        path = self.data_dir / "lessons.json"
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {l["id"]: l for l in data.get("lessons", [])}

    def score_relevance(self, req: VendorRequest, dec: Dict[str, Any]) -> float:
        score = 0.0

        # Exact vendor match
        if req.vendor_id and req.vendor_id == dec.get("vendor_id"):
            score += 0.40

        # Same decision type
        if req.type and req.type == dec.get("type"):
            score += 0.20

        # Similar SLA breach status
        req_breaches = req.sla_breaches_12m or 0
        dec_breaches = dec.get("sla_breaches_12m", 0)
        if req_breaches > 0 and dec_breaches > 0:
            score += 0.20
            # Higher weight if both have 2+ breaches (the Brightline risk pattern)
            if req_breaches >= 2 and dec_breaches >= 2:
                score += 0.15
        elif req_breaches == 0 and dec_breaches == 0:
            score += 0.10

        # Both involve client data
        if req.handles_client_data and dec.get("handles_client_data"):
            score += 0.15

        # Prior mistake or lesson attached: boost so cautionary tales always surface
        if dec.get("mistake"):
            score += 0.15

        return min(round(score, 2), 0.98)

    def retrieve(self, req: VendorRequest, top_k: int = 3) -> Tuple[List[PrecedentItem], List[str]]:
        scored = []
        for dec in self.decisions:
            relevance = self.score_relevance(req, dec)
            if relevance > 0.30:
                scored.append((relevance, dec))

        # Sort by relevance descending
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]

        precedents = []
        cited_lessons = []

        for rel, dec in top:
            takeaway = dec.get("mistake_note") or dec.get("outcome") or dec.get("decision_note")
            precedents.append(
                PrecedentItem(
                    decision_id=dec["id"],
                    similarity=rel,
                    outcome_status=dec.get("outcome_status", "good"),
                    takeaway=takeaway[:140] + ("..." if len(takeaway) > 140 else "")
                )
            )
            for lid in dec.get("lesson_ids", []):
                if lid not in cited_lessons:
                    cited_lessons.append(lid)

        return precedents, cited_lessons
