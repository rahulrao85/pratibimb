"""
Decision packs: one engine, many seniors.

A pack is one senior and one kind of decision: their profile, delegation-of-authority mandate, past decisions with
outcomes, lessons, documents and demo requests. The ADK workflow, the guardrails (mandate floor, citation checks), the
Firestore memory and the learning loop are shared; a Domain supplies the parts that differ:

  persona       how the agents' instructions refer to the senior (name, title, pronouns, what they decide)
  request_model the request fields for this decision type
  mandate       evaluate(req) -> MandateResult (the floor Gemini may tighten but never loosen)
  challenger    the documents the Challenger reads (contracts, RFPs, invoices, policies)
  case_text     how a request is described to the agents
  score/brief   how past decisions are matched and summarised

  vendor  Meera Nair, Head of Delivery Operations — vendor approvals (data/)
  leads   Vikram Sethi, Head of Sales — lead qualification (data/packs/leads)
  spend   Kavya Iyer, Financial Controller — spend & payment exceptions (data/packs/spend)
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict

from agents import llm
from agents.mandate import STRICTNESS, MandateResult, stricter
from agents.models import ChallengeItem, ChallengeList, VendorRequest

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PACK_IDS = ["vendor", "leads", "spend"]

VENDOR_PERSONA = {
    "name": "Meera Nair", "first": "Meera", "pos": "her", "subj": "she",
    "title": "Head of Delivery Operations", "title_at": "Head of Delivery Operations at a Mumbai delivery centre",
    "noun": "vendor request", "nouns": "vendor requests", "clean_example": "a clean routine renewal usually needs none",
    "label_note": "",
}


def inr(n) -> str:
    """Indian digit grouping: 4600000 -> ₹46,00,000."""
    n = int(n or 0)
    s = str(abs(n))
    if len(s) > 3:
        head, tail, parts = s[:-3], s[-3:], []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        s = ",".join(([head] if head else []) + parts) + "," + tail
    return ("-₹" if n < 0 else "₹") + s


def _load(path: Path, key: str = None):
    data = json.loads(path.read_text(encoding="utf-8"))
    return data[key] if key else data


# ---------------------------------------------------------------- generic pieces

class GenericRequest(BaseModel):
    """A request in any non-vendor pack: common fields + the pack's own fields (extra keys allowed)."""
    model_config = ConfigDict(extra="allow")
    id: str
    type: str
    entity_id: str = ""
    entity_name: Optional[str] = None
    amount_inr: int = 0
    date: Optional[str] = None
    requested_by: Optional[str] = None
    description: Optional[str] = None
    document_id: Optional[str] = None

    def get(self, field: str, default=None):
        return getattr(self, field, None) if field in type(self).model_fields else (self.model_extra or {}).get(field, default)


_OPS = {
    "==": lambda a, b: a == b, "!=": lambda a, b: a != b,
    "<": lambda a, b: a is not None and a < b, "<=": lambda a, b: a is not None and a <= b,
    ">": lambda a, b: a is not None and a > b, ">=": lambda a, b: a is not None and a >= b,
    "in": lambda a, b: a in b, "not_in": lambda a, b: a not in b,
    "contains": lambda a, b: a is not None and b in a,
}


class GenericMandate:
    """Delegation of authority written as data: {"applies_to": [...]|"*", "when": [{"field","op","value"}], "then": ...}."""

    def __init__(self, data_dir: Path):
        self.doc = _load(data_dir / "mandate.json")
        self.rules = self.doc["rules"]
        self.entities = {e["id"]: e for e in _load(data_dir / "entities.json", "entities")}

    def _value(self, req: GenericRequest, field: str):
        if field.startswith("entity."):
            return self.entities.get(req.entity_id, {}).get(field.split(".", 1)[1])
        return req.get(field)

    def _matches(self, rule: Dict[str, Any], req: GenericRequest, has_precedent: bool) -> bool:
        applies = rule.get("applies_to", "*")
        if applies != "*" and req.type not in applies:
            return False
        if req.type == "out_of_scope" and applies == "*":
            return False  # out-of-scope requests are decided by their own rule only
        for c in rule.get("when", []):
            if "has_precedent" in c:
                if bool(c["has_precedent"]) != has_precedent:
                    return False
                continue
            try:
                if not _OPS[c["op"]](self._value(req, c["field"]), c["value"]):
                    return False
            except TypeError:
                return False  # missing or mistyped value: the condition is not met (conservative)
        return True

    def evaluate(self, req: GenericRequest, has_precedent: bool = True, auto_renewal: bool = False) -> MandateResult:
        res = MandateResult(floor="escalate")
        approvals, restrictions = [], []
        for rule in self.rules:
            if self._matches(rule, req, has_precedent):
                (approvals if rule["then"] in ("approve", "approve_with_conditions") else restrictions).append(rule)
        if approvals:
            res.floor = max((r["then"] for r in approvals), key=STRICTNESS.index)
            for r in restrictions:
                res.floor = stricter(res.floor, r["then"])
        elif restrictions:  # no rule allows it, but a rule says what to do (e.g. ask for the missing budget)
            res.floor = max((r["then"] for r in restrictions), key=STRICTNESS.index)
        else:
            res.breaches.append("No mandate rule allows this request; default is to escalate to the senior.")
        res.triggered = approvals + restrictions
        for r in restrictions:
            res.breaches.append(f"{r['id']}: {r['reason']}")
        for r in res.triggered:
            res.required_conditions += [c for c in r.get("requires_conditions", []) if c not in res.required_conditions]
        return res


