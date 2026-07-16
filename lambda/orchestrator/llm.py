"""
LLM invocation module for the CSUCI Student Success Navigator.

This is the ONLY module that knows the Bedrock Converse API exists. It wraps
tool-use invocation (our own tiny ``bind_tools``): it sends the tool config,
forces a tool call via ``toolChoice: {any}``, and unwraps the response into a
clean list of ``{"name": ..., "input": ...}`` tool calls for the handler.

Structural validation also lives here (``validate_decision``): is each tool
recognized, are the student-facing fields present, is the combination allowed?
Domain policy (office coercion, citation range checks, fail-safe escalation)
belongs to the handler, which has the retrieved chunks and the safety context.

Environment variables
---------------------
- ``MODEL_ID`` — Bedrock model/inference-profile identifier. Claude models are
  inference-profile only; defaults to ``us.anthropic.claude-sonnet-5``.
"""

import logging
import os
from typing import Optional

import boto3

from tools import ANSWER_TOOL, CLARIFY_TOOL, DECLINE_TOOL, ESCALATE_TOOL

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-5"

# Lazy-initialised client
_client = None


def _get_client():
    """Return the ``bedrock-runtime`` client, creating it on first use."""
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime")
        logger.info("bedrock-runtime client initialised.")
    return _client


def _get_model_id() -> str:
    """Read MODEL_ID at request time so dev_server's late load_env() works."""
    return os.environ.get("MODEL_ID", _DEFAULT_MODEL_ID)


def format_messages_for_converse(
    conversation_history: list[dict],
    current_user_message: str,
) -> list[dict]:
    """Convert client-passed history turns into Bedrock Converse format.

    Client history stores turns as ``{"role": "user"|"assistant", "content": str}``;
    Converse wants ``{"role": ..., "content": [{"text": str}]}``.
    """
    messages: list[dict] = []

    for turn in conversation_history:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        messages.append({"role": role, "content": [{"text": content}]})

    messages.append(
        {"role": "user", "content": [{"text": current_user_message}]}
    )
    return messages


def extract_tool_calls(response: dict) -> list[dict]:
    """Unwrap a Converse response into ``[{"name": str, "input": dict}, ...]``.

    Ignores any interleaved text blocks — with ``toolChoice: any`` the tool
    calls are the decision; free text alongside them carries no contract.
    """
    output_message = response.get("output", {}).get("message", {})
    content_blocks = output_message.get("content", [])

    calls: list[dict] = []
    for block in content_blocks:
        tool_use = block.get("toolUse")
        if tool_use and tool_use.get("name"):
            calls.append(
                {
                    "name": tool_use["name"],
                    "input": tool_use.get("input") or {},
                }
            )
    return calls


def invoke_model(
    system_prompt: str,
    messages: list[dict],
    tool_config: dict,
    max_tokens: int = 1024,
) -> list[dict]:
    """Invoke the model with forced tool-use and return the parsed tool calls.

    Note: no ``temperature`` — Claude Sonnet 5 on Bedrock rejects it as
    deprecated (ValidationException).

    Args:
        system_prompt: The thin global system prompt (with numbered passages).
        messages:      Converse-format messages.
        tool_config:   ``tools.TOOL_CONFIG`` (tools + toolChoice).
        max_tokens:    Response cap.

    Returns:
        A list of ``{"name": str, "input": dict}`` tool calls (possibly empty
        if the model produced no usable tool call — the handler treats that as
        a fail-safe escalation).

    Raises:
        Exception: Re-raised after logging if the Bedrock call itself fails
        (the handler maps this to HTTP 500, distinct from unusable output).
    """
    model_id = _get_model_id()
    try:
        response = _get_client().converse(
            modelId=model_id,
            system=[{"text": system_prompt}],
            messages=messages,
            toolConfig=tool_config,
            inferenceConfig={
                "maxTokens": max_tokens,
            },
        )
    except Exception:
        logger.exception(
            "Failed to invoke Bedrock model %s via Converse API.", model_id
        )
        raise

    usage = response.get("usage", {})
    logger.info(
        "Bedrock Converse usage — input_tokens: %s, output_tokens: %s, stop: %s",
        usage.get("inputTokens", "N/A"),
        usage.get("outputTokens", "N/A"),
        response.get("stopReason", "N/A"),
    )

    return extract_tool_calls(response)


