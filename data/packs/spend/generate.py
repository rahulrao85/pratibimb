"""
Pack 3 — Spend & payment exceptions. Synthetic data (written by the team, labelled synthetic in the app).

Kavya Iyer, Financial Controller at Meridian Global Services (Mumbai), decides the exceptions her accounts-payable team
cannot clear alone: invoices without a PO, price variances, budget overruns, expense exceptions and advance payments.
Indian practice built in: GST input credit only once the invoice shows in GSTR-2B, MSME suppliers paid within 45 days
(MSMED Act; Income-tax Act s.43B(h)), no-PO limits and invoice splitting, bank-detail-change fraud, the March rush.

    python data/packs/spend/generate.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent

PACK = {
    "id": "spend",
    "label": "Spend & payment exceptions",
    "noun": "spend exception",
    "domain": "invoice, budget, expense and advance-payment exceptions the accounts-payable team cannot clear alone",
    "entity_label": "Supplier",
    "amount_label": "Amount",
    "verdict_labels": {"approve": "Approve payment", "approve_with_conditions": "Approve with conditions", "ask": "Hold & ask",
                       "escalate": "Escalate to Kavya", "refuse": "Reject"},
    "request_types": {"invoice_without_po": "Invoice without PO", "price_variance": "Price variance vs PO",
                      "budget_overrun": "Budget overrun", "expense_exception": "Expense exception",
                      "advance_payment": "Advance / early payment", "out_of_scope": "Rate a team member (out of scope)"},
    "fields": [
        {"name": "cost_centre", "label": "Cost centre", "type": "enum", "options": ["delivery", "it", "facilities", "sales", "admin"]},
        {"name": "grn_matched", "label": "Goods/service receipt confirmed (GRN)", "type": "bool"},
        {"name": "variance_pct", "label": "Variance vs PO / budget (%)", "type": "float"},
        {"name": "gst_in_2b", "label": "Invoice visible in GSTR-2B", "type": "bool"},
        {"name": "receipt_attached", "label": "Receipt attached", "type": "bool"},
        {"name": "supplier_msme", "label": "Supplier is MSME-registered", "type": "bool"},
        {"name": "days_since_invoice", "label": "Days since invoice accepted", "type": "int"},
        {"name": "advance_pct", "label": "Advance (%)", "type": "int"},
        {"name": "requester_is_approver", "label": "Requester would approve own request", "type": "bool"},
    ],
    "similarity_fields": ["cost_centre", "grn_matched", "gst_in_2b", "supplier_msme"],
    "document_label": "Invoice / policy",
    "standing_documents": ["POL-AP-2026"],
}

SENIOR = {
    "id": "SEN-003",
    "name": "Kavya Iyer",
    "title": "Financial Controller",
    "org": "Meridian Global Services (Mumbai delivery centre)",
    "location": "Mumbai, India",
    "tenure_years": 8,
    "reports_to": "CFO (Singapore)",
    "span": "Accounts payable team of 9; ₹140 Cr annual spend; statutory audit owner",
    "pronoun": "she",
    "decision_style": {
        "summary": "Chartered accountant. Pays fast when the paper is right and never when it isn't. Treats every exception "
                   "as either a control gap or a fraud attempt until the documents say otherwise.",
        "principles": [
            "No PO, no surprise: retro POs are for emergencies, not habits.",
            "Two invoices just under the limit are one invoice over it.",
            "Bank details change by phone call, never by email.",
            "GST we cannot claim is cost we chose to pay.",
            "Pay small suppliers on time — the 45-day rule is the law, not a courtesy.",
        ],
        "red_flags": [
            "Invoices from the same supplier for the same job, each just under ₹1 lakh",
            "New bank account details on an invoice or in an email",
            "Invoice not visible in GSTR-2B",
            "Year-end spend to 'use the budget before it lapses'",
            "Advance requested by a supplier who mentions cash trouble",
            "Anyone approving their own claim",
        ],
        "questions_she_always_asks": [
            "Where is the PO, and why wasn't it raised before the work?",
            "Has anyone confirmed the goods or service actually arrived?",
            "Is this the first invoice for this job?",
            "Do the bank details match the supplier master?",
            "Can we claim the GST on this?",
        ],
    },
    "signature_limit_inr": 500000,
}

MANDATE = {
    "id": "MAN-KAVYA-2026",
    "senior_id": "SEN-003",
    "currency": "INR",
    "effective_from": "2026-04-01",
    "notes": "Delegation to accounts-payable managers. Pratibimb may recommend approval only where a rule allows it; every "
             "other exception goes to Kavya with a decision file. Kavya makes every final call. Any ask, escalate or reject "
             "rule overrides an earlier approve.",
    "rules": [
        {"id": "F-R1", "applies_to": ["price_variance"], "when": [{"field": "variance_pct", "op": "<=", "value": 5},
            {"field": "amount_inr", "op": "<=", "value": 50000}],
         "then": "approve", "reason": "Variance within 5% on a small invoice: normal rounding and freight."},
        {"id": "F-R2", "applies_to": ["invoice_without_po"], "when": [{"field": "amount_inr", "op": "<=", "value": 100000}],
         "then": "approve_with_conditions", "requires_conditions": ["Retro PO within 3 working days", "Reason recorded by the budget owner"],
         "reason": "Small no-PO invoice: pay, but close the control gap (policy POL-AP-2026 §2.1)."},
        {"id": "F-R3", "applies_to": ["invoice_without_po"], "when": [{"field": "amount_inr", "op": ">", "value": 100000}],
         "then": "escalate", "reason": "No-PO invoice above ₹1 lakh."},
        {"id": "F-R4", "applies_to": ["price_variance"], "when": [{"field": "variance_pct", "op": ">", "value": 5}],
         "then": "escalate", "reason": "Variance above 5% needs a revised PO or Kavya's sign-off."},
        {"id": "F-R5", "applies_to": "*", "when": [{"field": "grn_matched", "op": "==", "value": False}],
         "then": "ask", "reason": "Nobody has confirmed the goods or service arrived: no payment without a GRN."},
        {"id": "F-R6", "applies_to": "*", "when": [{"field": "gst_in_2b", "op": "==", "value": False}],
         "then": "approve_with_conditions", "requires_conditions": ["Pay the base amount; hold the GST portion until the invoice shows in GSTR-2B"],
         "reason": "Input tax credit is only claimable once the supplier has filed: protect the GST."},
        {"id": "F-R7", "applies_to": ["expense_exception"], "when": [{"field": "amount_inr", "op": "<=", "value": 15000},
            {"field": "receipt_attached", "op": "==", "value": True}],
         "then": "approve", "reason": "Small expense exception with a receipt."},
        {"id": "F-R8", "applies_to": ["expense_exception"], "when": [{"field": "receipt_attached", "op": "==", "value": False}],
         "then": "ask", "reason": "No receipt, no reimbursement."},
        {"id": "F-R9", "applies_to": ["budget_overrun"], "when": [{"field": "variance_pct", "op": "<=", "value": 10},
            {"field": "amount_inr", "op": "<=", "value": 500000}],
         "then": "approve_with_conditions", "requires_conditions": ["Funding moved from a named cost line", "Budget owner's written reason"],
         "reason": "Overrun within 10%: allowed if funded by a reallocation."},
        {"id": "F-R10", "applies_to": ["budget_overrun"], "when": [{"field": "variance_pct", "op": ">", "value": 10}],
         "then": "escalate", "reason": "Overrun above 10% of the cost-centre budget."},
        {"id": "F-R11", "applies_to": ["advance_payment"], "when": [{"field": "advance_pct", "op": "<=", "value": 30},
            {"field": "entity.relationship_months", "op": ">=", "value": 12}],
         "then": "approve", "reason": "Advance up to 30% to a supplier with a year of history."},
        {"id": "F-R12", "applies_to": ["advance_payment"], "when": [{"field": "advance_pct", "op": ">", "value": 30}],
         "then": "escalate", "reason": "Advance above 30%."},
        {"id": "F-R13", "applies_to": ["advance_payment"], "when": [{"field": "entity.relationship_months", "op": "<", "value": 12}],
         "then": "escalate", "reason": "Advance to a supplier with under a year of history."},
        {"id": "F-R14", "applies_to": "*", "when": [{"field": "supplier_msme", "op": "==", "value": True},
            {"field": "days_since_invoice", "op": ">=", "value": 30}],
         "then": "approve_with_conditions", "requires_conditions": ["Pay within 45 days of acceptance (MSMED Act; Income-tax Act s.43B(h))"],
         "reason": "MSME supplier nearing the 45-day legal limit: late payment costs interest and the tax deduction."},
        {"id": "F-R15", "applies_to": "*", "when": [{"field": "requester_is_approver", "op": "==", "value": True}],
         "then": "refuse", "reason": "Segregation of duties: nobody approves their own request."},
        {"id": "F-R16", "applies_to": "*", "when": [{"field": "amount_inr", "op": ">", "value": 500000}],
         "then": "escalate", "reason": "Above Kavya's delegated ₹5 lakh."},
        {"id": "F-R17", "applies_to": ["out_of_scope"], "when": [],
         "then": "refuse", "reason": "Pratibimb never rates or ranks people (EU AI Act high-risk)."},
    ],
    "limits_table": [
        {"case": "Price variance ≤ 5% on invoices ≤ ₹50k", "action": "Recommend approve", "signoff": "Kavya, one-click confirm"},
        {"case": "No-PO invoice ≤ ₹1 lakh", "action": "Approve with retro PO in 3 days", "signoff": "Kavya, one-click confirm"},
        {"case": "No-PO invoice > ₹1 lakh, or variance > 5%", "action": "Escalate", "signoff": "Kavya"},
        {"case": "No GRN (receipt not confirmed)", "action": "Hold & ask", "signoff": "AP manager"},
        {"case": "Invoice not in GSTR-2B", "action": "Pay base, hold GST", "signoff": "Kavya, one-click confirm"},
        {"case": "MSME supplier, invoice 30+ days old", "action": "Pay before day 45", "signoff": "Kavya, one-click confirm"},
        {"case": "Budget overrun ≤ 10% with reallocation", "action": "Approve with conditions", "signoff": "Kavya, one-click confirm"},
        {"case": "Budget overrun > 10%", "action": "Escalate", "signoff": "Kavya"},
        {"case": "Advance ≤ 30% to a supplier of 12+ months", "action": "Recommend approve", "signoff": "Kavya, one-click confirm"},
        {"case": "Advance > 30%, or supplier < 12 months", "action": "Escalate", "signoff": "Kavya"},
        {"case": "Anything above ₹5 lakh", "action": "Escalate", "signoff": "Kavya"},
        {"case": "Requester approving own request", "action": "Reject", "signoff": "N/A"},
    ],
}

ENTITIES = [
    {"id": "P-SOUNDWAVE", "name": "Soundwave AV Systems", "category": "audio-visual", "relationship_months": 20, "msme": True, "flags": []},
    {"id": "P-SPARKLE", "name": "Sparkle Facility Services", "category": "housekeeping", "relationship_months": 44, "msme": True, "flags": []},
    {"id": "P-BYTEFORGE", "name": "ByteForge Infotech", "category": "IT hardware", "relationship_months": 31, "msme": False, "flags": []},
    {"id": "P-COOLAIR", "name": "CoolAir HVAC Services", "category": "HVAC repair", "relationship_months": 27, "msme": True, "flags": []},
    {"id": "P-METRO", "name": "Metro Cabs Corporate", "category": "employee transport", "relationship_months": 38, "msme": False, "flags": []},
    {"id": "P-DESKCRAFT", "name": "DeskCraft Furniture", "category": "furniture", "relationship_months": 15, "msme": True, "flags": []},
    {"id": "P-PRINTEX", "name": "Printex Stationers", "category": "stationery", "relationship_months": 52, "msme": True, "flags": []},
    {"id": "P-CLOUDNINE", "name": "CloudNine Software", "category": "SaaS licences", "relationship_months": 9, "msme": False, "flags": []},
    {"id": "P-GREENLEAF", "name": "GreenLeaf Caterers", "category": "catering", "relationship_months": 36, "msme": True, "flags": []},
    {"id": "P-NETSURE", "name": "NetSure Security Systems", "category": "CCTV & access", "relationship_months": 41, "msme": False, "flags": []},
    {"id": "P-EMPLOYEE", "name": "Employee reimbursement", "category": "expenses", "relationship_months": 999, "msme": False, "flags": []},
    {"id": "P-OTHER", "name": "Other / new supplier", "category": "other", "relationship_months": 0, "msme": False, "flags": []},
]

DOCUMENTS = [
    {"id": "POL-AP-2026", "title": "Accounts-payable policy (FY 2026-27)",
     "clauses": [
         {"number": "2.1", "title": "No-PO invoices", "text": "Invoices without a purchase order may be paid up to ₹1,00,000 with a retro PO raised within 3 working days."},
         {"number": "2.4", "title": "Splitting", "text": "Splitting one requirement into several invoices or POs to stay under a limit is prohibited; invoices from the same supplier for the same work within 60 days are aggregated."},
         {"number": "4.2", "title": "Bank changes", "text": "Any change to supplier bank details must be confirmed by a phone call to the number on the supplier master before the next payment."},
         {"number": "5.1", "title": "MSME suppliers", "text": "MSME-registered suppliers are paid within 45 days of acceptance (MSMED Act s.15; Income-tax Act s.43B(h))."},
         {"number": "6.3", "title": "Year-end spend", "text": "Spend in the last month of the financial year above budget needs a business case showing use in the next quarter."}]},
    {"id": "INV-SOUNDWAVE-2291", "entity_id": "P-SOUNDWAVE", "title": "Soundwave AV — invoice 2291",
     "clauses": [
         {"number": "1", "title": "Description", "text": "Conference room AV upgrade, 4th floor — Phase 2 (displays and cabling)."},
         {"number": "2", "title": "Amount", "text": "₹96,000 plus GST at 18%."},
         {"number": "3", "title": "Reference", "text": "Phase 1 of the same upgrade was billed on invoice 2274 dated 12-Sep-2026 for ₹94,500."},
         {"number": "4", "title": "Bank", "text": "HDFC Bank, account as per supplier master."}]},
    {"id": "INV-SPARKLE-0815", "entity_id": "P-SPARKLE", "title": "Sparkle Facility Services — invoice 0815",
     "clauses": [
         {"number": "1", "title": "Description", "text": "Deep cleaning, floors 2–5, September 2026."},
         {"number": "2", "title": "Amount", "text": "₹42,800 plus GST, against PO 4471 for ₹41,500 (3.1% variance: extra consumables)."},
         {"number": "3", "title": "Bank", "text": "Please note our NEW bank account with effect from this invoice: Axis Bank, A/c ending 7781. Kindly update your records."}]},
]


def dec(i, date, typ, ent, amount, f, decision, note, outcome, status="good", conditions=(), lessons=(), mistake="",
        holdout=False, doc=None, by="AP manager – R. Menon"):
    e = next(x for x in ENTITIES if x["id"] == ent)
    return {"id": f"FC-{i:04d}", "date": date, "type": typ, "entity_id": ent, "entity_name": e["name"], "amount_inr": amount,
            "requested_by": by, **f, "decision": decision, "decision_note": note, "reasons": [note],
            "conditions": list(conditions), "document_id": doc, "outcome": outcome, "outcome_status": status,
            "mistake": bool(mistake), "mistake_note": mistake, "lesson_ids": list(lessons), "holdout": holdout}


def F(cc="facilities", grn=True, var=0.0, gst=True, receipt=True, msme=False, days=10, adv=0, self_=False):
    return {"cost_centre": cc, "grn_matched": grn, "variance_pct": var, "gst_in_2b": gst, "receipt_attached": receipt,
            "supplier_msme": msme, "days_since_invoice": days, "advance_pct": adv, "requester_is_approver": self_}


DECISIONS = [
    dec(1, "2024-05-08", "price_variance", "P-PRINTEX", 18400, F("admin", var=2.2, msme=True), "approved", "Stationery 2.2% over PO: freight.", "Paid; no issue."),
    dec(2, "2024-06-12", "invoice_without_po", "P-COOLAIR", 46000, F(msme=True), "approved_with_conditions", "Emergency compressor repair, no PO.", "Retro PO raised in 2 days.", conditions=["Retro PO within 3 working days"]),
    dec(3, "2024-07-03", "invoice_without_po", "P-SOUNDWAVE", 95000, F(msme=True), "approved_with_conditions",
        "Approved two no-PO invoices of ₹95,000 each for the same AV job, a week apart.", "Audit found the split; job was over-billed by ₹41,000.",
        "bad", conditions=["Retro PO"], mistake="Two invoices just under the limit are one invoice over it: aggregate the same supplier and job before applying the no-PO limit.", lessons=["FL01"]),
    dec(4, "2024-08-19", "price_variance", "P-GREENLEAF", 61200, F("admin", var=3.0, msme=True), "approved",
        "Catering invoice paid to new bank details sent by email with the invoice.", "Account belonged to a fraudster; ₹6.4 L lost across two payments, ₹1.1 L recovered.",
        "bad", mistake="Bank details change by phone call to the number on the supplier master, never by email or invoice note.", lessons=["FL02"]),
    dec(5, "2024-09-24", "expense_exception", "P-EMPLOYEE", 9200, F("sales"), "approved", "Client dinner slightly over per-diem; receipt attached.", "Paid."),
    dec(6, "2024-10-15", "budget_overrun", "P-BYTEFORGE", 380000, F("it", var=8.0), "approved_with_conditions", "Laptop refresh 8% over; funded from deferred server spend.", "Within year budget.", conditions=["Funding moved from a named cost line"]),
    dec(7, "2024-11-06", "invoice_without_po", "P-NETSURE", 240000, F("facilities"), "escalated", "CCTV upgrade billed without PO: ₹2.4 L.", "Kavya approved after a quote check."),
    dec(8, "2024-12-10", "price_variance", "P-METRO", 152000, F("delivery", var=12.5), "escalated", "Cab invoice 12.5% over PO: night-shift surcharge.", "Revised PO; surcharge renegotiated to 6%."),
    dec(9, "2025-01-14", "advance_payment", "P-DESKCRAFT", 210000, F("facilities", adv=25, msme=True), "approved",
        "25% advance to furniture supplier who said cash was tight this quarter.", "Supplier went insolvent; advance of ₹2.1 L lost.",
        "bad", mistake="An advance to a supplier signalling cash trouble is a loan we will not get back: escalate whatever the percentage.", lessons=["FL04"]),
    dec(10, "2025-02-04", "expense_exception", "P-EMPLOYEE", 6800, F("delivery", receipt=False), "asked", "Taxi claim without receipt.", "Receipt produced next day."),
    dec(11, "2025-03-18", "budget_overrun", "P-DESKCRAFT", 340000, F("facilities", var=7.0, msme=True), "approved_with_conditions",
        "Year-end overrun for ergonomic chairs 'before the budget lapses'.", "Chairs stayed boxed for 5 months; audit observation on March spending.",
        "bad", conditions=["Funding moved from a named cost line"], mistake="March spend to 'use the budget' needs a business case showing use next quarter.", lessons=["FL03"]),
    dec(12, "2025-04-09", "price_variance", "P-SPARKLE", 39800, F(var=4.1, gst=False, msme=True), "approved_with_conditions", "Small variance; invoice not yet in GSTR-2B.", "GST released after supplier filed.", conditions=["Hold GST until in GSTR-2B"]),
    dec(13, "2025-05-06", "invoice_without_po", "P-SOUNDWAVE", 88000, F(msme=True), "escalated",
        "Applied FL01: second Soundwave invoice for the same room within 30 days; aggregated to ₹1.79 L.", "Single PO raised; ₹22,000 duplicate cabling removed.", lessons=["FL01"]),
    dec(14, "2025-06-03", "price_variance", "P-PRINTEX", 22600, F("admin", var=1.8, msme=True), "asked",
        "Applied FL02: invoice carried new bank details; callback to master number.", "Supplier confirmed genuine change; paid next day.", lessons=["FL02"]),
    dec(15, "2025-06-25", "advance_payment", "P-METRO", 180000, F("delivery", adv=20), "approved", "20% advance for festive-season fleet; 3-year supplier.", "Delivered."),
    dec(16, "2025-07-15", "advance_payment", "P-CLOUDNINE", 450000, F("it", adv=40), "escalated", "40% upfront for SaaS licences; supplier 9 months old.", "Negotiated quarterly billing."),
    dec(17, "2025-08-05", "expense_exception", "P-EMPLOYEE", 12500, F("sales"), "approved", "Hotel over limit during a client visit to Singapore; receipt attached.", "Paid."),
    dec(18, "2025-08-27", "invoice_without_po", "P-COOLAIR", 72000, F(msme=True, days=34), "approved_with_conditions", "AC repair, MSME, invoice 34 days old.", "Paid on day 41.", conditions=["Retro PO", "Pay within 45 days"]),
    dec(19, "2025-09-16", "price_variance", "P-NETSURE", 47000, F(var=6.4), "escalated", "Variance 6.4% on access cards.", "Approved with revised PO."),
    dec(20, "2025-10-07", "expense_exception", "P-EMPLOYEE", 14200, F("sales", self_=True), "rejected", "Sales manager tried to approve own claim.", "Routed to his manager."),
    dec(21, "2025-10-29", "advance_payment", "P-GREENLEAF", 120000, F("admin", adv=20, msme=True), "escalated",
        "Applied FL04: caterer asked for 20% advance citing delayed client payments.", "Paid weekly in arrears instead; caterer stayed solvent.", lessons=["FL04"]),
    dec(22, "2025-11-18", "budget_overrun", "P-BYTEFORGE", 520000, F("it", var=14.0), "escalated", "Overrun 14% on network switches.", "Phased into next quarter."),
    dec(23, "2025-12-09", "price_variance", "P-METRO", 34000, F("delivery", var=3.5), "approved", "Cab variance 3.5%.", "Paid."),
    dec(24, "2026-01-13", "invoice_without_po", "P-PRINTEX", 28000, F("admin", msme=True), "approved_with_conditions", "Urgent printing, no PO.", "Retro PO raised.", conditions=["Retro PO within 3 working days"]),
    dec(25, "2026-02-03", "price_variance", "P-SPARKLE", 44000, F(var=2.9, grn=False, msme=True), "asked", "No GRN from facilities yet.", "GRN confirmed; paid."),
    dec(26, "2026-02-24", "budget_overrun", "P-DESKCRAFT", 260000, F("facilities", var=6.0, msme=True), "asked",
        "Applied FL03: March furniture overrun; asked for use plan.", "Plan showed a new floor opening in April; approved.", lessons=["FL03"]),
    dec(27, "2026-03-10", "expense_exception", "P-EMPLOYEE", 7400, F("delivery"), "approved", "Late-night meal over per-diem; receipt.", "Paid."),
    dec(28, "2026-03-31", "price_variance", "P-GREENLEAF", 26500, F("admin", var=4.8, msme=True, days=38), "approved_with_conditions", "MSME caterer, day 38.", "Paid on day 43.", conditions=["Pay within 45 days"]),
    dec(29, "2026-04-21", "invoice_without_po", "P-BYTEFORGE", 310000, F("it"), "escalated", "Emergency firewall licence, ₹3.1 L, no PO.", "Approved by Kavya; PO next day."),
    dec(30, "2026-05-12", "advance_payment", "P-NETSURE", 90000, F(adv=25), "approved", "25% advance, 41-month supplier.", "Delivered."),
    # ---- 15 holdouts ----
    dec(131, "2026-07-03", "price_variance", "P-PRINTEX", 21000, F("admin", var=3.0, msme=True), "approved", "Clean 3% variance.", "Paid.", holdout=True),
    dec(132, "2026-07-08", "invoice_without_po", "P-COOLAIR", 80000, F(msme=True), "approved_with_conditions", "₹80k no-PO repair.", "Retro PO.", conditions=["Retro PO"], holdout=True),
    dec(133, "2026-07-14", "invoice_without_po", "P-NETSURE", 240000, F(), "escalated", "₹2.4 L no-PO.", "Kavya approved.", holdout=True),
    dec(134, "2026-07-21", "price_variance", "P-METRO", 98000, F("delivery", var=14.0), "escalated", "14% variance.", "Revised PO.", holdout=True),
    dec(135, "2026-07-28", "price_variance", "P-SPARKLE", 36000, F(var=2.0, grn=False, msme=True), "asked", "No GRN.", "Paid after GRN.", holdout=True),
    dec(136, "2026-08-04", "expense_exception", "P-EMPLOYEE", 9000, F("sales"), "approved", "Expense with receipt.", "Paid.", holdout=True),
    dec(137, "2026-08-11", "expense_exception", "P-EMPLOYEE", 11000, F("delivery", receipt=False), "asked", "No receipt.", "Pending.", holdout=True),
    dec(138, "2026-08-18", "budget_overrun", "P-BYTEFORGE", 410000, F("it", var=18.0), "escalated", "Overrun 18%.", "Deferred.", holdout=True),
    dec(139, "2026-08-25", "expense_exception", "P-EMPLOYEE", 8000, F("sales", self_=True), "rejected", "Self-approval.", "Rejected.", holdout=True),
    dec(140, "2026-09-01", "price_variance", "P-GREENLEAF", 30000, F("admin", var=2.5, msme=True, days=38), "approved_with_conditions", "MSME day 38.", "Paid day 42.", conditions=["Pay within 45 days"], holdout=True),
    dec(141, "2026-09-08", "invoice_without_po", "P-SOUNDWAVE", 96000, F(msme=True), "escalated",
        "Second invoice for the same AV upgrade (Phase 1 ₹94,500 last month): aggregated ₹1.9 L (FL01).", "Single PO.", lessons=["FL01"], holdout=True),
    dec(142, "2026-09-11", "price_variance", "P-SPARKLE", 42800, F(var=3.1, msme=True), "asked",
        "Invoice carries new bank details: callback first (FL02).", "Callback revealed a spoofed email.", lessons=["FL02"], holdout=True),
    dec(143, "2026-09-16", "budget_overrun", "P-DESKCRAFT", 290000, F("facilities", var=7.0, msme=True), "asked",
        "March-style 'before it lapses' purchase: needs a use plan (FL03).", "No use plan; deferred.", lessons=["FL03"], holdout=True),
    dec(144, "2026-09-22", "advance_payment", "P-METRO", 150000, F("delivery", adv=20), "escalated",
        "20% advance, but supplier says drivers' salaries are delayed (FL04).", "Paid weekly instead.", lessons=["FL04"], holdout=True),
    dec(145, "2026-09-29", "invoice_without_po", "P-COOLAIR", 42000, F(msme=True), "approved_with_conditions",
        "URGENT server-room AC failure fixed overnight; rate card matches.", "Retro PO next morning.", conditions=["Retro PO"], holdout=True),
]

LESSONS = [
    {"id": "FL01", "title": "Aggregate split invoices", "rule": "Invoices from the same supplier for the same job within 60 days are added together before applying the ₹1 lakh no-PO limit.",
     "trigger": "No-PO invoice where the same supplier billed related work recently, or the invoice mentions a phase or part", "action_required": "Escalate on the aggregate amount; one PO for the whole job.", "source_decision_ids": ["FC-0003"]},
    {"id": "FL02", "title": "Bank changes by callback only", "rule": "Any new or changed bank details on an invoice or email are verified by a phone call to the number on the supplier master before paying.",
     "trigger": "Invoice or request mentions new, changed or updated bank details", "action_required": "Hold & ask: callback verification before payment.", "source_decision_ids": ["FC-0004"]},
    {"id": "FL03", "title": "No 'use it or lose it' spend", "rule": "Spend justified by the budget lapsing needs a business case showing use in the next quarter.",
     "trigger": "Overrun or purchase justified by year-end, budget lapse, or using up budget", "action_required": "Ask for the use plan before approving.", "source_decision_ids": ["FC-0011"]},
    {"id": "FL04", "title": "No advances to distressed suppliers", "rule": "If a supplier signals cash trouble (delayed salaries, cash crunch, client not paying), no advance regardless of percentage.",
     "trigger": "Advance or early payment where the supplier mentions cash flow difficulty", "action_required": "Escalate; offer pay-in-arrears or milestone payment instead.", "source_decision_ids": ["FC-0009"]},
]
for l in LESSONS:
    l.update({"version": 1, "status": "approved", "created": "2025-04-01", "approved_by": "Kavya Iyer", "half_life_days": 540})

REQ_FIELDS = ["id", "date", "type", "entity_id", "entity_name", "amount_inr", "requested_by", "document_id",
              "cost_centre", "grn_matched", "variance_pct", "gst_in_2b", "receipt_attached", "supplier_msme",
              "days_since_invoice", "advance_pct", "requester_is_approver"]

REQUESTS = [
    {"id": "REQ-F01", "date": "2026-10-04", "type": "price_variance", "entity_id": "P-PRINTEX", "entity_name": "Printex Stationers",
     "amount_inr": 19600, "requested_by": "AP manager – R. Menon", "document_id": None, **F("admin", var=2.4, msme=True, days=12),
     "description": "Stationery invoice ₹19,600 against PO ₹19,140: 2.4% over for courier charges. GRN done, invoice in GSTR-2B."},
    {"id": "REQ-F02", "date": "2026-10-04", "type": "invoice_without_po", "entity_id": "P-SOUNDWAVE", "entity_name": "Soundwave AV Systems",
     "amount_inr": 96000, "requested_by": "Facilities – G. Raman", "document_id": "INV-SOUNDWAVE-2291", **F(msme=True, days=8),
     "description": "AV work on the 4th-floor conference room is done and the team is happy. No PO was raised as it was urgent. ₹96,000 — under the ₹1 lakh no-PO limit, please pay."},
    {"id": "REQ-F03", "date": "2026-10-04", "type": "price_variance", "entity_id": "P-SPARKLE", "entity_name": "Sparkle Facility Services",
     "amount_inr": 42800, "requested_by": "AP manager – R. Menon", "document_id": "INV-SPARKLE-0815", **F(var=3.1, msme=True, days=14),
     "description": "Deep-cleaning invoice ₹42,800 vs PO ₹41,500 (3.1% for extra consumables). GRN done. Routine — please release."},
]

BACKTEST_TEXT = {
    "FC-0131": "Printex stationery invoice 3% over PO for freight; GRN done.",
    "FC-0132": "CoolAir repaired a pantry AC; ₹80,000 invoice, no PO raised; GRN done.",
    "FC-0133": "NetSure CCTV upgrade invoiced at ₹2.4 lakh without a PO.",
    "FC-0134": "Metro Cabs invoice is 14% over the PO due to night-shift surcharges.",
    "FC-0135": "Sparkle invoice 2% over PO; facilities has not confirmed the GRN yet.",
    "FC-0136": "Client dinner ₹9,000, slightly over per-diem; receipt attached.",
    "FC-0137": "Taxi and meals claim ₹11,000; receipts lost.",
    "FC-0138": "IT network-switch spend will run 18% over the cost-centre budget.",
    "FC-0139": "Sales manager submitting his own ₹8,000 expense claim for his own approval.",
    "FC-0140": "GreenLeaf (MSME) catering invoice 2.5% over PO; accepted 38 days ago.",
    "FC-0141": "Soundwave AV invoice ₹96,000, no PO, for the 4th-floor conference room upgrade (Phase 2). Under the ₹1 lakh no-PO limit.",
    "FC-0142": "Sparkle cleaning invoice 3.1% over PO; GRN done. The invoice says their bank account has changed and gives the new details.",
    "FC-0143": "Facilities wants ergonomic chairs now, 7% over budget, 'so the remaining budget doesn't lapse at year-end'; funding from the pantry line.",
    "FC-0144": "Metro Cabs asks for a 20% advance for the festive fleet. They mention their drivers' salaries were delayed last month.",
    "FC-0145": "URGENT: server-room AC failed overnight; CoolAir fixed it by 6 am. ₹42,000, no PO, rate card matches, GRN done.",
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
    print(f"spend: {len(DECISIONS) - len(holdouts)} in memory ({sum(d['mistake'] for d in DECISIONS)} mistakes), {len(holdouts)} holdouts, "
          f"{len(LESSONS)} lessons, {len(MANDATE['rules'])} rules, {len(REQUESTS)} demo requests")


if __name__ == "__main__":
    main()
