"""
eval/scorer.py

Runs app/eval/test_cases.json against the hybrid intent detector and scores
each case on three independent dimensions instead of one strict/partial
number:

  1. intent_match   - did it call the right tool(s), and ALL of them
  2. param_match    - are the extracted parameters correct (no missing
                       required params, no placeholder junk like "unknown")
  3. behavior_match - did it correctly EXECUTE vs correctly DECLINE

A case only counts as a full pass if all three dimensions pass. This
replaces the old run_test_cases.py approach of eyeballing a single
accuracy % across runs.

Usage:
    python -m eval.scorer
    python -m eval.scorer --cases app/eval/test_cases.json --out eval/runs/
    python -m eval.scorer --tag post-langgraph-migration
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------
# Wire this up to your actual detector.
#
# Your hybrid detector lives in app/intent/hybrid.py. This tries a couple of
# common call shapes; adjust `call_detector` below to match your real
# function signature and return shape if it doesn't line up.
# --------------------------------------------------------------------------
try:
    from app.intent.hybrid import detect_intent_hybrid
except ImportError:
    detect_intent_hybrid = None


PLACEHOLDER_VALUES = {"unknown", "n/a", "none", "null", "tbd", ""}
DEFAULT_PATIENT_ID = "p1"


def call_detector(input_text: str):
    """
    Calls detect_intent_hybrid() for a single input and normalizes the
    result to a common shape:

        {
            "intents": ["book_appointment", ...],   # [] if it declined
            "parameters": {...},
        }

    Based on app/intent/hybrid.py's actual return shape:
      - single intent:  {"matched": True, "intent": "...", "parameters": {...}}
      - multi-intent:   {"all_intents": [...], "parameters": {...}} (via the LLM path)
      - decline:        matched is falsy / no intent present
    """
    if detect_intent_hybrid is None:
        raise RuntimeError(
            "Could not import detect_intent_hybrid from app.intent.hybrid. "
            "Run this from your project root."
        )

    result = detect_intent_hybrid(input_text, patient_id=DEFAULT_PATIENT_ID)

    all_intents = result.get("all_intents")
    parameters = dict(result.get("parameters", {}) or {})

    if all_intents:
        intents = []
        for entry in all_intents:
            if isinstance(entry, dict):
                # each entry looks like {"intent": "...", "parameters": {...}}
                name = entry.get("intent") or entry.get("name")
                if name:
                    intents.append(name)
                parameters.update(entry.get("parameters", {}) or {})
            else:
                # plain string intent name
                intents.append(entry)
    elif result.get("matched") and result.get("intent"):
        intents = [result["intent"]]
    else:
        intents = []

    return {"intents": intents, "parameters": parameters}


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------

def score_intents(expected_intents, actual_intents) -> bool:
    """Order-independent set match. [] == [] counts as a correct decline."""
    return set(expected_intents) == set(actual_intents)


def score_behavior(expected_behavior, expected_intents, actual_intents) -> bool:
    """
    execute        -> exactly one intent, and it must be present
    execute_multi  -> two or more intents, all present
    decline        -> no intents fired
    """
    fired = len(actual_intents) > 0

    if expected_behavior == "decline":
        return not fired
    if expected_behavior in ("execute", "execute_multi"):
        return fired and score_intents(expected_intents, actual_intents)
    return False


def score_parameters(expected_parameters: dict, actual_parameters: dict) -> bool:
    """
    Checks that every expected key is present with a non-placeholder value.
    Does NOT fail on extra keys the detector filled in beyond what's
    expected - only missing/placeholder values on the ones we care about.
    """
    if not expected_parameters:
        return True

    for key, expected_value in expected_parameters.items():
        actual_value = actual_parameters.get(key)

        if actual_value is None:
            return False
        if isinstance(actual_value, str) and actual_value.strip().lower() in PLACEHOLDER_VALUES:
            return False

        # "tomorrow" etc. are relative dates - your date_utils.normalize_date()
        # resolves these, so we don't do a strict string match on dates,
        # just require *something* non-placeholder got filled in.
        if key == "date":
            continue

        if str(actual_value).strip().lower() != str(expected_value).strip().lower():
            return False

    return True


def run_case(case: dict) -> dict:
    start = time.perf_counter()
    error = None
    actual = {"intents": [], "parameters": {}}

    try:
        actual = call_detector(case["input"])
    except Exception as exc:  # noqa: BLE001 - we want to record any failure
        error = str(exc)

    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

    intent_pass = score_intents(case["expected_intents"], actual["intents"])
    behavior_pass = score_behavior(
        case["expected_behavior"], case["expected_intents"], actual["intents"]
    )
    param_pass = score_parameters(case.get("expected_parameters", {}), actual["parameters"])

    overall_pass = intent_pass and behavior_pass and param_pass and error is None

    return {
        "id": case["id"],
        "category": case["category"],
        "input": case["input"],
        "expected_intents": case["expected_intents"],
        "actual_intents": actual["intents"],
        "expected_parameters": case.get("expected_parameters", {}),
        "actual_parameters": actual["parameters"],
        "intent_pass": intent_pass,
        "behavior_pass": behavior_pass,
        "param_pass": param_pass,
        "pass": overall_pass,
        "elapsed_ms": elapsed_ms,
        "error": error,
        "notes": case.get("notes", ""),
    }


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def summarize(results: list[dict]) -> dict:
    total = len(results)
    passed = sum(r["pass"] for r in results)

    by_category = {}
    for r in results:
        cat = r["category"]
        bucket = by_category.setdefault(cat, {"total": 0, "passed": 0})
        bucket["total"] += 1
        bucket["passed"] += int(r["pass"])

    by_dimension = {
        "intent_match": sum(r["intent_pass"] for r in results),
        "behavior_match": sum(r["behavior_pass"] for r in results),
        "param_match": sum(r["param_pass"] for r in results),
    }

    return {
        "total": total,
        "passed": passed,
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "by_category": {
            cat: {
                "passed": v["passed"],
                "total": v["total"],
                "pass_rate": round(v["passed"] / v["total"], 4),
            }
            for cat, v in by_category.items()
        },
        "by_dimension": by_dimension,
    }


def print_report(summary: dict, results: list[dict]) -> None:
    print(f"\n{'='*60}")
    print(f"EVAL RESULTS: {summary['passed']}/{summary['total']} passed "
          f"({summary['pass_rate']*100:.1f}%)")
    print(f"{'='*60}\n")

    print("By category:")
    for cat, stats in summary["by_category"].items():
        print(f"  {cat:<18} {stats['passed']}/{stats['total']}  "
              f"({stats['pass_rate']*100:.0f}%)")

    print("\nBy dimension (out of total cases):")
    for dim, count in summary["by_dimension"].items():
        print(f"  {dim:<16} {count}/{summary['total']}")

    failures = [r for r in results if not r["pass"]]
    if failures:
        print(f"\nFailures ({len(failures)}):")
        for r in failures:
            reasons = []
            if not r["intent_pass"]:
                reasons.append(f"intent: expected {r['expected_intents']}, got {r['actual_intents']}")
            if not r["behavior_pass"]:
                reasons.append("behavior mismatch")
            if not r["param_pass"]:
                reasons.append(f"params: expected {r['expected_parameters']}, got {r['actual_parameters']}")
            if r["error"]:
                reasons.append(f"error: {r['error']}")
            print(f"  [{r['id']}] \"{r['input']}\"")
            for reason in reasons:
                print(f"      - {reason}")
    print()


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Run the intent-detection eval suite.")
    parser.add_argument("--cases", default="app/eval/test_cases.json",
                         help="Path to the test cases JSON file.")
    parser.add_argument("--out", default="eval/runs",
                         help="Directory to write the timestamped run report to.")
    parser.add_argument("--tag", default="",
                         help="Optional label for this run (e.g. a git commit or 'post-langgraph-migration'), stored in the report for regression tracking.")
    args = parser.parse_args()

    cases_path = Path(args.cases)
    if not cases_path.exists():
        print(f"Could not find test cases at {cases_path}", file=sys.stderr)
        sys.exit(1)

    cases = json.loads(cases_path.read_text())
    results = [run_case(case) for case in cases]
    summary = summarize(results)

    print_report(summary, results)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = out_dir / f"run_{timestamp}.json"
    report_path.write_text(json.dumps({
        "timestamp": timestamp,
        "tag": args.tag,
        "summary": summary,
        "results": results,
    }, indent=2))

    print(f"Report saved to {report_path}")


if __name__ == "__main__":
    main()