def translate_query_to_english(query: str) -> str:
    """Translate a student query to English to optimize vector search.

    The knowledge base is English, so non-English queries embed poorly. This
    is a plain Converse call (no tools, small budget); on ANY failure it
    falls back to the original query — retrieval degrades, nothing breaks.
    """
    system_prompt = (
        "You are a translation helper. Translate the user's message into "
        "plain English. If it is already in English, return it exactly as "
        "is. Output ONLY the final English translation text, with no "
        "introduction, no surrounding quotes, and no extra notes."
    )
    try:
        response = _get_client().converse(
            modelId=_get_model_id(),
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": query}]}],
            inferenceConfig={"maxTokens": 128},
        )
        blocks = response.get("output", {}).get("message", {}).get("content", [])
        translation = "".join(b.get("text", "") for b in blocks if "text" in b)
        translation = translation.strip().strip('"').strip("'")
        return translation or query
    except Exception:
        logger.warning("Query translation failed, falling back to original text.")
        return query


# ---------------------------------------------------------------------------
# Structural validation
# ---------------------------------------------------------------------------

_KNOWN_TOOLS = {ANSWER_TOOL, CLARIFY_TOOL, ESCALATE_TOOL, DECLINE_TOOL}


def _call_is_well_formed(call: dict) -> bool:
    """Check the student-facing required fields for a single tool call.

    Internal fields (``reason``, ``office``) are deliberately lenient here —
    the handler coerces or defaults them. The fields the student reads
    (``answer``, ``question``) must be non-empty strings.
    """
    name = call.get("name")
    inputs = call.get("input") or {}

    if name == ANSWER_TOOL:
        answer = inputs.get("answer")
        citations = inputs.get("citations")
        return bool(
            isinstance(answer, str)
            and answer.strip()
            and isinstance(citations, list)
        )
    if name == CLARIFY_TOOL:
        question = inputs.get("question")
        return bool(isinstance(question, str) and question.strip())
    if name == ESCALATE_TOOL:
        # office/reason are coerced by handler policy; presence not required.
        return True
    if name == DECLINE_TOOL:
        return True
    return False


def validate_decision(calls: list[dict]) -> Optional[dict]:
    """Structurally validate the model's tool calls into a decision.

    Valid shapes:
      - exactly one well-formed call of a known tool, or
      - exactly two calls forming the one allowed pair:
        ``answer_from_context`` + ``escalate_to_office``.

    Returns:
        ``{"primary": call, "escalation": call | None}`` where ``primary`` is
        the call that drives the response ``type`` (for the pair: the answer),
        or ``None`` when the output is structurally unusable (the handler
        fail-safes to a human).
    """
    known = [c for c in calls if c.get("name") in _KNOWN_TOOLS]
    if len(known) != len(calls):
        unknown = [c.get("name") for c in calls if c.get("name") not in _KNOWN_TOOLS]
        logger.warning("Model called unknown tool(s): %s", unknown)
        return None

    if len(calls) == 1:
        call = calls[0]
        if not _call_is_well_formed(call):
            logger.warning(
                "Tool call %s is missing required fields: %s",
                call.get("name"),
                call.get("input"),
            )
            return None
        if call["name"] == ESCALATE_TOOL:
            return {"primary": call, "escalation": call}
        return {"primary": call, "escalation": None}

    if len(calls) == 2:
        names = {c["name"] for c in calls}
        if names == {ANSWER_TOOL, ESCALATE_TOOL}:
            answer_call = next(c for c in calls if c["name"] == ANSWER_TOOL)
            escalate_call = next(c for c in calls if c["name"] == ESCALATE_TOOL)
            if _call_is_well_formed(answer_call):
                return {"primary": answer_call, "escalation": escalate_call}
            logger.warning("Pair rejected: answer call malformed.")
            return None
        logger.warning("Model returned a disallowed tool pair: %s", names)
        return None

    logger.warning("Model returned %d tool calls (expected 1 or 2).", len(calls))
    return None
