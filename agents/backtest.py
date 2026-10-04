"""
Back-test harness for Pratibimb.

Replays each senior's 15 held-out decisions (DEC-, SL-, FC-0131..0145) as fresh requests and compares the engine's verdict
with hers. Holdouts are never in the engine's memory.

Blind by construction:
  - each request is built from the request-side fields of the decision record plus the requester's own
    description (backtest.json → request_description). Meera's decision note, conditions, outcome and the
    grading notes never reach the engine;
  - it runs on a copy of data/ with an empty store: the baseline lessons (L01-L06) and no demo overrides, so a
    learning-loop demo can't leak into the score.

Two modes, the same pipeline:
  rules   — PRATIBIMB_LLM=off: the delegation-of-authority mandate alone (the baseline)
  gemini  — the full agent pipeline (Precedent, Challenger, Interviewer, Decider on Gemini)

Usage:  python -m agents.backtest [--mode rules|gemini|both]
Results of a full run go to data/backtest_results.json (the API serves that file; it never re-runs on a page load).
Single-mode runs go to data/backtest_results_<mode>.json (gitignored).
"""
import argparse
import datetime as dt
import json
import os
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List

from agents import llm
from agents.store import FileStore

DATA_DIR = Path(__file__).parent.parent / "data"
RESULTS_PATH = DATA_DIR / "backtest_results.json"


def pack_dir(pack: str = "vendor") -> Path:
    return DATA_DIR if pack == "vendor" else DATA_DIR / "packs" / pack


def results_path(pack: str = "vendor") -> Path:
    return pack_dir(pack) / "backtest_results.json"

# Request-side fields only. Never decision, decision_note, reasons, conditions, outcome, lesson_ids, ...
REQUEST_KEYS = ["date", "type", "vendor_id", "vendor_name", "value_inr", "term_months", "sla_breaches_12m",
                "handles_client_data", "advance_pct", "price_increase_pct", "contract_id", "requested_by"]

# Ask and escalate both withhold approval until someone acts; scored as the same call in the lenient score.
HOLD = {"ask", "escalate"}


def build_request(decision: Dict[str, Any], case: Dict[str, Any], keys: List[str] = None) -> Dict[str, Any]:
    req = {k: decision[k] for k in (keys or REQUEST_KEYS) if decision.get(k) is not None}
    req["id"] = "BT-" + decision["id"].split("-")[1]
    req["description"] = case["request_description"]
    return req


def _sandbox(src: Path = DATA_DIR) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="pratibimb-bt-"))
    for f in src.glob("*.json"):
        if not f.name.startswith("backtest_results"):
            shutil.copy(f, tmp / f.name)
    return tmp


def _score(rows: List[Dict[str, Any]], mode: str) -> Dict[str, Any]:
    def agg(subset):
        exact = sum(r[mode]["verdict"] == r["expected"] for r in subset)
        lenient = sum(r[mode]["verdict"] == r["expected"] or {r[mode]["verdict"], r["expected"]} <= HOLD for r in subset)
        return {"cases": len(subset), "exact": exact, "lenient": lenient}

    hard = [r for r in rows if r["set"] == "hard"]
    return {
        "all": agg(rows),
        "original_10": agg([r for r in rows if r["set"] == "original"]),
        "hard_5": agg(hard),
        # Meera did not approve as-is, the engine did: the expensive kind of miss.
        "unsafe_approvals": [r["decision_id"] for r in rows if r[mode]["verdict"] == "approve" and r["expected"] != "approve"],
        # Meera approved as-is, the engine held it back: the annoying kind of miss.
        "over_cautious": [r["decision_id"] for r in rows if r["expected"] == "approve" and r[mode]["verdict"] != "approve"],
        "citation_recall": round(
            sum(len(set(r["expected_citations"]) & set(r[mode]["citations"])) for r in rows)
            / max(1, sum(len(r["expected_citations"]) for r in rows)), 2),
    }


