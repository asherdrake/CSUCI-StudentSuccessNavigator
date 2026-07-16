"""
Faithfulness (groundedness) eval for the CSUCI Student Success Navigator.

Where run_eval.py grades the model's ROUTING decision (answer / clarify /
escalate / decline / crisis) against the single-turn-case label, this grades the
*truthfulness of the answer prose itself*: for every case the model actually
answers, it checks whether each factual claim is backed by the passages the
retriever returned. It catches hallucination that the routing scorecard can't
see — a perfectly-routed "answer" that invents a deadline, phone number, or URL.

How it works:
  1. Run each answerable single-turn case through the REAL handler with DEBUG_CHUNKS
     on, so we capture the exact answer, citations, and retrieved passages a
     student would have gotten.
  2. Hand (question, answer, passages) to an LLM judge (faithfulness_judge.py),
     which extracts atomic claims and labels each supported/unsupported/
     contradicted against the passages ONLY.
  3. Aggregate: per-answer faithfulness = supported / total claims; corpus
     faithfulness = supported / total claims across all answers; plus a count
     of contradictions (the worst failures) and every unsupported claim.

Usage (needs live AWS credentials + the Bedrock KB, same as run_eval.py):
    python eval/run_faithfulness.py            # all answerable cases
    python eval/run_faithfulness.py A3 A6 P1   # only specific case ids

Judge model override:  set JUDGE_MODEL_ID (default us.anthropic.claude-sonnet-5).
This is a manual/opt-in tool — deliberately NOT part of the pytest suite.
Output: per-case verdicts + a JSON dump to eval/results/faithfulness_results.json.
"""

import json
import os
import sys
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "lambda"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "lambda", "orchestrator"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CASES_PATH = os.path.join(PROJECT_ROOT, "eval", "single_turn_cases.json")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "eval", "results")
RESULTS_PATH = os.path.join(RESULTS_DIR, "faithfulness_results.json")

# Answer bodies for answered cases are split on this separator: the escalation
# addendum after it is code-owned boilerplate, not model-authored prose, so we
# judge only the part before it.
_ESCALATION_SEP = "\n\n---\n\n"


def load_env() -> None:
    """Load .env, and force DEBUG_CHUNKS on so responses carry retrieved_chunks."""
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())
    # The judge needs the passages the model saw; DEBUG_CHUNKS surfaces them.
    os.environ["DEBUG_CHUNKS"] = "1"


def _run_handler(lambda_handler, case: dict) -> dict:
    """Run one case through the live handler; return the parsed 200 body."""
    event = {
        "httpMethod": "POST",
        "body": json.dumps(
            {"message": case["query"], "history": [], "sessionId": f"faith-{case['id']}"}
        ),
    }
    response = lambda_handler(event, None)
    return json.loads(response["body"])