GENERIC_CHALLENGER = (
    "You are the Challenger agent of Pratibimb, an AI junior that mirrors how {name} ({title}) decides {nouns}. "
    "Read the documents and the request like a sceptical senior and list concrete risks only. {first}'s red flags: "
    "{red_flags}. Each finding must cite its source exactly in one of these forms: a document clause written like "
    "'{example_cite}', 'Request', or 'History'. Do not invent facts or give generic advice. Severity: high if it could "
    "cost money, cash, compliance or reputation; medium if it weakens our position; low otherwise. Return an empty list "
    "if nothing material."
)


class GenericChallenger:
    def __init__(self, data_dir: Path, persona: Dict[str, str], pack: Dict[str, Any], senior: Dict[str, Any], entities: Dict[str, Any]):
        self.contracts = {d["id"]: d for d in _load(data_dir / "documents.json", "documents")}  # same shape as contracts
        self.persona, self.pack, self.entities = persona, pack, entities
        self.standing = pack.get("standing_documents", [])
        first_doc = next(iter(self.contracts), "DOC-1")
        self.system = GENERIC_CHALLENGER.format(**persona, red_flags="; ".join(senior["decision_style"]["red_flags"]),
                                                example_cite=f"{first_doc} §1")

    def _docs_for(self, req: GenericRequest) -> List[str]:
        ids = [req.document_id] if req.document_id in self.contracts else []
        return ids + [s for s in self.standing if s in self.contracts and s not in ids]

    def has_auto_renewal(self, req) -> bool:
        return False

    def challenge(self, req) -> Tuple[List[ChallengeItem], List[str]]:
        return [], []  # rules baseline: the mandate rules carry the deterministic checks for generic packs

    def challenge_llm(self, case: str, req: GenericRequest) -> Tuple[List[ChallengeItem], List[str]]:
        docs = self._docs_for(req)
        parts = []
        for did in docs:
            d = self.contracts[did]
            parts.append(f"DOCUMENT {did} — {d.get('title', '')}\n" + "\n".join(
                f"{did} §{c['number']} {c.get('title', '')}: {c.get('text', '')}" for c in d.get("clauses", [])))
        doc_text = "\n\n".join(parts) or "DOCUMENTS: none on file for this request."
        ent = self.entities.get(req.entity_id, {})
        hist = (f"HISTORY: {self.pack['entity_label']} {ent.get('name', req.entity_name)}; relationship "
                f"{ent.get('relationship_months', 'unknown')} months; flags: {', '.join(ent.get('flags', [])) or 'none'}; "
                f"{ent.get('note', '')}")
        out: ChallengeList = llm.generate_json("challenger", self.system, f"{case}\n\n{doc_text}\n\n{hist}", ChallengeList)
        valid = {f"{did} §{c['number']}" for did in docs for c in self.contracts[did].get("clauses", [])}
        findings, cits = [], []
        for ch in out.challenges:
            src = ch.source.strip()
            m = re.search(r"([A-Z][A-Z0-9]+-[A-Z0-9-]+)\s*§\s*([\d.]+)", src)
            if m:
                src = f"{m.group(1)} §{m.group(2)}"
                if src not in valid:
                    continue  # cited a clause that does not exist: drop the finding
                cits.append(src)
            elif src not in ("Request", "History"):
                src = "Request"
            findings.append(ChallengeItem(finding=ch.finding, source=src, severity=ch.severity))
        return findings, list(dict.fromkeys(cits))


# ---------------------------------------------------------------- domains

