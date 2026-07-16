"""
LLM-as-judge for answer *groundedness* (faithfulness) in the CSUCI Navigator.

The system prompt tells the model the retrieved passages are its ONLY source of
truth (see prompts.py). This judge tests whether the model actually obeyed that:
it extracts the atomic factual claims a student would rely on from an answer, and
labels each one against the passages that were in front of the model when it
answered — supported / unsupported / contradicted. Nothing here re-retrieves or
consults the open web; "grounded" means "backed by the passages the model saw,"
which is exactly the contract the system prompt sets.

This is deliberately separate from run_eval.py's routing scorecard: that grades
*which* tool the model picked; this grades the *truthfulness of the prose* inside
an answer_from_context call.

Judge model: JUDGE_MODEL_ID (default us.anthropic.claude-sonnet-5 — the same
profile MODEL_ID uses, so it works out of the box). A stronger judge such as
us.anthropic.claude-opus-4-8 is preferable when that inference profile is enabled
in the account; set JUDGE_MODEL_ID to switch. Uses the Bedrock Converse API with
forced tool-use, matching the rest of the codebase (no Anthropic SDK).
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import boto3

logger = logging.getLogger(__name__)

_DEFAULT_JUDGE_MODEL_ID = "us.anthropic.claude-sonnet-5"

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime")
    return _client


def _judge_model_id() -> str:
    return os.environ.get("JUDGE_MODEL_ID") or _DEFAULT_JUDGE_MODEL_ID


# The judge returns its verdict by calling this tool — same forced-tool pattern
# the orchestrator uses, so the output is structured, not free text we must parse.
_GROUNDEDNESS_TOOL_NAME = "report_groundedness"
_GROUNDEDNESS_TOOL = {
    "toolSpec": {
        "name": _GROUNDEDNESS_TOOL_NAME,
        "description": (
            "Report the groundedness of an assistant answer against the numbered "
            "passages it was given. Extract every atomic factual claim a student "
            "would act on, and judge each ONLY against the passages."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "claims": {
                        "type": "array",
                        "description": (
                            "One entry per atomic factual claim in the answer "
                            "(a fact, number, name, URL, deadline, contact, or "
                            "concrete step). Skip pure pleasantries, offers to "
                            "help, and generic encouragement."
                        ),
                        "items": {
                            "type": "object",
                            "properties": {
                                "claim": {
                                    "type": "string",
                                    "description": "The factual claim, quoted or closely paraphrased.",
                                },
                                "verdict": {
                                    "type": "string",
                                    "enum": ["supported", "unsupported", "contradicted"],
                                    "description": (
                                        "supported = a passage states or directly "
                                        "entails it; unsupported = no passage covers "
                                        "it (the model brought it in from outside); "
                                        "contradicted = a passage says otherwise."
                                    ),
                                },
                                "passages": {
                                    "type": "array",
                                    "items": {"type": "integer"},
                                    "description": "Passage number(s) that support or contradict this claim; empty if none.",
                                },
                                "note": {
                                    "type": "string",
                                    "description": "Brief reason, especially for unsupported/contradicted.",
                                },
                            },
                            "required": ["claim", "verdict", "passages"],
                        },
                    },
                    "overall": {
                        "type": "string",
                        "enum": ["grounded", "partially_grounded", "ungrounded"],
                        "description": (
                            "grounded = all material claims supported; "
                            "partially_grounded = some unsupported but nothing "
                            "contradicted; ungrounded = a contradiction, or most "
                            "claims unsupported."
                        ),
                    },
                    "summary": {
                        "type": "string",
                        "description": "One sentence on the answer's truthfulness against the passages.",
                    },
                },
                "required": ["claims", "overall", "summary"],
            }
        },
    }
}

_JUDGE_SYSTEM_PROMPT = (
    "You are a strict grounding auditor for a university help chatbot. The "
    "assistant was told the numbered passages are its ONLY allowed source of "
    "truth. Your job is to catch hallucination: any factual claim in the answer "
    "that the passages do not support.\n\n"
    "Method:\n"
    "1. Read the passages. They are the only ground truth. Do NOT use outside "
    "knowledge about CSU Channel Islands or anything else — a claim that happens "
    "to be true in the real world is still 'unsupported' if no passage backs it.\n"
    "2. Break the answer into atomic factual claims (facts, numbers, names, "
    "URLs, emails, phone numbers, deadlines, office names, concrete steps). "
    "Ignore greetings, offers to help further, and generic encouragement.\n"
    "3. Label each claim: 'supported' (a passage states or directly entails it), "
    "'unsupported' (no passage covers it), or 'contradicted' (a passage says "
    "otherwise). Record which passage number(s) apply.\n"
    "4. A vague or hedged claim that a passage clearly implies counts as "
    "supported. When genuinely unsure, prefer 'unsupported' over 'supported'.\n"
    "Report your findings by calling report_groundedness exactly once."
)


def _format_passages(chunks: List[dict]) -> str:
    if not chunks:
        return "(No passages were retrieved.)"
    lines: List[str] = []
    for i, chunk in enumerate(chunks, start=1):
        title = chunk.get("source_title") or "Unknown Source"
        text = (chunk.get("text") or "").strip()
        lines.append(f"[Passage {i}] (source: {title})\n{text}")
    return "\n\n".join(lines)


def judge_answer(
    query: str,
    answer: str,
    chunks: List[dict],
    max_tokens: int = 2048,
) -> Dict[str, Any]:
    """Audit one answer's groundedness against the passages it was given.

    Returns the parsed report_groundedness input plus a computed
    ``faithfulness`` score (supported / total claims), or an ``error`` key if
    the judge call failed or produced no usable tool call.
    """
    user_text = (
        f"## Student question\n{query}\n\n"
        f"## Numbered passages (the only allowed source of truth)\n"
        f"{_format_passages(chunks)}\n\n"
        f"## Assistant answer to audit\n{answer}\n\n"
        "Audit the answer now by calling report_groundedness."
    )

    try:
        response = _get_client().converse(
            modelId=_judge_model_id(),
            system=[{"text": _JUDGE_SYSTEM_PROMPT}],
            messages=[{"role": "user", "content": [{"text": user_text}]}],
            toolConfig={
                "tools": [_GROUNDEDNESS_TOOL],
                "toolChoice": {"tool": {"name": _GROUNDEDNESS_TOOL_NAME}},
            },
            inferenceConfig={"maxTokens": max_tokens},
        )
    except Exception as exc:  # noqa: BLE001 — one bad case must not kill the run
        logger.exception("Judge call failed.")
        return {"error": f"judge call failed: {exc}"}

    report: Optional[dict] = None
    for block in response.get("output", {}).get("message", {}).get("content", []):
        tool_use = block.get("toolUse")
        if tool_use and tool_use.get("name") == _GROUNDEDNESS_TOOL_NAME:
            report = tool_use.get("input") or {}
            break

    if report is None:
        return {"error": "judge returned no report_groundedness tool call"}

    raw_claims = report.get("claims") or []
    # The judge model sometimes emits a claim as a bare string instead of the
    # object its tool schema requires; drop those so counting never crashes on
    # ``str.get`` and one malformed claim can't take down the whole run.
    claims = [c for c in raw_claims if isinstance(c, dict)]
    report["claims"] = claims
    total = len(claims)
    supported = sum(1 for c in claims if c.get("verdict") == "supported")
    contradicted = sum(1 for c in claims if c.get("verdict") == "contradicted")
    unsupported = sum(1 for c in claims if c.get("verdict") == "unsupported")

    report["faithfulness"] = (supported / total) if total else None
    report["counts"] = {
        "total": total,
        "supported": supported,
        "unsupported": unsupported,
        "contradicted": contradicted,
    }
    # `overall`/`summary` are required by the schema but the model can still
    # omit them; derive a sensible `overall` from the counts so downstream
    # reporting never KeyErrors.
    if not report.get("overall"):
        if contradicted or (total and supported / total < 0.5):
            report["overall"] = "ungrounded"
        elif unsupported:
            report["overall"] = "partially_grounded"
        else:
            report["overall"] = "grounded"
    report.setdefault("summary", "")
    return report
