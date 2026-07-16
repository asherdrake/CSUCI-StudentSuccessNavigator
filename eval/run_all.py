"""
Run the full evaluation suite for the CSUCI Student Success Navigator.

There is no shared harness across the three evals — each is a standalone script
with its own input and output. This driver runs all three in sequence (each as a
separate process, so they stay isolated) and then writes ONE combined artifact:

  eval/results/run_all_results.json = {
    "manifest": { ...everything about HOW this run was configured... },
    "suites":   { per-suite status + summary metrics }
  }

The manifest is the point: a result is only meaningful if you know the model,
commit, knowledge base, and chunking config that produced it. It records the
current generation/judge/rewrite models, the git commit (and whether the tree was
dirty), timestamp, KB id, guardrail, region, the retrieval/inference parameters
the code uses, and — pulled live from the Bedrock control plane — the KB's
embedding model and chunking strategy. Control-plane lookups are best-effort: if
the IAM role can't describe the KB, the run still completes and the error is
recorded in the manifest instead.

Sub-evals run:
  1. run_eval.py           routing over single_turn_cases.json -> baseline_results.json
  2. run_faithfulness.py   answer groundedness (single-turn) -> faithfulness_results.json
  3. run_conversations.py  multi-turn routing + faithfulness -> conversation_results.json

Usage (needs live AWS creds + the Bedrock KB, same as the individual evals):
    python eval/run_all.py                       # run all three
    python eval/run_all.py routing conversations # run only the named suites

Suite names: routing, faithfulness, conversations. To filter by individual case
id, run the underlying script directly (e.g. python eval/run_faithfulness.py A13).
This is a manual/opt-in tool — deliberately NOT part of the pytest suite.
"""

import inspect
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL_DIR = os.path.join(PROJECT_ROOT, "eval")
# All eval outputs are written here (the sub-evals write their own result files
# to this same folder); inputs like single_turn_cases.json stay in eval/.
RESULTS_DIR = os.path.join(EVAL_DIR, "results")
ORCHESTRATOR_DIR = os.path.join(PROJECT_ROOT, "lambda", "orchestrator")
MANIFEST_AND_RESULTS_PATH = os.path.join(RESULTS_DIR, "run_all_results.json")

# name -> (script, result file). `name` is what the user types to select a suite.
SUITES = {
    "routing": ("run_eval.py", "baseline_results.json"),
    "faithfulness": ("run_faithfulness.py", "faithfulness_results.json"),
    "conversations": ("run_conversations.py", "conversation_results.json"),
}
SUITE_ORDER = ["routing", "faithfulness", "conversations"]


def load_env() -> None:
    """Load .env into os.environ so the manifest can record MODEL_ID/KB id/etc.

    Uses setdefault (never clobbers an already-exported value), matching the
    sub-evals; subprocesses inherit this environment.
    """
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


# ---------------------------------------------------------------------------
# Manifest collection — the "how was this run configured" record
# ---------------------------------------------------------------------------