class VendorDomain:
    """Pack 1: Meera Nair, vendor approvals. Keeps the original vendor code paths (and their cached prompts) intact."""
    pack_id = "vendor"

    def __init__(self, data_dir: Path = DATA):
        from agents.challenger import ChallengerAgent
        from agents.interviewer import InterviewerAgent
        from agents.mandate import Mandate

        self.data_dir = data_dir
        self.senior = _load(data_dir / "senior.json")
        self.persona = VENDOR_PERSONA
        self.mandate = Mandate(data_dir)
        self.challenger = ChallengerAgent(data_dir=data_dir)
        self.request_model = VendorRequest
        self.entities = self.mandate.vendors
        self._rules_interviewer = InterviewerAgent()
        self.meta = {
            "id": "vendor", "label": "Vendor approvals", "noun": "vendor request", "entity_label": "Vendor",
            "amount_label": "Annual value", "senior": self.senior["name"], "senior_title": self.senior["title"],
            "verdict_labels": {"approve": "Approve", "approve_with_conditions": "Approve with conditions", "ask": "Ask",
                               "escalate": "Escalate to Meera", "refuse": "Refuse"},
        }

    @property
    def request_keys(self) -> List[str]:
        return ["date", "type", "vendor_id", "vendor_name", "value_inr", "term_months", "sla_breaches_12m",
                "handles_client_data", "advance_pct", "price_increase_pct", "contract_id", "requested_by"]

    def case_text(self, req: VendorRequest) -> str:
        s, style = self.senior, self.senior.get("decision_style", {})
        rel = self.mandate.vendors.get(req.vendor_id, {}).get("relationship_months", "unknown")
        return (
            f"SENIOR: {s['name']}, {s['title']} — {style.get('summary', '')}\n"
            f"Her principles: {' | '.join(style.get('principles', []))}\n"
            f"Her red flags: {' | '.join(style.get('red_flags', []))}\n\n"
            f"NEW REQUEST {req.id} ({req.type})\n"
            f"Vendor: {req.vendor_name or req.vendor_id} (relationship {rel} months)\n"
            f"Value: ₹{req.value_inr:,} · Term: {req.term_months} months · SLA breaches (12m): {req.sla_breaches_12m} · "
            f"Handles client data: {'yes' if req.handles_client_data else 'no'} · Advance: {req.advance_pct}% · "
            f"Price change: {req.price_increase_pct}%\n"
            f"Requested by: {req.requested_by or 'n/a'}\nDescription: {req.description or '(none)'}"
        )

    score = None  # PrecedentAgent's built-in vendor scoring
    brief = None

    def rules_questions(self, req, challenges) -> List[str]:
        return self._rules_interviewer.formulate_questions(req, challenges)

    def rules_headline(self, req, verdict: str) -> str:
        name = req.vendor_name or req.vendor_id
        return {
            "approve": f"Approve {name} for ₹{req.value_inr:,}: inside the mandate, clean record",
            "approve_with_conditions": f"Approve {name} only with protective conditions",
            "escalate": f"Escalate {name} to Meera: outside the mandate",
            "ask": f"Hold {name}: information missing",
            "refuse": "Refuse: out of scope",
        }[verdict]

    def summary(self, r: Dict[str, Any]) -> str:
        return (f"{r.get('type')} · {r.get('vendor_name')} · ₹{int(r.get('value_inr') or 0):,} · {r.get('term_months')} months · "
                f"breaches {r.get('sla_breaches_12m')} · client data {r.get('handles_client_data')} · {r.get('description') or ''}")

    def precedent_record(self, req: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": req.get("type"), "vendor_id": req.get("vendor_id"), "vendor_name": req.get("vendor_name"),
                "value_inr": int(req.get("value_inr") or 0), "term_months": int(req.get("term_months") or 12),
                "sla_breaches_12m": int(req.get("sla_breaches_12m") or 0), "handles_client_data": bool(req.get("handles_client_data"))}


