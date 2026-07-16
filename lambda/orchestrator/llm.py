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
- ``MAX_TOKENS`` — output token cap for the main tool-use decision; defaults to
  ``_DEFAULT_MAX_TOKENS``. Too low truncates long answers into malformed tool
  calls that needlessly fail-safe to a human.
"""

import logging
import os
from typing import Optional

import boto3

from tools import ANSWER_TOOL, CLARIFY_TOOL, DECLINE_TOOL, ESCALATE_TOOL

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-5"

# Output token cap for the main forced-tool-use decision. Long compound answers
# (e.g. "how do I register? also connect me with an advisor") can exceed a tight
# budget; when generation is truncated mid-tool-call the emitted toolUse is
# malformed (``citations`` never lands as its own field), which fails structural
# validation and needlessly fail-safes to a human. Keep this generous. Override
# with MAX_TOKENS.
_DEFAULT_MAX_TOKENS = 2048

# Fast/cheap model used for the auxiliary query-rewriting and translation
# steps (not the main tool-use decision). Override with REWRITE_MODEL_ID.
_DEFAULT_REWRITE_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

# How many trailing history turns to feed the query-contextualizer. A couple
# of exchanges is plenty to resolve "that"/"the completion degree version"
# style references without bloating the prompt.
_CONTEXTUALIZE_HISTORY_TURNS = 6

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


def _get_max_tokens() -> int:
    """Output token cap for the main tool-use call (read at request time)."""
    raw = os.environ.get("MAX_TOKENS")
    if raw:
        try:
            return int(raw)
        except ValueError:
            logger.warning("Invalid MAX_TOKENS=%r; using default %d.", raw, _DEFAULT_MAX_TOKENS)
    return _DEFAULT_MAX_TOKENS


def _get_rewrite_model_id() -> str:
    """Model for auxiliary rewrite/translation calls (read at request time).

    Defaults to a fast, cheap Haiku profile. Falls back to MODEL_ID only if
    someone explicitly sets REWRITE_MODEL_ID to an empty string.
    """
    return os.environ.get("REWRITE_MODEL_ID") or _DEFAULT_REWRITE_MODEL_ID


def _guardrail_config() -> Optional[dict]:
    """Return the Converse ``guardrailConfig`` block, or None if unconfigured.

    Read at request time (like MODEL_ID). When ``GUARDRAIL_ID`` is unset the
    tool-use call runs without a Bedrock Guardrail — the deterministic safety
    filter and the grounding/citation checks still apply, so this degrades
    gracefully in local/dev setups that have no guardrail provisioned.
    """
    guardrail_id = os.environ.get("GUARDRAIL_ID")
    if not guardrail_id:
        return None
    return {
        "guardrailIdentifier": guardrail_id,
        "guardrailVersion": os.environ.get("GUARDRAIL_VERSION", "DRAFT"),
        "trace": "enabled",
    }


def check_guardrail_only(text: str) -> dict:
    """Run the Bedrock Guardrail against raw text via the standalone
    ``ApplyGuardrail`` API, with no LLM call involved.

    Used to check the student's raw message for content-safety issues
    (denied topics, abusive language, etc.) before RAG retrieval / the
    KB-relevance score floor gets a chance to short-circuit the request —
    those are a separate, unrelated check and would otherwise prevent the
    guardrail from ever seeing messages with a low KB-relevance score.

    Args:
        text: Raw text to check (typically the student's message).

    Returns:
        A dict with keys:
            - ``intervened``: True if the guardrail acted on the text.
            - ``action_reason``: Bedrock's ``actionReason`` string
              (e.g. ``"Guardrail blocked."`` vs ``"...masked."``), empty
              if the guardrail didn't intervene.
            - ``blocked_message``: the guardrail's configured
              blocked-message text, if it intervened with a block
              (empty string otherwise).
            - ``trace``: the raw assessment object for logging.

    Note:
        Failures here are swallowed (logged only) and treated as
        "did not intervene" — this check is a pre-filter, not the sole
        safety mechanism, and the existing Converse-call guardrail check
        still runs downstream as a second layer.
    """
    guardrail_id = os.environ.get("GUARDRAIL_ID")
    if not guardrail_id:
        # No guardrail provisioned (e.g. local dev) — treat as not intervened.
        return {"intervened": False, "action_reason": "", "blocked_message": "", "trace": {}}
    try:
        response = _get_client().apply_guardrail(
            guardrailIdentifier=guardrail_id,
            guardrailVersion=os.environ.get("GUARDRAIL_VERSION", "DRAFT"),
            source="INPUT",
            content=[{"text": {"text": text}}],
        )
    except Exception:
        logger.exception("Standalone ApplyGuardrail check failed; treating as not intervened.")
        return {"intervened": False, "action_reason": "", "blocked_message": "", "trace": {}}

    intervened = response.get("action", "NONE") == "GUARDRAIL_INTERVENED"

    blocked_message = ""
    if intervened:
        output_blocks = response.get("outputs", [])
        blocked_message = "".join(
            block.get("text", "") for block in output_blocks if "text" in block
        ).strip()

    return {
        "intervened": intervened,
        "action_reason": response.get("actionReason", ""),
        "blocked_message": blocked_message,
        "trace": response.get("assessments", []),
    }


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
    max_tokens: Optional[int] = None,
) -> list[dict]:
    """Invoke the model with forced tool-use and return the parsed tool calls.

    When a Bedrock Guardrail is configured (``GUARDRAIL_ID`` /
    ``GUARDRAIL_VERSION`` env vars) it is applied to this call's input and
    output as a second content-safety layer.

    Note: no ``temperature`` — Claude Sonnet 5 on Bedrock rejects it as
    deprecated (ValidationException).

    Args:
        system_prompt: The thin global system prompt (with numbered passages).
        messages:      Converse-format messages.
        tool_config:   ``tools.TOOL_CONFIG`` (tools + toolChoice).
        max_tokens:    Response cap; defaults to ``_get_max_tokens()`` (MAX_TOKENS
                       env var, else ``_DEFAULT_MAX_TOKENS``) when None.

    Returns:
        A list of ``{"name": str, "input": dict}`` tool calls (possibly empty
        if the model produced no usable tool call, or if the guardrail blocked
        the output — the handler treats an empty/unusable result as a fail-safe
        escalation).

    Raises:
        Exception: Re-raised after logging if the Bedrock call itself fails
        (the handler maps this to HTTP 500, distinct from unusable output).
    """
    model_id = _get_model_id()
    if max_tokens is None:
        max_tokens = _get_max_tokens()
    converse_kwargs: dict = {
        "modelId": model_id,
        "system": [{"text": system_prompt}],
        "messages": messages,
        "toolConfig": tool_config,
        "inferenceConfig": {"maxTokens": max_tokens},
    }
    guardrail_config = _guardrail_config()
    if guardrail_config is not None:
        converse_kwargs["guardrailConfig"] = guardrail_config
    try:
        response = _get_client().converse(**converse_kwargs)
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


_CONTEXTUALIZE_SYSTEM_PROMPT = (
    "You rewrite a student's latest message into a single standalone search "
    "query for a university knowledge base. Use the conversation so far to "
    "resolve references such as 'that', 'it', 'the completion degree version', "
    "pronouns, and dropped subjects, so the query stands on its own without the "
    "conversation. Carry over the specific program, degree, department, or topic "
    "names from earlier turns whenever the latest message refers to them "
    "implicitly. Do NOT answer the question or add information that is not "
    "implied by the conversation. Output ONLY the rewritten search query as "
    "plain text — no quotes, no labels, no explanation. If the latest message "
    "is already self-contained, output it unchanged."
)


def contextualize_query(history: list[dict], message: str) -> str:
    """Rewrite a follow-up message into a standalone retrieval query.

    Vector search embeds only the query text, so a follow-up like "yes, I want
    that completion degree version" retrieves generically (any "completion
    degree" chunk) because the topic from earlier turns is absent. This uses a
    fast model to fold the recent conversation back into a self-contained query
    before retrieval — the generation model still gets the full history
    separately.

    Args:
        history: Prior turns as ``[{"role": ..., "content": ...}, ...]``.
        message: The student's current message.

    Returns:
        A standalone search query. On empty history or ANY failure, returns the
        original ``message`` unchanged — retrieval degrades to the old behavior,
        nothing breaks.
    """
    if not history:
        return message

    recent = history[-_CONTEXTUALIZE_HISTORY_TURNS:]
    transcript_lines: list[str] = []
    for turn in recent:
        role = turn.get("role", "user")
        speaker = "Assistant" if role == "assistant" else "Student"
        content = (turn.get("content") or "").strip()
        if content:
            transcript_lines.append(f"{speaker}: {content}")

    if not transcript_lines:
        return message

    transcript = "\n".join(transcript_lines)
    user_text = (
        f"Conversation so far:\n{transcript}\n\n"
        f"Latest message: {message}\n\n"
        "Rewrite the latest message as a standalone search query."
    )

    try:
        response = _get_client().converse(
            modelId=_get_rewrite_model_id(),
            system=[{"text": _CONTEXTUALIZE_SYSTEM_PROMPT}],
            messages=[{"role": "user", "content": [{"text": user_text}]}],
            inferenceConfig={"maxTokens": 128},
        )
        blocks = response.get("output", {}).get("message", {}).get("content", [])
        rewritten = "".join(b.get("text", "") for b in blocks if "text" in b)
        rewritten = rewritten.strip().strip('"').strip("'").strip()
        return rewritten or message
    except Exception:
        logger.warning(
            "Query contextualization failed, falling back to original message."
        )
        return message


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