def _git_info() -> dict:
    """Current commit, branch, and whether the working tree was dirty."""

    def _git(*args: str) -> str:
        return subprocess.check_output(
            ["git", *args], cwd=PROJECT_ROOT, stderr=subprocess.DEVNULL, text=True
        ).strip()

    try:
        commit = _git("rev-parse", "HEAD")
        return {
            "commit": commit,
            "commit_short": commit[:10],
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            # Dirty = uncommitted changes; a result from a dirty tree is not
            # reproducible from the commit alone, so flag it loudly.
            "dirty": bool(_git("status", "--porcelain")),
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def _model_config() -> dict:
    """Effective generation / judge / rewrite model ids (env override or code default)."""
    info: dict = {
        "generation": {"env_MODEL_ID": os.environ.get("MODEL_ID")},
        "judge": {"env_JUDGE_MODEL_ID": os.environ.get("JUDGE_MODEL_ID")},
        "rewrite": {"env_REWRITE_MODEL_ID": os.environ.get("REWRITE_MODEL_ID")},
    }
    # Resolve the effective values by importing the same defaults the code uses,
    # so the manifest matches what actually ran even when env vars are unset.
    for path in (ORCHESTRATOR_DIR, EVAL_DIR):
        if path not in sys.path:
            sys.path.insert(0, path)
    try:
        import llm  # noqa: E402

        info["generation"]["effective"] = llm._get_model_id()
        info["rewrite"]["effective"] = llm._get_rewrite_model_id()
    except Exception as exc:  # noqa: BLE001
        info["generation"]["effective_error"] = f"{type(exc).__name__}: {exc}"
    try:
        import faithfulness_judge  # noqa: E402

        info["judge"]["effective"] = faithfulness_judge._judge_model_id()
    except Exception as exc:  # noqa: BLE001
        info["judge"]["effective_error"] = f"{type(exc).__name__}: {exc}"
    return info


def _pipeline_params() -> dict:
    """Retrieval + generation-inference params, read from the code that uses them."""
    params: dict = {
        "retrieval": {
            "search_type": "Bedrock KB default (not overridden in code)",
            "note": (
                "number_of_results is retrieve_context's default; handler.py "
                "calls retrieve_context(query, top_k=5) at the recorded commit."
            ),
        },
        "generation_inference": {
            "temperature": None,
            "note": "temperature intentionally unset — Sonnet 5 rejects it; see llm.invoke_model.",
        },
    }
    for path in (ORCHESTRATOR_DIR,):
        if path not in sys.path:
            sys.path.insert(0, path)
    try:
        import retriever  # noqa: E402

        top_k = inspect.signature(retriever.retrieve_context).parameters["top_k"].default
        params["retrieval"]["number_of_results"] = top_k
    except Exception as exc:  # noqa: BLE001
        params["retrieval"]["error"] = f"{type(exc).__name__}: {exc}"
    try:
        import llm  # noqa: E402

        # invoke_model resolves max_tokens from MAX_TOKENS (or a code default) at
        # request time, so read the effective value rather than the None sentinel
        # in the signature.
        params["generation_inference"]["max_tokens"] = llm._get_max_tokens()
        params["generation_inference"]["env_MAX_TOKENS"] = os.environ.get("MAX_TOKENS")
    except Exception as exc:  # noqa: BLE001
        params["generation_inference"]["error"] = f"{type(exc).__name__}: {exc}"
    return params


def _knowledge_base_info() -> dict:
    """Describe the KB via the Bedrock control plane: embedding model + chunking.

    Best-effort. Requires bedrock:GetKnowledgeBase / ListDataSources /
    GetDataSource on the eval role; on any failure the error is returned rather
    than raised, so the run still completes.
    """
    kb_id = os.environ.get("BEDROCK_KB_ID", "")
    info: dict = {"id": kb_id}
    if not kb_id:
        info["error"] = "BEDROCK_KB_ID not set"
        return info
    try:
        import boto3  # noqa: E402

        client = boto3.client("bedrock-agent", region_name=os.environ.get("AWS_REGION"))
        kb = client.get_knowledge_base(knowledgeBaseId=kb_id)["knowledgeBase"]
        info["name"] = kb.get("name")
        info["status"] = kb.get("status")

        kb_cfg = kb.get("knowledgeBaseConfiguration", {})
        info["type"] = kb_cfg.get("type")
        vec = kb_cfg.get("vectorKnowledgeBaseConfiguration", {})
        info["embedding_model_arn"] = vec.get("embeddingModelArn")
        emb_cfg = (vec.get("embeddingModelConfiguration") or {}).get(
            "bedrockEmbeddingModelConfiguration", {}
        )
        info["embedding_dimensions"] = emb_cfg.get("dimensions")
        info["embedding_data_type"] = emb_cfg.get("embeddingDataType")

        storage = kb.get("storageConfiguration", {})
        info["vector_store_type"] = storage.get("type")

        data_sources = []
        for summary in client.list_data_sources(knowledgeBaseId=kb_id).get(
            "dataSourceSummaries", []
        ):
            ds_id = summary["dataSourceId"]
            try:
                ds = client.get_data_source(
                    knowledgeBaseId=kb_id, dataSourceId=ds_id
                )["dataSource"]
                ingestion = ds.get("vectorIngestionConfiguration", {})
                data_sources.append(
                    {
                        "id": ds_id,
                        "name": ds.get("name"),
                        "status": ds.get("status"),
                        # Captured verbatim — the exact chunking strategy shape
                        # (HIERARCHICAL / FIXED_SIZE / SEMANTIC / NONE) and its
                        # token/overlap settings, plus any parsing config.
                        "chunking_configuration": ingestion.get("chunkingConfiguration"),
                        "parsing_configuration": ingestion.get("parsingConfiguration"),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                data_sources.append({"id": ds_id, "error": f"{type(exc).__name__}: {exc}"})
        info["data_sources"] = data_sources
    except Exception as exc:  # noqa: BLE001
        info["error"] = f"{type(exc).__name__}: {exc}"
    return info


def _runtime_info() -> dict:
    info = {"python": sys.version.split()[0], "platform": sys.platform}
    try:
        import boto3  # noqa: E402

        info["boto3"] = boto3.__version__
    except Exception:  # noqa: BLE001
        pass
    return info


def collect_manifest(selected: list, run_at: datetime) -> dict:
    """Assemble the full run manifest. Every sub-collector is failure-tolerant."""
    return {
        "run_at": run_at.isoformat(),
        "suites_selected": selected,
        "git": _git_info(),
        "models": _model_config(),
        "pipeline_params": _pipeline_params(),
        "bedrock": {
            "region": os.environ.get("AWS_REGION"),
            "guardrail_id": os.environ.get("GUARDRAIL_ID"),
            "guardrail_version": os.environ.get("GUARDRAIL_VERSION"),
            "debug_chunks": os.environ.get("DEBUG_CHUNKS"),
        },
        "knowledge_base": _knowledge_base_info(),
        "runtime": _runtime_info(),
    }


# ---------------------------------------------------------------------------
# Per-suite summary
# ---------------------------------------------------------------------------


def _pct(value) -> str:
    """Turn an 'a/b' string into 'a/b (NN%)'; pass through anything else."""
    try:
        num, den = str(value).split("/")
        num, den = int(num), int(den)
        return f"{value} ({100 * num / den:.0f}%)" if den else str(value)
    except (ValueError, AttributeError):
        return str(value)


def _load_result(filename: str, started_at: float) -> dict | None:
    """Load a suite's result JSON, but only if it was written by THIS run.

    Guards against summarizing a stale *_results.json left over from an earlier
    invocation when the sub-eval failed before writing a new one.
    """
    path = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(path) or os.path.getmtime(path) < started_at:
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _conversation_faithfulness(result: dict) -> str | None:
    """Sum answer-turn claim counts across all scenarios into an 'a/b' string."""
    supported = total = 0
    for scenario in result.get("results", []):
        for turn in scenario.get("turns", []):
            judge = turn.get("judge")
            if judge and "error" not in judge:
                counts = judge.get("counts", {})
                supported += counts.get("supported", 0)
                total += counts.get("total", 0)
    return f"{supported}/{total}" if total else None


def _summary_metrics(name: str, result: dict) -> dict:
    """Machine-readable summary for one suite (also drives the console print)."""
    if name == "routing":
        return {
            "outcome_accuracy": result.get("outcome_accuracy"),
            "routing_accuracy": result.get("routing_accuracy"),
        }
    if name == "faithfulness":
        return {
            "answers_judged": result.get("answered_judged"),
            "corpus_faithfulness": result.get("corpus_faithfulness"),
        }
    if name == "conversations":
        return {
            "scenarios_correct": result.get("scenarios_ok"),
            "turn_routing": result.get("turn_routing"),
            "answer_faithfulness": _conversation_faithfulness(result),
        }
    return {}


def main() -> None:
    requested = [a.lower() for a in sys.argv[1:]] or SUITE_ORDER
    unknown = [s for s in requested if s not in SUITES]
    if unknown:
        print(f"Unknown suite(s): {', '.join(unknown)}")
        print(f"Valid suites: {', '.join(SUITE_ORDER)}")
        sys.exit(2)
    selected = [s for s in SUITE_ORDER if s in requested]

    load_env()
    run_at = datetime.now(timezone.utc)
    started_at = time.time()

    # Capture the manifest up front — it describes the config the suites run under.
    manifest = collect_manifest(selected, run_at)
    print("=" * 70)
    print("RUN MANIFEST")
    print("=" * 70)
    print(json.dumps(manifest, indent=2, default=str))

    statuses: dict = {}
    for name in selected:
        script, _ = SUITES[name]
        print("\n" + "#" * 70)
        print(f"# {name.upper()}  ({script})")
        print("#" * 70, flush=True)
        # Inherit stdout/stderr so each eval streams live; separate process keeps
        # boto clients and module state isolated between suites.
        proc = subprocess.run(
            [sys.executable, os.path.join(EVAL_DIR, script)],
            cwd=PROJECT_ROOT,
        )
        statuses[name] = "ok" if proc.returncode == 0 else f"exit {proc.returncode}"

    elapsed = time.time() - started_at

    # ---- Combined scorecard + machine-readable artifact ----
    suites_out: dict = {}
    print("\n" + "=" * 70)
    print("COMBINED EVALUATION SUMMARY")
    print("=" * 70)
    for name in selected:
        _, result_file = SUITES[name]
        entry = {"status": statuses[name], "result_file": result_file, "metrics": None}
        print(f"\n{name.capitalize()}  [{statuses[name]}]")
        if statuses[name] != "ok":
            entry["note"] = "suite did not complete — see its output above"
            print("  (suite did not complete — see its output above)")
        else:
            result = _load_result(result_file, started_at)
            if result is None:
                entry["note"] = f"no fresh {result_file} written"
                print(f"  (no fresh {result_file} written)")
            else:
                metrics = _summary_metrics(name, result)
                entry["metrics"] = metrics
                for label, value in metrics.items():
                    if value is None:
                        continue
                    shown = _pct(value) if isinstance(value, str) and "/" in value else value
                    print(f"  {label:<20}: {shown}")
        suites_out[name] = entry

    combined = {"manifest": manifest, "suites": suites_out}
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(MANIFEST_AND_RESULTS_PATH, "w") as f:
        json.dump(combined, f, indent=2, default=str)

    print(f"\nTotal wall time: {elapsed:.0f}s")
    print(f"Manifest + summary written to {os.path.relpath(MANIFEST_AND_RESULTS_PATH, PROJECT_ROOT)}")

    failed = [n for n, s in statuses.items() if s != "ok"]
    if failed:
        print(f"Suites that did not complete cleanly: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
