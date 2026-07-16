"""
Live eval runner for the CSUCI Student Success Navigator.

Runs every golden_set.json case through the REAL stack (handler → Bedrock
Retrieve → Claude tool-use) and scores the model's routing decisions against
the human-written answer key. This is an exact-match scorecard, not an
LLM-as-a-judge: outcomes are categorical (answer / clarify / escalate /
decline / crisis), so equality against the label is the whole grade.

Usage (needs live AWS credentials + the Bedrock KB):
    python eval/run_eval.py            # full run + confusion matrix
    python eval/run_eval.py A20 U4     # only specific case ids

Output: per-case verdicts, outcome accuracy, routing accuracy (on needs_human
rows), a confusion matrix, and a JSON dump to eval/baseline_results.json.
This is a manual/opt-in tool — deliberately NOT part of the pytest suite.
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "lambda"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "lambda", "orchestrator"))

GOLDEN_SET_PATH = os.path.join(PROJECT_ROOT, "eval", "golden_set.json")
RESULTS_PATH = os.path.join(PROJECT_ROOT, "eval", "baseline_results.json")

# Golden-set taxonomy → expected response type
EXPECTED_TYPE = {
    "answerable": "answer",
    "ambiguous": "clarify",
    "needs_human": "escalate",
    "out_of_scope": "decline",
    "crisis": "crisis",
}

OUTCOMES = ["answer", "clarify", "escalate", "decline", "crisis", "error"]


def load_env() -> None:
    """Load .env so MODEL_ID / BEDROCK_KB_ID are set before handler import."""
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())


def run_case(lambda_handler, case: dict) -> dict:
    """Run one golden case through the live handler and score it."""
    event = {
        "httpMethod": "POST",
        "body": json.dumps(
            {"message": case["query"], "history": [], "sessionId": f"eval-{case['id']}"}
        ),
    }
    try:
        response = lambda_handler(event, None)
        body = json.loads(response["body"])
        actual_type = body.get("type", "error") if response["statusCode"] == 200 else "error"
    except Exception as exc:  # noqa: BLE001 — an eval must never die mid-run
        body = {"error": str(exc)}
        actual_type = "error"

    expected_type = EXPECTED_TYPE[case["type"]]
    type_ok = actual_type == expected_type

    # Routing accuracy: which office, when a handoff was expected.
    expected_office = case.get("expected_office")
    office_expected = case["type"] == "needs_human" or case.get("expect_escalation")
    actual_office = (body.get("escalation") or {}).get("office")
    office_ok = None
    if office_expected and expected_office:
        office_ok = actual_office == expected_office

    # Pair check: answerable rows flagged expect_escalation must carry the card.
    escalation_ok = None
    if case.get("expect_escalation"):
        escalation_ok = body.get("escalation") is not None

    return {
        "id": case["id"],
        "topic": case["topic"],
        "query": case["query"],
        "expected_type": expected_type,
        "actual_type": actual_type,
        "type_ok": type_ok,
        "expected_office": expected_office if office_expected else None,
        "actual_office": actual_office,
        "office_ok": office_ok,
        "escalation_ok": escalation_ok,
        "message_preview": (body.get("message") or "")[:160],
    }


def main() -> None:
    load_env()
    from handler import lambda_handler  # imported after env is ready

    with open(GOLDEN_SET_PATH) as f:
        golden = json.load(f)

    only_ids = set(sys.argv[1:])
    if only_ids:
        golden = [c for c in golden if c["id"] in only_ids]

    results = []
    for i, case in enumerate(golden, 1):
        print(f"[{i}/{len(golden)}] {case['id']}: {case['query'][:70]}...", flush=True)
        result = run_case(lambda_handler, case)
        status = "PASS" if result["type_ok"] else "FAIL"
        office_note = ""
        if result["office_ok"] is not None:
            office_note = f" | office {'OK' if result['office_ok'] else 'WRONG'} ({result['actual_office']})"
        print(f"     -> {status}: expected {result['expected_type']}, got {result['actual_type']}{office_note}")
        results.append(result)

    # ---- Scorecard ----
    scored = [r for r in results]
    type_hits = sum(1 for r in scored if r["type_ok"])
    office_rows = [r for r in scored if r["office_ok"] is not None]
    office_hits = sum(1 for r in office_rows if r["office_ok"])
    pair_rows = [r for r in scored if r["escalation_ok"] is not None]
    pair_hits = sum(1 for r in pair_rows if r["escalation_ok"])

    print("\n" + "=" * 68)
    print(f"Outcome accuracy : {type_hits}/{len(scored)} "
          f"({100 * type_hits / len(scored):.0f}%)")
    if office_rows:
        print(f"Routing accuracy : {office_hits}/{len(office_rows)} "
              f"({100 * office_hits / len(office_rows):.0f}%)  (needs_human rows)")
    if pair_rows:
        print(f"Pair behavior    : {pair_hits}/{len(pair_rows)} answerable+human rows carried an escalation card")

    # ---- Confusion matrix (rows=expected, cols=actual) ----
    matrix = defaultdict(lambda: defaultdict(int))
    for r in scored:
        matrix[r["expected_type"]][r["actual_type"]] += 1

    col_names = [o for o in OUTCOMES if any(matrix[e].get(o) for e in matrix) or o in matrix]
    print("\nConfusion matrix (rows = expected, cols = actual):")
    header = "            " + "".join(f"{c:>10}" for c in col_names)
    print(header)
    for expected in OUTCOMES:
        if expected not in matrix:
            continue
        row = "".join(f"{matrix[expected].get(c, 0):>10}" for c in col_names)
        print(f"{expected:>12}{row}")

    failures = [r for r in scored if not r["type_ok"] or r["office_ok"] is False]
    if failures:
        print("\nFailures:")
        for r in failures:
            print(f"  {r['id']}: expected {r['expected_type']}"
                  f"{'/' + r['expected_office'] if r['expected_office'] else ''}, "
                  f"got {r['actual_type']}"
                  f"{'/' + str(r['actual_office']) if r['actual_office'] else ''}")
            print(f"       msg: {r['message_preview']}")

    with open(RESULTS_PATH, "w") as f:
        json.dump(
            {
                "run_at": datetime.now(timezone.utc).isoformat(),
                "model_id": os.environ.get("MODEL_ID", ""),
                "outcome_accuracy": f"{type_hits}/{len(scored)}",
                "routing_accuracy": f"{office_hits}/{len(office_rows)}" if office_rows else None,
                "results": results,
            },
            f,
            indent=2,
        )
    print(f"\nResults written to {os.path.relpath(RESULTS_PATH, PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