def run_backtest(modes=("rules", "gemini"), verbose: bool = True, pack: str = "vendor") -> Dict[str, Any]:
    from agents.domain import make_domain
    from agents.engine import PratibimbEngine  # after env is set per mode

    src = pack_dir(pack)
    keys = make_domain(pack, src).request_keys
    decisions = {d["id"]: d for d in json.loads((src / "decisions.json").read_text(encoding="utf-8"))["decisions"]}
    cases = json.loads((src / "backtest.json").read_text(encoding="utf-8"))["backtest_cases"]
    rows = [{
        "decision_id": c["decision_id"],
        "vendor_name": decisions[c["decision_id"]].get("vendor_name") or decisions[c["decision_id"]].get("entity_name"),
        "set": "hard" if int(c["decision_id"].split("-")[1]) >= 141 else "original",
        "request": build_request(decisions[c["decision_id"]], c, keys),
        "expected": c["expected_verdict"], "expected_citations": c.get("expected_citations", []), "why": c.get("why", ""),
        "meera_note": decisions[c["decision_id"]]["decision_note"],
    } for c in cases]

    sandbox = _sandbox(src)
    before = llm.cost_report()
    prev_flag = os.environ.get("PRATIBIMB_LLM")
    try:
        for mode in modes:
            os.environ["PRATIBIMB_LLM"] = "off" if mode == "rules" else "on"
            engine = PratibimbEngine(data_dir=sandbox, store=FileStore(sandbox / "state"), pack=pack)  # baseline lessons, no overrides
            with ThreadPoolExecutor(max_workers=1 if mode == "rules" else 4) as pool:
                verdicts = list(pool.map(lambda r: engine.decide(r["request"]), rows))
            for r, v in zip(rows, verdicts):
                r[mode] = {"verdict": v.verdict, "headline": v.headline, "citations": v.citations,
                           "lessons_applied": v.lessons_applied, "reasoning": v.reasoning, "engine": v.engine}
    finally:
        if prev_flag is None:
            os.environ.pop("PRATIBIMB_LLM", None)
        else:
            os.environ["PRATIBIMB_LLM"] = prev_flag
        shutil.rmtree(sandbox, ignore_errors=True)
    after = llm.cost_report()

    run_cost_usd = round(after["cost_usd"] - before["cost_usd"], 4)
    result = {
        "run_at": dt.datetime.now().isoformat(timespec="seconds"),
        "pack": pack,
        "model": llm.MODEL,
        "modes": list(modes),
        "scores": {m: _score(rows, m) for m in modes},
        "cost": {"live_calls": after["live_calls"] - before["live_calls"],
                 "cached_calls": after["cached_calls"] - before["cached_calls"],
                 "usd": run_cost_usd, "inr": round(run_cost_usd * 88, 2)},
        "cases": rows,
    }
    # Only a full rules-vs-Gemini run replaces the file the UI shows; single-mode runs go to their own file.
    out = results_path(pack) if set(modes) == {"rules", "gemini"} else src / f"backtest_results_{modes[0]}.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    if verbose:
        _print(result)
    return result


def load_results(pack: str = "vendor") -> Dict[str, Any]:
    path = results_path(pack)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _print(res: Dict[str, Any]) -> None:
    modes = res["modes"]
    print("=" * 96)
    print(f"PRATIBIMB BACK-TEST · {len(res['cases'])} held-out decisions · pack {res.get('pack', 'vendor')} · model {res['model']}")
    print("=" * 96)
    print(f"{'case':9} {'vendor':24} {'Meera':24} " + " ".join(f"{m:24}" for m in modes))
    for r in res["cases"]:
        cells = []
        for m in modes:
            v = r[m]["verdict"]
            mark = "ok" if v == r["expected"] else ("~" if {v, r["expected"]} <= HOLD else "XX")
            cells.append(f"{v + ' ' + mark:24}")
        print(f"{r['decision_id']:9} {r['vendor_name'][:23]:24} {r['expected']:24} " + " ".join(cells))
    print("-" * 96)
    for m in modes:
        s = res["scores"][m]
        print(f"{m:7} all {s['all']['exact']}/{s['all']['cases']} exact, {s['all']['lenient']}/{s['all']['cases']} with ask≈escalate"
              f" · original {s['original_10']['lenient']}/10 · hard {s['hard_5']['lenient']}/5"
              f" · unsafe approvals {len(s['unsafe_approvals'])} · over-cautious {len(s['over_cautious'])}"
              f" · citation recall {s['citation_recall']:.0%}")
    c = res["cost"]
    print(f"cost: {c['live_calls']} live calls, {c['cached_calls']} cached · USD {c['usd']} ≈ ₹{c['inr']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["rules", "gemini", "both"], default="both")
    ap.add_argument("--pack", choices=["vendor", "leads", "spend", "all"], default="vendor")
    args = ap.parse_args()
    modes = ("rules", "gemini") if args.mode == "both" else (args.mode,)
    for pk in (["vendor", "leads", "spend"] if args.pack == "all" else [args.pack]):
        res = run_backtest(modes, pack=pk)
    sys.exit(0)
