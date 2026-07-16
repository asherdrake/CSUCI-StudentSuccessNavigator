"""
Multi-turn conversation eval for the CSUCI Student Success Navigator.

run_eval.py and run_faithfulness.py each judge a SINGLE user turn with empty
history. This one judges scripted MULTI-TURN scenarios (multi_turn_cases.json),
which is where the interesting routing behavior lives:

  - Does an ambiguous opener get CLARIFIED instead of guessed or escalated?
  - When the student answers the clarifying question with enough context, does
    the bot then do the right thing — answer if it's answerable, escalate if the
    resolved question actually needs a human?
  - Is the resolved ANSWER still grounded in the retrieved passages?

It threads the bot's own replies back into `history` between turns exactly as
the frontend does, so it also exercises contextualize_query (the step that folds
the conversation into the retrieval query for follow-ups).

Each scenario is a list of turns; each turn carries:
  - user               : the student's message for that turn
  - expect_type        : answer | clarify | escalate | decline | crisis
  - expected_office    : (escalate turns) which office the handoff should target
  - judge_faithfulness : (answer turns) also grade the answer's groundedness

Usage (needs live AWS creds + the Bedrock KB, same as the other evals):
    python eval/run_conversations.py           # all scenarios
    python eval/run_conversations.py C1 C3      # only specific scenario ids

This is a manual/opt-in tool — deliberately NOT part of the pytest suite.
Output: per-turn verdicts + a JSON dump to eval/results/conversation_results.json.
"""

import json
import os
import sys
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "lambda"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "lambda", "orchestrator"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

MULTI_TURN_CASES_PATH = os.path.join(PROJECT_ROOT, "eval", "multi_turn_cases.json")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "eval", "results")
RESULTS_PATH = os.path.join(RESULTS_DIR, "conversation_results.json")

# Answer bodies for answered cases are split on this separator; the escalation
# addendum after it is code-owned boilerplate, not model prose, so we judge only
# the part before it (mirrors run_faithfulness.py).
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
    os.environ["DEBUG_CHUNKS"] = "1"


def _send(lambda_handler, message: str, history: list, session_id: str) -> dict:
    """Send one turn through the live handler; return the parsed 200 body."""
    event = {
        "httpMethod": "POST",
        "body": json.dumps(
            {"message": message, "history": history, "sessionId": session_id}
        ),
    }
    response = lambda_handler(event, None)
    return json.loads(response["body"])


def run_scenario(lambda_handler, judge_answer, scenario: dict) -> dict:
    """Walk a scenario turn-by-turn, threading history, grading each turn."""
    session_id = f"conv-{scenario['id']}"
    history: list = []
    turn_records = []

    for idx, turn in enumerate(scenario["turns"], start=1):
        user_msg = turn["user"]
        expect_type = turn["expect_type"]

        try:
            body = _send(lambda_handler, user_msg, history, session_id)
        except Exception as exc:  # noqa: BLE001 — one turn must not kill the run
            turn_records.append(
                {"turn": idx, "user": user_msg, "expect_type": expect_type,
                 "actual_type": "error", "type_ok": False, "error": str(exc)}
            )
            break

        actual_type = body.get("type", "error")
        type_ok = actual_type == expect_type

        rec = {
            "turn": idx,
            "user": user_msg,
            "expect_type": expect_type,
            "actual_type": actual_type,
            "type_ok": type_ok,
            "message_preview": (body.get("message") or "")[:160],
        }

        # Office check on escalate turns.
        expected_office = turn.get("expected_office")
        if expect_type == "escalate" and expected_office:
            actual_office = (body.get("escalation") or {}).get("office")
            rec["expected_office"] = expected_office
            rec["actual_office"] = actual_office
            rec["office_ok"] = actual_office == expected_office

        # Faithfulness on answer turns (only if it actually answered).
        if turn.get("judge_faithfulness") and actual_type == "answer":
            answer_text = (body.get("message") or "").split(_ESCALATION_SEP, 1)[0].strip()
            chunks = (body.get("debug") or {}).get("retrieved_chunks") or []
            rec["chunks_returned"] = len(chunks)
            rec["judge"] = judge_answer(user_msg, answer_text, chunks)

        turn_records.append(rec)

        # Thread this exchange back into history, exactly as the frontend would:
        # the student's message, then the assistant's visible reply text.
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": body.get("message") or ""})

    scenario_ok = all(t["type_ok"] for t in turn_records) and all(
        t.get("office_ok", True) for t in turn_records
    )
    return {
        "id": scenario["id"],
        "topic": scenario["topic"],
        "scenario_ok": scenario_ok,
        "turns": turn_records,
    }