class GenericDomain:
    """Packs 2 and 3 (and any future pack): everything comes from the pack's data files."""

    def __init__(self, pack_id: str, data_dir: Path = None):
        self.pack_id = pack_id
        self.data_dir = data_dir or DATA / "packs" / pack_id
        self.pack = _load(self.data_dir / "pack.json")
        self.senior = _load(self.data_dir / "senior.json")
        s = self.senior
        he = s.get("pronoun", "she") == "he"
        labels = self.pack["verdict_labels"]
        self.persona = {
            "name": s["name"], "first": s["name"].split()[0], "pos": "his" if he else "her", "subj": "he" if he else "she",
            "title": s["title"], "title_at": f"{s['title']} at {s['org']}", "noun": self.pack["noun"], "nouns": self.pack["noun"] + "s",
            "clean_example": f"a clean, well-documented {self.pack['noun']} usually needs none",
            "label_note": " In this domain the verdicts are shown to people as: " + "; ".join(f"{k} = '{v}'" for k, v in labels.items()) + ".",
        }
        self.mandate = GenericMandate(self.data_dir)
        self.entities = self.mandate.entities
        self.challenger = GenericChallenger(self.data_dir, self.persona, self.pack, s, self.entities)
        self.request_model = GenericRequest
        self.fields = self.pack["fields"]
        self.meta = {**{k: self.pack[k] for k in ("id", "label", "noun", "entity_label", "amount_label", "verdict_labels",
                                                  "request_types", "fields", "document_label")},
                     "senior": s["name"], "senior_title": s["title"]}

    @property
    def request_keys(self) -> List[str]:
        return ["date", "type", "entity_id", "entity_name", "amount_inr", "requested_by", "document_id"] + [f["name"] for f in self.fields]

    def _field_text(self, req) -> str:
        out = []
        for f in self.fields:
            v = req.get(f["name"]) if isinstance(req, GenericRequest) else req.get(f["name"])
            if v is None:
                continue
            if f["type"] == "bool":
                v = "yes" if v else "no"
            elif f["type"] == "enum":
                v = str(v).replace("_", " ")
            out.append(f"{f['label']}: {v}")
        return " · ".join(out)

    def case_text(self, req: GenericRequest) -> str:
        s, style, p = self.senior, self.senior.get("decision_style", {}), self.persona
        ent = self.entities.get(req.entity_id, {})
        pos = p["pos"].capitalize()
        return (
            f"SENIOR: {s['name']}, {s['title']} — {style.get('summary', '')}\n"
            f"{pos} principles: {' | '.join(style.get('principles', []))}\n"
            f"{pos} red flags: {' | '.join(style.get('red_flags', []))}\n\n"
            f"NEW {self.pack['noun'].upper()} {req.id} ({self.pack['request_types'].get(req.type, req.type)})\n"
            f"{self.pack['entity_label']}: {req.entity_name or ent.get('name') or req.entity_id} "
            f"(relationship {ent.get('relationship_months', 'unknown')} months; flags: {', '.join(ent.get('flags', [])) or 'none'})\n"
            f"{self.pack['amount_label']}: {inr(req.amount_inr)} · {self._field_text(req)}\n"
            f"Requested by: {req.requested_by or 'n/a'}\nDescription: {req.description or '(none)'}"
        )

    def score(self, req: GenericRequest, dec: Dict[str, Any]) -> float:
        s = 0.0
        if req.entity_id and req.entity_id == dec.get("entity_id") and req.entity_id not in ("A-OTHER", "P-OTHER", "P-EMPLOYEE"):
            s += 0.40
        if req.type == dec.get("type"):
            s += 0.20
        s += min(0.30, 0.075 * sum(req.get(f) == dec.get(f) for f in self.pack.get("similarity_fields", [])))
        if dec.get("mistake"):
            s += 0.15
        return min(round(s, 2), 0.98)

    def brief(self, d: Dict[str, Any]) -> str:
        bits = [f"{d['id']} ({d.get('date', '?')}) {self.pack['request_types'].get(d.get('type'), d.get('type'))} · "
                f"{d.get('entity_name', '?')} · {inr(d.get('amount_inr', 0))} · {self._field_text(d)}",
                f"  Decision: {d.get('decision', '?')} — {d.get('decision_note', '')}"]
        if d.get("conditions"):
            bits.append(f"  Conditions: {'; '.join(d['conditions'])}")
        bits.append(f"  Outcome ({d.get('outcome_status')}): {d.get('outcome')}")
        if d.get("mistake"):
            bits.append(f"  MISTAKE: {d.get('mistake_note')} → lessons {', '.join(d.get('lesson_ids', []))}")
        return "\n".join(bits)

    def rules_questions(self, req, challenges) -> List[str]:
        return []

    def rules_headline(self, req: GenericRequest, verdict: str) -> str:
        name, label = req.entity_name or req.entity_id, self.pack["verdict_labels"][verdict]
        first = self.persona["first"]
        return {
            "approve": f"{label}: {name}, {inr(req.amount_inr)}, inside the mandate",
            "approve_with_conditions": f"{label}: {name}, only with the conditions below",
            "escalate": f"Escalate {name} to {first}: outside the mandate",
            "ask": f"Hold {name}: information missing",
            "refuse": f"{label}: {name}",
        }[verdict]

    def summary(self, r: Dict[str, Any]) -> str:
        return (f"{self.pack['request_types'].get(r.get('type'), r.get('type'))} · {r.get('entity_name')} · "
                f"{inr(r.get('amount_inr'))} · {self._field_text(r)} · {r.get('description') or ''}")

    def precedent_record(self, req: Dict[str, Any]) -> Dict[str, Any]:
        return {k: req.get(k) for k in ["type", "entity_id", "entity_name", "amount_inr"] + [f["name"] for f in self.fields]}


def make_domain(pack_id: str = "vendor", data_dir: Path = None):
    if pack_id == "vendor":
        return VendorDomain(data_dir or DATA)
    return GenericDomain(pack_id, data_dir)
