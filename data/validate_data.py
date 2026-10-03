"""
Validation script for Pratibimb mock data.
Tests that all JSON files parse correctly and conform to schema and referential integrity.
"""
import json
import sys
from pathlib import Path

def validate():
    data_dir = Path(__file__).parent
    files = [
        "senior.json",
        "mandate.json",
        "vendors.json",
        "contracts.json",
        "decisions.json",
        "lessons.json",
        "requests.json",
        "backtest.json",
    ]
    
    results = {}
    errors = []
    
    # 1. Test JSON parsing for each file
    parsed = {}
    for filename in files:
        filepath = data_dir / filename
        if not filepath.exists():
            errors.append(f"Missing file: {filename}")
            results[filename] = "MISSING"
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = json.load(f)
                parsed[filename] = content
                results[filename] = "VALID_JSON"
        except Exception as e:
            errors.append(f"JSON syntax error in {filename}: {e}")
            results[filename] = f"ERROR: {e}"
            
    if errors:
        print("FAIL: JSON parsing errors detected:")
        for err in errors:
            print("  -", err)
        return False, results, errors

    # 2. Schema and count checks
    # Senior
    senior = parsed.get("senior.json", {})
    assert senior.get("id") == "SEN-001", "Invalid senior ID"
    assert senior.get("signature_limit_inr") == 500000, "Expected signature limit 500,000"

    # Mandate
    mandate = parsed.get("mandate.json", {})
    rules = mandate.get("rules", [])
    assert len(rules) >= 10, f"Expected at least 10 mandate rules, got {len(rules)}"

    # Vendors
    vendors = parsed.get("vendors.json", {}).get("vendors", [])
    vendor_ids = {v["id"] for v in vendors}
    assert "V-KESTREL" in vendor_ids, "Missing V-KESTREL"
    assert "V-BRIGHTLINE" in vendor_ids, "Missing V-BRIGHTLINE"
    assert "V-PRINTPRO" in vendor_ids, "Missing V-PRINTPRO"
    assert "V-PARLO" in vendor_ids, "Missing V-PARLO"

    # Contracts
    contracts = parsed.get("contracts.json", {}).get("contracts", [])
    assert len(contracts) >= 3, f"Expected at least 3 contracts, got {len(contracts)}"
    kestrel = next((c for c in contracts if c["vendor_id"] == "V-KESTREL"), None)
    assert kestrel is not None, "Missing Kestrel contract"
    clause_9_2 = next((cl for cl in kestrel["clauses"] if cl["number"] == "9.2"), None)
    assert clause_9_2 is not None, "Missing Kestrel clause 9.2"
    assert "24" in clause_9_2["text"] or "twenty-four" in clause_9_2["text"].lower(), "Clause 9.2 should specify 24 months auto-renewal"

    # Decisions
    decisions = parsed.get("decisions.json", {}).get("decisions", [])
    assert len(decisions) == 40, f"Expected exactly 40 decisions, got {len(decisions)}"
    mistakes = [d for d in decisions if d.get("mistake")]
    assert len(mistakes) == 4, f"Expected exactly 4 mistakes, got {len(mistakes)}"
    holdouts = [d for d in decisions if d.get("holdout")]
    assert len(holdouts) == 10, f"Expected exactly 10 holdouts, got {len(holdouts)}"

    # Lessons
    lessons = parsed.get("lessons.json", {}).get("lessons", [])
    assert len(lessons) == 6, f"Expected exactly 6 lessons, got {len(lessons)}"
    lesson_ids = {l["id"] for l in lessons}
    expected_lessons = {"L01", "L02", "L03", "L04", "L05", "L06"}
    assert lesson_ids == expected_lessons, f"Lessons set mismatch: {lesson_ids}"

    # Requests
    requests = parsed.get("requests.json", {}).get("requests", [])
    assert len(requests) == 3, f"Expected exactly 3 demo requests, got {len(requests)}"
    req_ids = [r["id"] for r in requests]
    assert req_ids == ["REQ-001", "REQ-002", "REQ-003"], f"Unexpected request IDs: {req_ids}"

    # Backtest
    backtest = parsed.get("backtest.json", {}).get("backtest_cases", [])
    assert len(backtest) == 10, f"Expected exactly 10 backtest cases, got {len(backtest)}"
    holdout_ids = [d["id"] for d in holdouts]
    backtest_ids = [b["decision_id"] for b in backtest]
    assert backtest_ids == holdout_ids, f"Backtest case IDs do not match holdout decision IDs"

    print("ALL MOCK DATA VALIDATION CHECKS PASSED SUCCESSFULLY!")
    print(f"  - Validated {len(files)} JSON files cleanly.")
    print(f"  - 40 decisions confirmed (30 active precedents, 10 holdouts, 4 historical mistakes).")
    print(f"  - 6 lessons confirmed (L01-L06).")
    print(f"  - 3 contracts confirmed (including Kestrel clause 9.2).")
    print(f"  - 3 live demo requests confirmed.")
    print(f"  - 10 holdout backtest cases verified against holdouts.")
    return True, results, []

if __name__ == "__main__":
    success, res, errs = validate()
    if not success:
        sys.exit(1)