def main() -> None:
    load_env()
    from handler import lambda_handler
    from faithfulness_judge import judge_answer

    with open(MULTI_TURN_CASES_PATH) as f:
        scenarios = json.load(f)

    only_ids = set(sys.argv[1:])
    if only_ids:
        scenarios = [s for s in scenarios if s["id"] in only_ids]

    results = []
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n[{i}/{len(scenarios)}] {scenario['id']}: {scenario['topic']}")
        result = run_scenario(lambda_handler, judge_answer, scenario)
        for t in result["turns"]:
            status = "PASS" if t["type_ok"] else "FAIL"
            line = (f"   turn {t['turn']}: {status}  expected {t['expect_type']}, "
                    f"got {t['actual_type']}")
            if "office_ok" in t:
                line += f" | office {'OK' if t['office_ok'] else 'WRONG'} ({t.get('actual_office')})"
            if t.get("judge") and "error" not in t["judge"]:
                j = t["judge"]
                faith = j.get("faithfulness")
                faith_str = f"{faith:.2f}" if faith is not None else "n/a"
                line += (f" | faithfulness {faith_str} "
                         f"({j['counts']['supported']}/{j['counts']['total']})")
            elif t.get("judge", {}).get("error"):
                line += f" | JUDGE ERROR: {t['judge']['error']}"
            print(line)
        print(f"   => scenario {'PASS' if result['scenario_ok'] else 'FAIL'}")
        results.append(result)

    _report(results)


def _report(results: list) -> None:
    all_turns = [t for r in results for t in r["turns"]]
    scenarios_ok = sum(1 for r in results if r["scenario_ok"])
    turns_ok = sum(1 for t in all_turns if t["type_ok"])

    office_turns = [t for t in all_turns if "office_ok" in t]
    office_ok = sum(1 for t in office_turns if t["office_ok"])

    judged = [t for t in all_turns if t.get("judge") and "error" not in t["judge"]]
    total_claims = sum(t["judge"]["counts"]["total"] for t in judged)
    supported = sum(t["judge"]["counts"]["supported"] for t in judged)

    print("\n" + "=" * 70)
    print(f"Scenarios fully correct : {scenarios_ok}/{len(results)}")
    print(f"Turn routing accuracy   : {turns_ok}/{len(all_turns)} "
          f"({100 * turns_ok / len(all_turns):.0f}%)" if all_turns else "")
    if office_turns:
        print(f"Escalation office match : {office_ok}/{len(office_turns)}")
    if total_claims:
        print(f"Answer faithfulness     : {supported}/{total_claims} claims "
              f"({100 * supported / total_claims:.0f}%)")

    failures = [t for r in results for t in r["turns"] if not t["type_ok"]
                or t.get("office_ok") is False]
    if failures:
        print("\nRouting failures:")
        for r in results:
            for t in r["turns"]:
                if not t["type_ok"] or t.get("office_ok") is False:
                    detail = f"expected {t['expect_type']}, got {t['actual_type']}"
                    if t.get("office_ok") is False:
                        detail += f" (office {t.get('actual_office')} != {t.get('expected_office')})"
                    print(f"  {r['id']} turn {t['turn']}: {detail}")
                    print(f"       msg: {t['message_preview']}")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(
            {
                "run_at": datetime.now(timezone.utc).isoformat(),
                "model_id": os.environ.get("MODEL_ID", ""),
                "judge_model_id": os.environ.get(
                    "JUDGE_MODEL_ID", "us.anthropic.claude-sonnet-5"
                ),
                "scenarios_ok": f"{scenarios_ok}/{len(results)}",
                "turn_routing": f"{turns_ok}/{len(all_turns)}",
                "results": results,
            },
            f,
            indent=2,
        )
    print(f"\nResults written to {os.path.relpath(RESULTS_PATH, PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
