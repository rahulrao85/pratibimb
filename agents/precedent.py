"""
Precedent Agent for Pratibimb.
1. retrieve(): deterministic candidate search over the senior's decision memory. Holdout decisions are
   NEVER loaded, so the back-test stays blind.
2. reason(): Gemini reads the candidates (with outcomes and mistakes) plus every approved lesson, and
   judges which precedents and lessons genuinely bear on the new request.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from agents import llm
from agents.models import LessonJudgement, PrecedentItem, PrecedentReasoning, VendorRequest

SYSTEM_T = (
    "You are the Precedent agent of Pratibimb, an AI junior that mirrors how {name}, {title_at}, "
    "decides {nouns}. You receive a new request, candidate past decisions from {pos} memory (with what happened "
    "afterwards, including {pos} mistakes) and {pos} approved lessons. "
    "Pick the precedents that genuinely bear on this request and say briefly how {first} decided them and what "
    "followed. Pick every lesson whose trigger or intent applies to this request, including lessons worded "
    "differently from the request (read the request description carefully). Ignore anything irrelevant. Use only "
    "the IDs you are given. Be concise: one sentence per item."
)


class PrecedentAgent:
    def __init__(self, data_dir: Path = None, persona: Dict[str, str] = None, scorer=None, briefer=None):
        from agents.domain import VENDOR_PERSONA

        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = data_dir
        self.system = SYSTEM_T.format(**(persona or VENDOR_PERSONA))
        self._scorer, self._briefer = scorer, briefer
        self.decisions = self._load_decisions()

    def _load_decisions(self) -> List[Dict[str, Any]]:
        path = self.data_dir / "decisions.json"
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # HARD RULE: NEVER retrieve holdout: true decisions during inference!
            return [d for d in data.get("decisions", []) if not d.get("holdout", False)]

    def load_lessons(self, taught: List[Dict[str, Any]] = ()) -> Dict[str, Dict[str, Any]]:
        """Baseline lessons plus those taught in this sandbox (read per request: a lesson recorded a moment ago counts)."""
        path = self.data_dir / "lessons.json"
        base = json.loads(path.read_text(encoding="utf-8")).get("lessons", []) if path.exists() else []
        return {l["id"]: l for l in list(base) + list(taught) if l.get("status", "approved") == "approved"}

    def memory(self, overrides: List[Dict[str, Any]] = ()) -> List[Dict[str, Any]]:
        """Past decisions plus the senior's overrides in this sandbox."""
        return self.decisions + list(overrides)

    def by_id(self, overrides: List[Dict[str, Any]] = ()) -> Dict[str, Dict[str, Any]]:
        return {d["id"]: d for d in self.memory(overrides)}

    def score_relevance(self, req: VendorRequest, dec: Dict[str, Any]) -> float:
        score = 0.0
        if req.vendor_id and req.vendor_id == dec.get("vendor_id"):
            score += 0.40
        if req.type and req.type == dec.get("type"):
            score += 0.20
        req_breaches = req.sla_breaches_12m or 0
        dec_breaches = dec.get("sla_breaches_12m", 0)
        if req_breaches > 0 and dec_breaches > 0:
            score += 0.20
            if req_breaches >= 2 and dec_breaches >= 2:
                score += 0.15
        elif req_breaches == 0 and dec_breaches == 0:
            score += 0.10
        if req.handles_client_data and dec.get("handles_client_data"):
            score += 0.15
        if dec.get("mistake"):
            score += 0.15
        return min(round(score, 2), 0.98)

    def retrieve(self, req: VendorRequest, top_k: int = 3, overrides: List[Dict[str, Any]] = ()) -> Tuple[List[PrecedentItem], List[str]]:
        score = self._scorer or self.score_relevance
        scored = [(score(req, d), d) for d in self.memory(overrides)]
        scored = [s for s in scored if s[0] > 0.30]
        scored.sort(key=lambda x: x[0], reverse=True)

        precedents, cited_lessons = [], []
        for rel, dec in scored[:top_k]:
            takeaway = dec.get("mistake_note") or dec.get("outcome") or dec.get("decision_note")
            precedents.append(PrecedentItem(
                decision_id=dec["id"], similarity=rel, outcome_status=dec.get("outcome_status", "good"),
                takeaway=takeaway[:140] + ("..." if len(takeaway) > 140 else ""),
            ))
            for lid in dec.get("lesson_ids", []):
                if lid not in cited_lessons:
                    cited_lessons.append(lid)
        return precedents, cited_lessons

    @staticmethod
    def _brief(d: Dict[str, Any]) -> str:
        bits = [
            f"{d['id']} ({d.get('date', '?')}) {d.get('type', '?')} · {d.get('vendor_name', '?')} · "
            f"₹{d.get('value_inr', 0):,} · {d.get('term_months', '?')}m · breaches {d.get('sla_breaches_12m', 0)} · "
            f"client data {'yes' if d.get('handles_client_data') else 'no'}",
            f"  Decision: {d.get('decision', '?')} — {d.get('decision_note', '')}",
        ]
        if d.get("conditions"):
            bits.append(f"  Conditions: {'; '.join(d['conditions'])}")
        bits.append(f"  Outcome ({d.get('outcome_status')}): {d.get('outcome')}")
        if d.get("mistake"):
            bits.append(f"  MISTAKE: {d.get('mistake_note')} → lessons {', '.join(d.get('lesson_ids', []))}")
        return "\n".join(bits)

    @staticmethod
    def _request_text(req) -> str:
        name = getattr(req, "vendor_name", None) or getattr(req, "entity_name", None) or ""
        return f"{req.type} · {name} · {req.description or ''}"

    def _hybrid_candidates(self, req, memory: List[Dict[str, Any]], score, brief, top_k: int, extra: int = 2) -> List[Dict[str, Any]]:
        """Smart search, additive only: every field-matched precedent is kept exactly as before, and up to `extra` past
        decisions that describe the same *situation* in other words (Vertex AI gemini-embedding-2) are added.

        (A blended ranking was tried first and rejected: it pushed field matches out and cost 2 back-test cases.)"""
        structured = sorted(((score(req, d), d) for d in memory), key=lambda x: x[0], reverse=True)
        picked = [d for s, d in structured[:top_k] if s > 0.25]
        try:
            q = llm.embed(self._request_text(req), "RETRIEVAL_QUERY")
            sims = sorted(((llm.cosine(q, llm.embed(brief(d), "RETRIEVAL_DOCUMENT")), d) for d in memory),
                          key=lambda x: x[0], reverse=True)
        except Exception:
            return picked
        have = {d["id"] for d in picked}
        for sim, d in sims:
            if len(picked) >= top_k + extra:
                break
            if d["id"] not in have and sim >= sims[0][0] - 0.05:  # only near-best meaning matches
                picked.append(d)
                have.add(d["id"])
        return picked

    def reason(self, case: str, req: VendorRequest, lessons: Dict[str, Dict[str, Any]], top_k: int = 6,
               overrides: List[Dict[str, Any]] = ()) -> Tuple[List[PrecedentItem], List[LessonJudgement]]:
        score, brief = self._scorer or self.score_relevance, self._briefer or self._brief
        candidates = self._hybrid_candidates(req, self.memory(overrides), score, brief, top_k)
        cand_text = "\n".join(brief(d) for d in candidates) or "(no similar past decisions)"
        lesson_text = "\n".join(
            f"{l['id']} — {l['rule']} | trigger: {l.get('trigger', '')} | action: {l.get('action_required', '')}"
            for l in lessons.values()
        )
        prompt = f"{case}\n\nCANDIDATE PAST DECISIONS\n{cand_text}\n\nAPPROVED LESSONS\n{lesson_text}"
        out: PrecedentReasoning = llm.generate_json("precedent", self.system, prompt, PrecedentReasoning)

        known = {d["id"]: d for d in candidates}
        items = []
        for p in sorted(out.relevant_precedents, key=lambda x: x.relevance, reverse=True)[:3]:
            d = known.get(p.decision_id)
            if d:  # drop any ID the model invented
                items.append(PrecedentItem(
                    decision_id=d["id"], similarity=round(max(0.0, min(1.0, p.relevance)), 2),
                    outcome_status=d.get("outcome_status", "good"), takeaway=p.takeaway[:180],
                ))
        applied = [l for l in out.applicable_lessons if l.lesson_id in lessons]
        return items, applied