def main() -> None:
    load_env()
    from handler import lambda_handler  # after env is ready
    from faithfulness_judge import judge_answer

    with open(CASES_PATH) as f:
        all_cases = json.load(f)

    only_ids = set(sys.argv[1:])
    # Only cases the answer key expects to be answered can be judged for
    # groundedness; the rest have no answer prose to audit.
    cases = [c for c in all_cases if c.get("type") == "answerable"]
    if only_ids:
        cases = [c for c in cases if c["id"] in only_ids]

    results = []
    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {case['id']}: {case['query'][:65]}...", flush=True)
        record = {"id": case["id"], "topic": case["topic"], "query": case["query"]}

        try:
            body = _run_handler(lambda_handler, case)
        except Exception as exc:  # noqa: BLE001
            print(f"     -> ERROR running handler: {exc}")
            record["skipped"] = f"handler error: {exc}"
            results.append(record)
            continue

        actual_type = body.get("type")
        if actual_type != "answer":
            # Didn't answer (clarified/escalated/declined) — nothing to audit.
            print(f"     -> SKIP: model returned '{actual_type}', not an answer")
            record["skipped"] = f"non-answer type: {actual_type}"
            record["actual_type"] = actual_type
            results.append(record)
            continue

        message = body.get("message") or ""
        answer_text = message.split(_ESCALATION_SEP, 1)[0].strip()
        chunks = (body.get("debug") or {}).get("retrieved_chunks") or []
        citations = body.get("citations") or []

        if not chunks:
            print("     -> WARN: no retrieved_chunks in response (DEBUG_CHUNKS off?)")

        verdict = judge_answer(case["query"], answer_text, chunks)
        record.update(
            {
                "actual_type": "answer",
                "answer": answer_text,
                "citations": citations,
                "chunks_returned": len(chunks),
                "judge": verdict,
            }
        )

        if "error" in verdict:
            print(f"     -> JUDGE ERROR: {verdict['error']}")
        else:
            counts = verdict["counts"]
            faith = verdict.get("faithfulness")
            faith_str = f"{faith:.2f}" if faith is not None else "n/a"
            flags = ""
            if counts["contradicted"]:
                flags += f" | {counts['contradicted']} CONTRADICTED"
            if counts["unsupported"]:
                flags += f" | {counts['unsupported']} unsupported"
            print(
                f"     -> {verdict.get('overall', 'n/a')} (faithfulness {faith_str}, "
                f"{counts['supported']}/{counts['total']} claims){flags}"
            )
        results.append(record)

    _report(results)


def _report(results: list) -> None:
    judged = [r for r in results if r.get("judge") and "error" not in r["judge"]]
    skipped = [r for r in results if r.get("skipped")]
    judge_errors = [r for r in results if r.get("judge", {}).get("error")]

    print("\n" + "=" * 70)
    print(f"Answered & judged : {len(judged)}")
    print(f"Skipped (non-answer / handler error): {len(skipped)}")
    if judge_errors:
        print(f"Judge errors      : {len(judge_errors)}")

    total_claims = sum(r["judge"]["counts"]["total"] for r in judged)
    supported = sum(r["judge"]["counts"]["supported"] for r in judged)
    unsupported = sum(r["judge"]["counts"]["unsupported"] for r in judged)
    contradicted = sum(r["judge"]["counts"]["contradicted"] for r in judged)

    if total_claims:
        print(
            f"\nCorpus faithfulness : {supported}/{total_claims} claims supported "
            f"({100 * supported / total_claims:.0f}%)"
        )
        print(f"  unsupported (invented) : {unsupported}")
        print(f"  contradicted (wrong)   : {contradicted}")

    # Per-answer breakdown, worst first.
    graded = [r for r in judged if r["judge"].get("faithfulness") is not None]
    graded.sort(key=lambda r: r["judge"]["faithfulness"])
    if graded:
        print("\nPer-answer faithfulness (worst first):")
        for r in graded:
            j = r["judge"]
            print(
                f"  {r['id']:>4} {j['faithfulness']:.2f}  "
                f"({j['counts']['supported']}/{j['counts']['total']})  {r['topic']}"
            )

    # The actionable part: every claim the model was not entitled to make.
    problems = []
    for r in judged:
        for c in r["judge"].get("claims", []):
            if c.get("verdict") in ("unsupported", "contradicted"):
                problems.append((r["id"], c))
    if problems:
        print("\nUngrounded / contradicted claims:")
        for case_id, c in problems:
            marker = "CONTRADICTED" if c["verdict"] == "contradicted" else "unsupported"
            print(f"  [{case_id}] ({marker}) {c['claim']}")
            if c.get("note"):
                print(f"         note: {c['note']}")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(
            {
                "run_at": datetime.now(timezone.utc).isoformat(),
                "model_id": os.environ.get("MODEL_ID", ""),
                "judge_model_id": os.environ.get(
                    "JUDGE_MODEL_ID", "us.anthropic.claude-sonnet-5"
                ),
                "answered_judged": len(judged),
                "corpus_faithfulness": (
                    f"{supported}/{total_claims}" if total_claims else None
                ),
                "results": results,
            },
            f,
            indent=2,
        )
    print(f"\nResults written to {os.path.relpath(RESULTS_PATH, PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
