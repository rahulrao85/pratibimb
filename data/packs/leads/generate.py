"""
Pack 2 — Lead qualification. Synthetic data (written by the team, labelled synthetic in the app).

Vikram Sethi, Head of Sales (India & Middle East) at Meridian Global Services, decides which enquiries and RFPs get a
pursuit team and proposal effort. Writes: pack.json, senior.json, mandate.json, entities.json, documents.json,
decisions.json (30 in memory incl. 4 mistakes + 15 holdouts), lessons.json, requests.json, backtest.json.

    python data/packs/leads/generate.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent

PACK = {
    "id": "leads",
    "label": "Lead qualification",
    "noun": "sales lead",
    "domain": "which sales enquiries and RFPs get a pursuit team and a proposal",
    "entity_label": "Prospect",
    "amount_label": "Est. annual contract value",
    "verdict_labels": {"approve": "Qualify", "approve_with_conditions": "Qualify with conditions", "ask": "Ask",
                       "escalate": "Escalate to Vikram", "refuse": "Disqualify"},
    "request_types": {"inbound_enquiry": "Inbound enquiry", "rfp_invitation": "RFP invitation",
                      "existing_client_upsell": "Existing-client upsell", "partner_referral": "Partner referral",
                      "out_of_scope": "Rate a salesperson (out of scope)"},
    "fields": [
        {"name": "service_line", "label": "Service line", "type": "enum",
         "options": ["finance_ops", "customer_support", "it_service_desk", "data_operations", "new_capability"]},
        {"name": "budget_confirmed", "label": "Budget confirmed", "type": "bool"},
        {"name": "decision_maker_engaged", "label": "Decision-maker engaged", "type": "bool"},
        {"name": "competitors", "label": "Competing vendors", "type": "int"},
        {"name": "payment_terms_days", "label": "Payment terms (days)", "type": "int"},
        {"name": "government_entity", "label": "Government / PSU buyer", "type": "bool"},
        {"name": "response_days", "label": "Days to respond", "type": "int"},
    ],
    "similarity_fields": ["service_line", "government_entity", "budget_confirmed", "decision_maker_engaged"],
    "document_label": "RFP / enquiry",
}

SENIOR = {
    "id": "SEN-002",
    "name": "Vikram Sethi",
    "title": "Head of Sales (India & APAC)",
    "org": "Meridian Global Services (Mumbai delivery centre)",
    "location": "Mumbai, India",
    "tenure_years": 11,
    "reports_to": "Chief Revenue Officer",
    "span": "14 account managers across Mumbai, Singapore and Sydney; ₹62 Cr annual bookings target",
    "pronoun": "he",
    "decision_style": {
        "summary": "Pipeline realist. Would rather lose a deal early than lose a quarter late. Qualifies the buyer before "
                   "the brief, and the cash before the logo.",
        "principles": [
            "A deal without a named decision-maker is a conversation, not a lead.",
            "If we were not in the room before the RFP, we are the price check.",
            "Revenue is only revenue once the money arrives — read the payment terms first.",
            "Free pilots are never free; scope and exit criteria up front.",
            "Grow accounts that pay; fix the ones that don't before selling them more.",
        ],
        "red_flags": [
            "RFP from a buyer we have never met, with many competitors",
            "Payment terms beyond 90 days, or a government buyer without milestone billing",
            "'Free pilot' or 'proof of concept at no cost'",
            "Existing client with invoices overdue beyond 60 days asking for more",
            "Only one contact engaged, or the sponsor has just moved on",
            "Go-live promised in weeks for a large team",
        ],
        "questions_she_always_asks": [
            "Who signs, and have we met them?",
            "Is the budget approved, and by when do they decide?",
            "Were we talking to them before the RFP came out?",
            "What are the payment terms, and how did they pay last time?",
            "What would make us walk away?",
        ],
    },
    "signature_limit_inr": 15000000,
}

MANDATE = {
    "id": "MAN-VIKRAM-2026",
    "senior_id": "SEN-002",
    "currency": "INR",
    "effective_from": "2026-04-01",
    "notes": "Delegation to account managers. Pratibimb may recommend qualifying only where a rule allows it; every other "
             "lead goes to Vikram with a decision file. Vikram makes every final call. Any ask, escalate or disqualify "
             "rule overrides an earlier qualify.",
    "rules": [
        {"id": "S-R1", "applies_to": ["inbound_enquiry", "partner_referral", "existing_client_upsell"],
         "when": [{"field": "amount_inr", "op": "<=", "value": 15000000}, {"field": "budget_confirmed", "op": "==", "value": True},
                  {"field": "decision_maker_engaged", "op": "==", "value": True}, {"field": "payment_terms_days", "op": "<=", "value": 60},
                  {"field": "service_line", "op": "!=", "value": "new_capability"}],
         "then": "approve", "reason": "Core service, inside ₹1.5 Cr, budget and decision-maker confirmed, normal payment terms."},
        {"id": "S-R2", "applies_to": ["inbound_enquiry", "partner_referral", "existing_client_upsell"],
         "when": [{"field": "amount_inr", "op": "<=", "value": 15000000}, {"field": "budget_confirmed", "op": "==", "value": True},
                  {"field": "decision_maker_engaged", "op": "==", "value": True}, {"field": "payment_terms_days", "op": ">", "value": 60},
                  {"field": "payment_terms_days", "op": "<=", "value": 90}, {"field": "service_line", "op": "!=", "value": "new_capability"}],
         "then": "approve_with_conditions", "requires_conditions": ["Credit check on the buyer", "Milestone or advance billing"],
         "reason": "Good lead, slow payer terms: qualify only with credit protection."},
        {"id": "S-R3", "applies_to": "*", "when": [{"field": "budget_confirmed", "op": "==", "value": False}],
         "then": "ask", "reason": "No confirmed budget: find out before spending pursuit effort."},
        {"id": "S-R4", "applies_to": "*", "when": [{"field": "decision_maker_engaged", "op": "==", "value": False}],
         "then": "ask", "reason": "No decision-maker engaged: a conversation, not a lead."},
        {"id": "S-R5", "applies_to": "*", "when": [{"field": "amount_inr", "op": ">", "value": 15000000}],
         "then": "escalate", "reason": "Above the ₹1.5 Cr account-manager authority."},
        {"id": "S-R6", "applies_to": "*", "when": [{"field": "government_entity", "op": "==", "value": True}],
         "then": "escalate", "requires_conditions": ["Milestone billing or mobilisation advance", "EMD and penalty review"],
         "reason": "Government and PSU buyers: procurement rules and payment cycles need Vikram (lesson SL02)."},
        {"id": "S-R7", "applies_to": "*", "when": [{"field": "service_line", "op": "==", "value": "new_capability"}],
         "then": "escalate", "reason": "We do not deliver this today: a capability bet needs Vikram and delivery."},
        {"id": "S-R8", "applies_to": "*", "when": [{"field": "payment_terms_days", "op": ">", "value": 90}],
         "then": "escalate", "reason": "Payment terms beyond 90 days."},
        {"id": "S-R9", "applies_to": ["rfp_invitation"], "when": [],
         "then": "escalate", "reason": "Every RFP response is a ₹-lakhs effort: Vikram decides bid / no-bid (lesson SL01)."},
        {"id": "S-R10", "applies_to": "*", "when": [{"field": "entity.flags", "op": "contains", "value": "do_not_pursue"}],
         "then": "refuse", "reason": "Account on the do-not-pursue list (unpaid dues or conduct issue)."},
        {"id": "S-R11", "applies_to": ["out_of_scope"], "when": [],
         "then": "refuse", "reason": "Pratibimb never rates or ranks people (EU AI Act high-risk)."},
    ],
    "limits_table": [
        {"case": "Core service ≤ ₹1.5 Cr · budget + decision-maker confirmed · ≤ 60-day terms", "action": "Recommend qualify", "signoff": "Vikram, one-click confirm"},
        {"case": "Same, 61–90-day terms", "action": "Qualify only with credit check + milestone billing", "signoff": "Vikram, one-click confirm"},
        {"case": "Budget or decision-maker not confirmed", "action": "Ask", "signoff": "Account manager"},
        {"case": "Above ₹1.5 Cr", "action": "Escalate", "signoff": "Vikram"},
        {"case": "Any RFP invitation", "action": "Escalate (bid / no-bid)", "signoff": "Vikram"},
        {"case": "Government / PSU buyer", "action": "Escalate + billing safeguards", "signoff": "Vikram + Finance"},
        {"case": "New capability we don't deliver", "action": "Escalate", "signoff": "Vikram + Delivery"},
        {"case": "Payment terms > 90 days", "action": "Escalate", "signoff": "Vikram"},
        {"case": "Do-not-pursue account", "action": "Disqualify", "signoff": "N/A"},
        {"case": "Rate or rank a salesperson", "action": "Refuse — out of scope", "signoff": "N/A"},
    ],
}

ENTITIES = [
    {"id": "A-HELIOS", "name": "Helios Insurance", "industry": "insurance", "relationship_months": 0, "flags": ["new_logo"], "note": "Large private insurer; no prior contact."},
    {"id": "A-ORCHID", "name": "Orchid Retail", "industry": "retail", "relationship_months": 30, "flags": [], "avg_payment_days": 38, "note": "Customer-support client since 2024; pays on time."},
    {"id": "A-TARANG", "name": "Tarang Telecom", "industry": "telecom", "relationship_months": 18, "flags": [], "avg_payment_days": 44},
    {"id": "A-NILGIRI", "name": "Nilgiri Foods", "industry": "fmcg", "relationship_months": 0, "flags": ["new_logo"]},
    {"id": "A-SAHYADRI", "name": "Sahyadri Power Distribution", "industry": "utilities", "relationship_months": 0, "flags": ["state_owned"]},
    {"id": "A-VERTEX", "name": "Vertex Logistics", "industry": "logistics", "relationship_months": 26, "flags": ["overdue_history"], "avg_payment_days": 71},
    {"id": "A-KAVERI", "name": "Kaveri Health", "industry": "healthcare", "relationship_months": 0, "flags": ["new_logo"]},
    {"id": "A-LUMINA", "name": "Lumina Bank", "industry": "banking", "relationship_months": 40, "flags": [], "avg_payment_days": 31},
    {"id": "A-ZEPHYR", "name": "Zephyr Airlines", "industry": "aviation", "relationship_months": 0, "flags": ["do_not_pursue"], "note": "₹38 L unpaid from a 2023 engagement; legal notice served."},
    {"id": "A-MERCURY", "name": "Mercury Edtech", "industry": "education", "relationship_months": 0, "flags": ["new_logo"]},
    {"id": "A-INDUS", "name": "Indus Ports Authority", "industry": "government", "relationship_months": 0, "flags": ["government"]},
    {"id": "A-PALMYRA", "name": "Palmyra Hotels", "industry": "hospitality", "relationship_months": 22, "flags": [], "avg_payment_days": 52},
    {"id": "A-GARNET", "name": "Garnet Pharma", "industry": "pharma", "relationship_months": 0, "flags": ["new_logo"]},
    {"id": "A-COBALT", "name": "Cobalt Fintech", "industry": "fintech", "relationship_months": 14, "flags": [], "avg_payment_days": 40},
    {"id": "A-STRAITS", "name": "Straits Mutual (Singapore)", "industry": "insurance", "relationship_months": 16, "flags": [], "avg_payment_days": 33, "note": "Singapore insurer; policy-servicing desk from Mumbai."},
    {"id": "A-SOUTHERNX", "name": "Southern Cross Energy (Australia)", "industry": "utilities", "relationship_months": 0, "flags": ["new_logo"], "note": "Australian retailer exploring offshore billing support."},
    {"id": "A-OTHER", "name": "Other / new prospect", "industry": "other", "relationship_months": 0, "flags": ["new_logo"]},
]

DOCUMENTS = [
    {"id": "RFP-HELIOS-2026", "entity_id": "A-HELIOS", "title": "Helios Insurance — RFP for claims-processing support (180 seats)",
     "clauses": [
         {"number": "1.2", "title": "Participants", "text": "This RFP has been issued to six (6) shortlisted vendors through the procurement portal."},
         {"number": "3.4", "title": "Liability", "text": "The Supplier's liability under this agreement shall be unlimited, including indirect and consequential losses."},
         {"number": "5.1", "title": "Payment", "text": "Undisputed invoices shall be paid within one hundred and twenty (120) days of receipt."},
         {"number": "6.2", "title": "Transition", "text": "Full service go-live is required within four (4) weeks of award for all 180 seats."},
         {"number": "8.3", "title": "Service credits", "text": "A service credit of 10% of the monthly fee applies for each SLA missed, uncapped."},
         {"number": "11.1", "title": "Submission", "text": "Responses are due within eight (8) calendar days of issue."}]},
    {"id": "ENQ-ORCHID-2026", "entity_id": "A-ORCHID", "title": "Orchid Retail — email: add Hindi chat support",
     "clauses": [
         {"number": "1", "title": "Request", "text": "Expand the existing customer-support team by 12 seats to cover Hindi chat, from 1 November."},
         {"number": "2", "title": "Budget", "text": "Budget approved by our COO, Ms. R. Shah, who will sign the change order."},
         {"number": "3", "title": "Terms", "text": "Same rates and 45-day payment terms as the current statement of work."}]},
    {"id": "ENQ-SAHYADRI-2026", "entity_id": "A-SAHYADRI", "title": "Sahyadri Power — partner referral note",
     "clauses": [
         {"number": "1", "title": "Referral", "text": "Referred by our implementation partner for consumer billing-dispute handling, 60 seats."},
         {"number": "2", "title": "Buyer", "text": "Sahyadri Power Distribution is a subsidiary of the state electricity board."},
         {"number": "3", "title": "Commercials", "text": "Payment on monthly certification by the user department; L1 (lowest price) selection."}]},
]

STYLE_NOTE = "decision_note"


def dec(i, date, typ, ent, amount, f, decision, note, outcome, status="good", conditions=(), reasons=(), lessons=(),
        mistake="", holdout=False, doc=None, by="Account manager"):
    e = next(x for x in ENTITIES if x["id"] == ent)
    d = {"id": f"SL-{i:04d}", "date": date, "type": typ, "entity_id": ent, "entity_name": e["name"], "amount_inr": amount,
         "requested_by": by, **f, "decision": decision, "decision_note": note, "reasons": list(reasons) or [note],
         "conditions": list(conditions), "document_id": doc, "outcome": outcome, "outcome_status": status,
         "mistake": bool(mistake), "mistake_note": mistake, "lesson_ids": list(lessons), "holdout": holdout}
    return d


def F(service="customer_support", budget=True, dm=True, comp=2, terms=45, gov=False, days=20):
    return {"service_line": service, "budget_confirmed": budget, "decision_maker_engaged": dm, "competitors": comp,
            "payment_terms_days": terms, "government_entity": gov, "response_days": days}


DECISIONS = [
    # ---- 30 in memory (4 mistakes) ----
    dec(1, "2024-05-14", "existing_client_upsell", "A-ORCHID", 4200000, F(), "approved", "Orchid adding 15 support seats; same terms, COO signing.", "Signed in 3 weeks; renewed 2025."),
    dec(2, "2024-06-03", "inbound_enquiry", "A-TARANG", 6800000, F("it_service_desk"), "approved", "Telecom service-desk enquiry, budget and CIO engaged.", "Won; live in 6 weeks."),
    dec(3, "2024-07-19", "rfp_invitation", "A-HELIOS", 52000000, F("customer_support", comp=6, terms=120, days=9, dm=False), "escalated",
        "Pursued a 6-vendor RFP with no prior relationship; 300 hours of solutioning.", "Lost on price to the incumbent; never met the decision-maker.",
        "bad", mistake="We were the price check: an RFP from a buyer we never met, with 5+ competitors, is column fodder. Bid only with a sponsor engaged before the RFP.",
        lessons=["SL01"]),
    dec(4, "2024-08-22", "partner_referral", "A-INDUS", 31000000, F("data_operations", terms=120, gov=True), "approved",
        "Won a port-authority data-entry contract on the GeM portal at L1 price, 120-day certification-based payment.", "Collections dragged 9 months; margin wiped by working-capital cost.",
        "bad", mistake="Government payment cycles: certification-based payment without milestone billing or mobilisation advance destroys margin.", lessons=["SL02"]),
    dec(5, "2024-09-10", "inbound_enquiry", "A-NILGIRI", 3500000, F("finance_ops", budget=False), "asked", "Interest but no budget line; asked for budget owner and timing.", "Budget approved in Q4; won ₹38 L."),
    dec(6, "2024-10-02", "existing_client_upsell", "A-LUMINA", 9500000, F("finance_ops"), "approved", "Lumina reconciliation scope extension; clean payer.", "Delivered; NPS 62."),
    dec(7, "2024-10-28", "inbound_enquiry", "A-KAVERI", 2800000, F("customer_support", terms=75), "approved_with_conditions",
        "Healthcare patient-support desk, 75-day terms.", "Paid on milestones; no overdue.", conditions=["Credit check", "Milestone billing"]),
    dec(8, "2024-11-15", "inbound_enquiry", "A-MERCURY", 1800000, F("data_operations", dm=True), "approved_with_conditions",
        "Edtech wanted a 6-week free pilot before deciding; agreed.", "Pilot ran 4 months unpaid as scope grew; client chose a cheaper vendor.",
        "bad", mistake="'Free' pilots are never free: always a paid pilot with fixed scope, duration and exit criteria.", lessons=["SL03"]),
    dec(9, "2024-12-04", "existing_client_upsell", "A-VERTEX", 7400000, F("customer_support"), "approved",
        "Vertex asked to double the tracking-desk team while 3 invoices were 70+ days overdue.", "Overdue grew to ₹96 L; part written off in 2025.",
        "bad", mistake="Never expand an account with invoices overdue beyond 60 days until they are cleared or secured.", lessons=["SL04"]),
    dec(10, "2025-01-09", "partner_referral", "A-PALMYRA", 2400000, F("customer_support"), "approved", "Hotel reservations desk via partner; GM signing.", "Won; expanded twice."),
    dec(11, "2025-01-27", "rfp_invitation", "A-GARNET", 21000000, F("finance_ops", comp=3, days=21), "escalated",
        "Pharma RFP; we shaped the requirement with their CFO for 4 months before release.", "Won; ₹2.1 Cr ACV.", reasons=["Sponsor engaged pre-RFP", "3 competitors"]),
    dec(12, "2025-02-18", "inbound_enquiry", "A-ZEPHYR", 5600000, F("customer_support"), "rejected", "Airline back with a new enquiry; ₹38 L still unpaid from 2023.", "Correct: their other vendors also faced non-payment."),
    dec(13, "2025-03-06", "inbound_enquiry", "A-COBALT", 3900000, F("it_service_desk", dm=False), "asked", "Fintech enquiry from an analyst; asked to meet the CTO.", "CTO meeting held; won ₹41 L."),
    dec(14, "2025-03-24", "existing_client_upsell", "A-TARANG", 5100000, F("customer_support", terms=60), "approved", "Tarang adding retention calls; same terms.", "Delivered."),
    dec(15, "2025-04-11", "inbound_enquiry", "A-OTHER", 16500000, F("new_capability"), "escalated", "Request for AI model red-teaming: not a service we deliver.", "No-bid after delivery review; right call."),
    dec(16, "2025-05-02", "rfp_invitation", "A-KAVERI", 9000000, F("customer_support", comp=7, days=7, dm=False), "rejected",
        "Applied SL01: 7-vendor RFP, no contact before, 7 days to respond.", "Saved ~250 hours; the incumbent retained.", lessons=["SL01"]),
    dec(17, "2025-05-26", "partner_referral", "A-SAHYADRI", 8000000, F("customer_support", gov=True, terms=90), "escalated",
        "Applied SL02: state utility; asked for mobilisation advance and monthly milestones.", "Buyer refused; no-bid. Avoided another Indus.", lessons=["SL02"]),
    dec(18, "2025-06-17", "inbound_enquiry", "A-NILGIRI", 3000000, F("finance_ops"), "approved_with_conditions",
        "Applied SL03: wanted a free proof of concept; offered a 4-week paid pilot with exit criteria.", "Paid pilot converted to a ₹30 L contract.", conditions=["Paid pilot, fixed scope", "Exit criteria agreed"], lessons=["SL03"]),
    dec(19, "2025-07-08", "existing_client_upsell", "A-VERTEX", 4600000, F("customer_support"), "asked",
        "Applied SL04: Vertex upsell held until ₹52 L overdue cleared.", "Cleared in 5 weeks; upsell signed with 30-day terms.", lessons=["SL04"]),
    dec(20, "2025-07-29", "inbound_enquiry", "A-MERCURY", 2200000, F("data_operations", budget=False, dm=False), "asked", "Two gaps: no budget, no decision-maker.", "Went quiet; no effort wasted."),
    dec(21, "2025-08-19", "existing_client_upsell", "A-LUMINA", 12500000, F("finance_ops"), "approved", "Lumina adding month-end close support.", "Won."),
    dec(22, "2025-09-09", "inbound_enquiry", "A-PALMYRA", 1600000, F("customer_support", terms=90), "approved_with_conditions", "Seasonal desk at 90-day terms.", "Paid at day 84.", conditions=["Credit check", "Milestone billing"]),
    dec(23, "2025-10-01", "existing_client_upsell", "A-STRAITS", 8600000, F("customer_support", terms=30), "approved", "Straits Mutual adding a claims-intake desk served from Mumbai; Singapore COO signing.", "Won; expanded in 2026."),
    dec(24, "2025-10-23", "rfp_invitation", "A-LUMINA", 34000000, F("finance_ops", comp=2, days=30), "escalated", "Existing client RFP, we co-wrote scope.", "Won; ₹3.4 Cr."),
    dec(25, "2025-11-12", "inbound_enquiry", "A-GARNET", 4800000, F("data_operations"), "approved", "Pharma data cleansing; CFO sponsor.", "Won."),
    dec(26, "2025-12-03", "inbound_enquiry", "A-OTHER", 900000, F("customer_support", budget=False), "asked", "Small enquiry, budget unknown.", "Converted at ₹9 L."),
    dec(27, "2026-01-20", "existing_client_upsell", "A-ORCHID", 3800000, F("customer_support"), "approved", "Orchid festive-season seats.", "Delivered."),
    dec(28, "2026-02-10", "rfp_invitation", "A-SOUTHERNX", 26000000, F("finance_ops", comp=5, days=12, dm=False), "rejected", "Applied SL01: Australian RFP, 5 vendors, never met them.", "No-bid; incumbent onshore BPO retained.", lessons=["SL01"]),
    dec(29, "2026-03-04", "partner_referral", "A-INDUS", 12000000, F("data_operations", gov=True, terms=120), "escalated", "Port authority again; asked for advance.", "Declined by buyer; no-bid.", lessons=["SL02"]),
    dec(30, "2026-03-25", "inbound_enquiry", "A-KAVERI", 3300000, F("customer_support"), "approved", "Kaveri appointment desk; COO sponsor.", "Won."),
    # ---- 15 holdouts (back-test; never in memory) ----
    dec(131, "2026-07-02", "existing_client_upsell", "A-ORCHID", 2900000, F(), "approved", "Orchid adding 10 seats.", "Signed.", holdout=True),
    dec(132, "2026-07-09", "inbound_enquiry", "A-COBALT", 3600000, F("it_service_desk"), "approved", "Clean fintech desk enquiry.", "Won.", holdout=True),
    dec(133, "2026-07-15", "inbound_enquiry", "A-PALMYRA", 2100000, F("customer_support", terms=80), "approved_with_conditions", "80-day terms.", "Won with milestones.", conditions=["Credit check", "Milestone billing"], holdout=True),
    dec(134, "2026-07-22", "inbound_enquiry", "A-NILGIRI", 2500000, F("finance_ops", budget=False), "asked", "No budget yet.", "Pending.", holdout=True),
    dec(135, "2026-07-30", "inbound_enquiry", "A-MERCURY", 1900000, F("data_operations", dm=False), "asked", "Only an analyst engaged.", "Pending.", holdout=True),
    dec(136, "2026-08-06", "existing_client_upsell", "A-LUMINA", 19000000, F("finance_ops"), "escalated", "Above ₹1.5 Cr.", "Won by Vikram.", holdout=True),
    dec(137, "2026-08-13", "partner_referral", "A-INDUS", 9000000, F("data_operations", gov=True, terms=90), "escalated", "Government buyer.", "No-bid.", holdout=True),
    dec(138, "2026-08-20", "inbound_enquiry", "A-OTHER", 7000000, F("new_capability"), "escalated", "Not a service we deliver.", "No-bid.", holdout=True),
    dec(139, "2026-08-27", "inbound_enquiry", "A-ZEPHYR", 4000000, F("customer_support"), "rejected", "Do-not-pursue account.", "Correct.", holdout=True),
    dec(140, "2026-09-03", "out_of_scope", "A-OTHER", 0, F(), "rejected", "Asked to rank account managers for bonuses.", "Refused.", holdout=True),
    dec(141, "2026-09-08", "existing_client_upsell", "A-VERTEX", 5200000, F("customer_support", terms=45), "asked",
        "Upsell held: two invoices 75 days overdue (SL04).", "Cleared, then signed.", lessons=["SL04"], holdout=True),
    dec(142, "2026-09-12", "inbound_enquiry", "A-GARNET", 2600000, F("data_operations"), "approved_with_conditions",
        "Wanted a free 6-week pilot; offered paid pilot (SL03).", "Converted.", conditions=["Paid pilot, fixed scope", "Exit criteria"], lessons=["SL03"], holdout=True),
    dec(143, "2026-09-17", "partner_referral", "A-OTHER", 6400000, F("customer_support", terms=60), "escalated",
        "Buyer turned out to be a state-board subsidiary (SL02).", "Billing safeguards negotiated by Vikram.", lessons=["SL02"], holdout=True),
    dec(144, "2026-09-23", "inbound_enquiry", "A-KAVERI", 4400000, F("customer_support", terms=45), "asked",
        "Sponsor left last week; only procurement remains.", "Re-engaged the new COO; signed later.", holdout=True),
    dec(145, "2026-09-29", "existing_client_upsell", "A-TARANG", 3200000, F("it_service_desk"), "approved",
        "URGENT but clean: CIO wants 20 seats next month, PO ready.", "Signed in 4 days.", holdout=True),
]

LESSONS = [
    {"id": "SL01", "title": "No column-fodder RFPs", "rule": "Bid on an RFP only if we were engaged with a sponsor before it was issued; with 5+ competitors and no prior contact, decline.",
     "trigger": "rfp_invitation, or any lead where we had no contact before the request and there are many competitors", "action_required": "Escalate as no-bid unless a sponsor is named; record why.", "source_decision_ids": ["SL-0003"]},
    {"id": "SL02", "title": "Government payment cycles", "rule": "Government, PSU or state-owned buyers (including subsidiaries, and GeM-portal bids) need milestone billing or a mobilisation advance before we qualify.",
     "trigger": "Buyer is government, a PSU, state-owned, or a subsidiary of one", "action_required": "Escalate with billing safeguards; never accept certification-only payment.", "source_decision_ids": ["SL-0004"]},
    {"id": "SL03", "title": "Paid pilots only", "rule": "Any 'free pilot' or no-cost proof of concept becomes a paid pilot with fixed scope, duration and exit criteria.",
     "trigger": "Request mentions a free pilot, PoC at no cost, or trial before commitment", "action_required": "Qualify only with paid-pilot conditions.", "source_decision_ids": ["SL-0008"]},
    {"id": "SL04", "title": "Clear overdue before expanding", "rule": "Never expand an account with invoices overdue beyond 60 days until cleared or secured.",
     "trigger": "Existing client with invoices overdue beyond 60 days", "action_required": "Ask: hold the upsell until overdue is cleared or an advance is agreed.", "source_decision_ids": ["SL-0009"]},
]
for l in LESSONS:
    l.update({"version": 1, "status": "approved", "created": "2025-04-01", "approved_by": "Vikram Sethi", "half_life_days": 540})

REQ_FIELDS = ["id", "date", "type", "entity_id", "entity_name", "amount_inr", "requested_by", "document_id",
              "service_line", "budget_confirmed", "decision_maker_engaged", "competitors", "payment_terms_days",
              "government_entity", "response_days"]

REQUESTS = [
    {"id": "REQ-L01", "date": "2026-10-04", "type": "existing_client_upsell", "entity_id": "A-ORCHID", "entity_name": "Orchid Retail",
     "amount_inr": 4600000, "requested_by": "Account manager – N. Desai", "document_id": "ENQ-ORCHID-2026", **F(),
     "description": "Orchid wants 12 more support seats for Hindi chat from 1 November, same rates and 45-day terms. Their COO approved the budget and will sign."},
    {"id": "REQ-L02", "date": "2026-10-04", "type": "rfp_invitation", "entity_id": "A-HELIOS", "entity_name": "Helios Insurance",
     "amount_inr": 32000000, "requested_by": "Account manager – P. Fernandes", "document_id": "RFP-HELIOS-2026",
     **F("customer_support", budget=True, dm=False, comp=6, terms=120, days=8),
     "description": "Big RFP just landed through Helios's procurement portal: 180-seat claims support, ₹3.2 Cr a year. Huge logo. We should go all out — response due in 8 days."},
    {"id": "REQ-L03", "date": "2026-10-04", "type": "partner_referral", "entity_id": "A-SAHYADRI", "entity_name": "Sahyadri Power Distribution",
     "amount_inr": 7200000, "requested_by": "Partner manager – S. Kulkarni", "document_id": "ENQ-SAHYADRI-2026",
     **F("customer_support", terms=60, gov=False),
     "description": "Partner referral: 60-seat billing-dispute desk for Sahyadri Power. Partner says it's a quick win and the budget is there."},
]

BACKTEST_TEXT = {
    "SL-0131": "Orchid wants 10 more support seats at the current rates; their COO approved the budget.",
    "SL-0132": "Cobalt Fintech enquiry for an L1 IT service desk; CTO engaged, budget approved.",
    "SL-0133": "Palmyra Hotels wants a seasonal reservations desk; budget approved, GM signing, asks for 80-day payment terms.",
    "SL-0134": "Nilgiri Foods is interested in finance-ops support but has not got a budget line yet.",
    "SL-0135": "Mercury Edtech: an analyst asked for a proposal for data operations; no senior contact yet.",
    "SL-0136": "Lumina Bank wants to extend reconciliation and add month-end close: ₹1.9 Cr a year.",
    "SL-0137": "Partner referral from Indus Ports Authority for data-entry work at 90-day terms.",
    "SL-0138": "Enquiry for us to build and run an AI model red-teaming team.",
    "SL-0139": "Zephyr Airlines has sent a new customer-support enquiry.",
    "SL-0140": "Please rank our account managers by performance so we can decide bonuses.",
    "SL-0141": "Vertex Logistics wants 15 more tracking-desk seats at the same 45-day terms. Note from finance: their last two invoices are 75 days overdue.",
    "SL-0142": "Garnet Pharma wants to try our data-cleansing team: they ask for a 6-week free pilot before signing anything.",
    "SL-0143": "Partner referral: 50-seat consumer helpdesk for a power distributor. The partner mentions the buyer is a subsidiary of the state electricity board.",
    "SL-0144": "Kaveri Health support desk expansion is ready to sign: budget approved. Our sponsor, their COO, left last week; procurement is now handling it.",
    "SL-0145": "URGENT: Tarang's CIO wants 20 more service-desk seats from next month. Budget approved, PO ready, same terms.",
}
EXPECTED = {"approved": "approve", "approved_with_conditions": "approve_with_conditions", "asked": "ask", "escalated": "escalate", "rejected": "refuse"}


def main():
    holdouts = [d for d in DECISIONS if d["holdout"]]
    backtest = [{"decision_id": d["id"], "request_description": BACKTEST_TEXT[d["id"]], "expected_verdict": EXPECTED[d["decision"]],
                 "expected_citations": d["lesson_ids"], "why": d["decision_note"]} for d in holdouts]
    files = {
        "pack.json": PACK, "senior.json": SENIOR, "mandate.json": MANDATE,
        "entities.json": {"entities": ENTITIES}, "documents.json": {"documents": DOCUMENTS},
        "decisions.json": {"decisions": DECISIONS}, "lessons.json": {"lessons": LESSONS},
        "requests.json": {"requests": REQUESTS, "request_fields": REQ_FIELDS}, "backtest.json": {"backtest_cases": backtest},
    }
    for name, payload in files.items():
        (HERE / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"leads: {len(DECISIONS) - len(holdouts)} in memory ({sum(d['mistake'] for d in DECISIONS)} mistakes), {len(holdouts)} holdouts, "
          f"{len(LESSONS)} lessons, {len(MANDATE['rules'])} rules, {len(REQUESTS)} demo requests")


if __name__ == "__main__":
    main()
