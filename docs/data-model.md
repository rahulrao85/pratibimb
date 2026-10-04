# Pratibimb — Data Model

Pratibimb reads six primary data collections. Every entity is keyed so an agentic verdict
can cite the exact decision, lesson, contract clause, or mandate rule it derived from.
Auditability and explainability are first-class architectural features.

## 1. Entities

| Entity | File | Key | Purpose |
|---|---|---|---|
| Senior | `senior.json` | `id` (SEN-001) | Profile, decision style principles, red flags, instinct questions. |
| Mandate | `mandate.json` | `rules[].id` (M-R#) | Delegation of authority: what can be approved vs escalated. |
| Vendor | `vendors.json` | `id` (V-####) | Vendor master, risk flags, relationship age, SLA history. |
| Contract | `contracts.json` | `id` (CN-####) | Grounded legal source of truth. Clause-level citations. |
| Decision | `decisions.json` | `id` (DEC-####) | Episodic memory. Request + reason + outcome + mistake links. |
| Lesson | `lessons.json` | `id` (L01…) | Lessons approved by the senior: L01–L06 from past mistakes, L07+ from live overrides. |
| Request | `requests.json` | `id` (REQ-###) | Live incoming vendor requests for evaluation. |
| Backtest | `backtest.json` | `decision_id` | 15 held-out cases: the requester's text (`request_description`) + the senior's verdict. |
| Override | `overrides.json` | `id` (OVR-###) | Runtime only: the senior's overrides, filed as precedents (gitignored; reset via `/api/demo/reset`). |

## 2. Decision Record Schema

```jsonc
{
  "id": "DEC-0087",
  "date": "2025-03-21",
  "type": "vendor_renewal",           // vendor_renewal | vendor_onboarding | one_time_spend | contract_amendment
  "vendor_id": "V-BRIGHTLINE",
  "value_inr": 560000,
  "term_months": 12,
  "sla_breaches_12m": 2,
  "requested_by": "Admin – A. Kulkarni",
  "decision": "approved",             // approved | approved_with_conditions | asked | escalated | rejected
  "decision_note": "Approved renewal despite 2 breaches due to lack of immediate supplier alternatives.",
  "reasons": ["Essential facility service", "Vendor committed verbally to fix performance"],
  "conditions": [],
  "contract_id": "CN-BRIGHTLINE-2025",
  "outcome": "Client audit 4 months later failed due to facility cleanliness; INR 3.2 lakh penalty imposed.",
  "outcome_status": "bad",            // good | mixed | bad | pending
  "mistake": true,
  "mistake_note": "Never renew a vendor with 2+ breaches without penalty clause and 90-day exit.",
  "lesson_ids": ["L01"],
  "cited_decision_ids": [],
  "holdout": false,                    // true => hidden from engine at inference (reserved for backtest)
  "followed_mandate": true
}
```

## 3. Mandate Rule Schema

```jsonc
{
  "id": "M-R1",
  "applies_to": "vendor_renewal",
  "when": { "max_value_inr": 500000, "max_sla_breaches_12m": 0, "min_relationship_months": 12, "no_open_dispute": true },
  "then": "approve",                  // approve | approve_with_conditions | escalate | refuse
  "requires_conditions": [],
  "reason": "Routine renewal inside the ₹5,00,000 signature limit, clean record."
}
```

## 4. Verdict Schema (Engine Output Contract)

```jsonc
{
  "request_id": "REQ-002",
  "verdict": "escalate",              // approve | approve_with_conditions | escalate | ask | refuse
  "headline": "Renew Kestrel for 12 months only, with service credits and a 90-day exit",
  "confidence": "high",               // high | medium | low
  "mandate_check": {
    "within_limits": false,
    "breaches": ["Above ₹5,00,000 limit", "2+ SLA breaches (3)", "Auto-renewal clause present"]
  },
  "precedents": [
    { "decision_id": "DEC-0087", "similarity": 0.91, "outcome_status": "bad", "takeaway": "Renewal with 2 breaches failed client audit" }
  ],
  "challenges": [
    { "finding": "Clause 9.2 auto-renews for 24 months with no SLA penalty", "source": "CN-KESTREL-2025 §9.2", "severity": "high" }
  ],
  "questions_for_requester": [
    "Has a competing quote been requested since 2024?",
    "Can desktop support SLAs be split by severity?"
  ],
  "recommended_conditions": [
    "5% service credit per SLA breach",
    "90-day termination for convenience without penalty",
    "Cap term to 12 months"
  ],
  "citations": [ "DEC-0087", "L01", "CN-KESTREL-2025 §9.2", "M-R3" ],
  "reasoning": "Two breaches and a 24-month evergreen clause…",   // in the senior's voice
  "lessons_applied": [ "L01", "L03" ],
  "engine": "gemini-3.8-flash",       // or "rules" (baseline / PRATIBIMB_LLM=off / daily cap reached)
  "cost_usd": 0.0042, "cost_inr": 0.37, "elapsed_ms": 5933
}
```

## 5. Lesson Schema

```jsonc
{
  "id": "L01",
  "version": 2,
  "status": "approved",               // approved | proposed
  "rule": "No renewal with 2+ SLA breaches without a service-credit clause and a 90-day exit.",
  "source_decision_ids": ["DEC-0087"],
  "created": "2025-07-28",
  "approved_by": "Meera Nair",
  "half_life_days": 540
}
```
