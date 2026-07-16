"""
Lambda orchestrator handler for the CSUCI Student Success Navigator.

Flow: crisis check (deterministic, pre-LLM) → RAG retrieval (always) → one
Converse tool-use call → validate + dispatch the structured decision into the
type-discriminated API contract. The model decides answer / clarify / escalate
/ decline by tool selection (see tools.py); this handler applies policy:
citation range checks, office coercion, fail-safe escalation, and the
explicit-human-request backstop.

Failure policy: unusable model output fails safe to a human handoff
(general_support); Bedrock/API errors return HTTP 500 (retryable) instead.
All interactions are logged in structured JSON to CloudWatch.
"""

import json
import logging
import os
import sys
import uuid
from typing import Any, Dict, List, Optional

# Make sure safety_filter (lambda/) and sibling orchestrator modules
# (retriever, prompts, llm, router — lambda/orchestrator/) are importable
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.join(_THIS_DIR, "..")
for _path in (_PARENT_DIR, _THIS_DIR):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from safety_filter import check_message  # noqa: E402
from retriever import retrieve_context  # noqa: E402
from prompts import (  # noqa: E402
    DECLINE_MESSAGE,
    ESCALATION_ADDENDUM,
    ESCALATION_MESSAGE,
    SPANISH_OVERRIDE,
    SYSTEM_PROMPT_TEMPLATE,
)
from llm import (  # noqa: E402
    check_guardrail_only,
    format_messages_for_converse,
    invoke_model,
    translate_query_to_english,
    validate_decision,
)
from router import DEFAULT_OFFICE_KEY, build_escalation  # noqa: E402
from tools import (  # noqa: E402
    ANSWER_TOOL,
    CLARIFY_TOOL,
    DECLINE_TOOL,
    ESCALATE_TOOL,
    TOOL_CONFIG,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# CORS response headers
_CORS_HEADERS: Dict[str, str] = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
    "Content-Type": "application/json",
}


def _debug_chunks_enabled() -> bool:
    """Whether to log/return retrieved chunks (set DEBUG_CHUNKS=1 in .env).

    Read at REQUEST time, not import time: dev_server.py imports this module
    before it calls load_env(), so a module-level constant would capture the
    flag before .env is loaded and always be False.
    """
    return os.environ.get("DEBUG_CHUNKS", "").lower() in ("1", "true", "yes")


# Bedrock Guardrails has no native input length limit (confirmed against the
# Converse API schema), so oversized input is rejected here before any
# retrieval or Bedrock call is made, to save cost/latency.
MAX_INPUT_LENGTH = 1000

# Shown when a message exceeds MAX_INPUT_LENGTH (rendered as a clarify turn).
INPUT_TOO_LONG_MESSAGE = (
    "That message is a bit long — could you shorten it to a specific question? "
    "I can help best with focused questions about CSUCI resources."
)


def _build_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Return an API Gateway proxy-integration response dict."""
    return {
        "statusCode": status_code,
        "headers": _CORS_HEADERS,
        "body": json.dumps(body, default=str),
    }


def _format_retrieved_chunks(chunks: List[dict]) -> str:
    """Format RAG passages into the numbered block the model cites by number."""
    if not chunks:
        return "(No relevant passages were found in the knowledge base.)"

    lines: List[str] = []
    for i, chunk in enumerate(chunks, start=1):
        title = chunk.get("source_title", "Unknown Source")
        text = chunk.get("text", "").strip()
        # Deliberately no URL here — the model cites by passage number only,
        # and code resolves numbers to trusted URLs afterwards.
        lines.append(f"**Passage {i}** (source: {title}):\n{text}")

    return "\n\n".join(lines)


def _resolve_citations(
    raw_citations: List[Any], chunks: List[dict]
) -> Optional[List[Dict[str, Any]]]:
    """Resolve model-cited passage numbers into trusted source entries.

    Returns a deduplicated list of ``{title, url, passages: [N, ...]}`` built
    ONLY from the retrieved chunks — the model never supplies a URL. Returns
    ``None`` when the citations are unusable (empty, non-integer, or out of
    range), which the caller treats as an ungrounded answer.
    """
    if not raw_citations:
        return None

    numbers: List[int] = []
    for item in raw_citations:
        try:
            n = int(item)
        except (TypeError, ValueError):
            return None
        if n < 1 or n > len(chunks):
            return None
        if n not in numbers:
            numbers.append(n)

    resolved: List[Dict[str, Any]] = []
    for n in numbers:
        chunk = chunks[n - 1]
        url = chunk.get("source_url", "")
        title = chunk.get("source_title", "") or "Unknown Source"
        existing = next(
            (c for c in resolved if c["url"] == url and c["title"] == title), None
        )
        if existing:
            existing["passages"].append(n)
        else:
            resolved.append({"title": title, "url": url, "passages": [n]})
    return resolved


def _log_interaction(**fields: Any) -> None:
    """Log the request outcome to CloudWatch in a structured JSON schema."""
    logger.info(json.dumps({"interaction": fields}, default=str))


# ---------------------------------------------------------------------------
# Lambda Handler
# ---------------------------------------------------------------------------


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda entry point for the Student Success Navigator."""
    logger.info("Received event: %s", json.dumps(event, default=str))
    debug_chunks = _debug_chunks_enabled()

    # --- CORS Preflight ---
    http_method = event.get("httpMethod", "") or event.get(
        "requestContext", {}
    ).get("http", {}).get("method", "")

    if http_method == "OPTIONS":
        return _build_response(200, {"message": "CORS preflight OK"})

    # --- 1. Parse & Validate request body ---
    try:
        body = event.get("body")
        if isinstance(body, str):
            body = json.loads(body)
        elif body is None:
            body = {}
    except (json.JSONDecodeError, TypeError) as exc:
        logger.error("Invalid JSON request body: %s", exc)
        return _build_response(400, {"error": "Invalid JSON in request body."})

    message: str = body.get("message", "").strip()
    if not message:
        return _build_response(400, {"error": "Missing required field: 'message'."})

    history: List[dict] = body.get("history", [])
    session_id: str = body.get("sessionId") or str(uuid.uuid4())
    # Explicit UI language selection. "es" forces Spanish replies and
    # translates the query for retrieval; "en" (default) leaves the prompt's
    # auto-detect rule in charge, so any-language questions still work.
    language_code = body.get("language", "en")

    # retrieved_chunks is referenced by respond()'s debug branch and by the
    # early exits below (crisis/length/small-talk/guardrail), so it must exist
    # before the first respond() call. Real retrieval happens in Section 3.
    retrieved_chunks: List[dict] = []

    def respond(
        rtype: str,
        rmessage: str,
        *,
        citations: Optional[List[dict]] = None,
        escalation: Optional[dict] = None,
        log: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Assemble the type-discriminated contract, log, and return 200."""
        _log_interaction(
            type=rtype,
            sessionId=session_id,
            message=message,
            message_preview=(rmessage[:300] + "...") if len(rmessage) > 300 else rmessage,
            citations_count=len(citations) if citations else 0,
            escalation_office=escalation.get("office") if escalation else None,
            **(log or {}),
        )
        response_body: Dict[str, Any] = {
            "type": rtype,
            "message": rmessage,
            "sessionId": session_id,
        }
        if citations is not None:
            response_body["citations"] = citations
        if escalation is not None:
            response_body["escalation"] = escalation
        if debug_chunks and rtype != "crisis":
            response_body["debug"] = {"retrieved_chunks": retrieved_chunks}
        return _build_response(200, response_body)

    # --- 1b. Input Length Guard (before any retrieval/Bedrock calls) ---
    # Bedrock Guardrails has no native input length limit, so oversized input
    # is rejected here (as a clarify turn) before any retrieval/Bedrock call.
    if len(message) > MAX_INPUT_LENGTH:
        logger.warning("Input length guard tripped (length=%d).", len(message))
        return respond("clarify", INPUT_TOO_LONG_MESSAGE)

    # --- 2. Crisis Check (deterministic, highest priority, pre-model) ---
    safety_result = check_message(message)
    if safety_result["crisis"]:
        logger.warning("Crisis detected - bypassing LLM.")
        return respond("crisis", safety_result["crisis_response"])

    user_requested_human = safety_result["escalation"]["needed"]

    # --- 2a. Small-Talk Check (greetings/closings — before retrieval) ---
    # Pure greetings ("hi") and closings ("thanks, I'm done") aren't real
    # questions and would waste a retrieval + model round-trip. Answer them
    # here with a canned, friendly response before any Bedrock call.
    if safety_result.get("smalltalk_response"):
        return respond("answer", safety_result["smalltalk_response"], citations=None)

    # --- 2b. Guardrail Check on Raw Message (before retrieval) ---
    # Runs the Bedrock Guardrail directly on the raw message first, so
    # denied-topic / content-policy blocks apply regardless of whether the
    # message would have retrieved any relevant CSUCI passages. (No-ops when
    # no guardrail is configured.) A hard block short-circuits as a decline;
    # a masked-only intervention (e.g. PII redaction) falls through unchanged.
    early_guardrail_result = check_guardrail_only(message)
    logger.info(
        "GUARDRAIL_CHECK_EARLY: sessionId=%s intervened=%s",
        session_id,
        early_guardrail_result["intervened"],
    )
    if early_guardrail_result["intervened"]:
        logger.warning(
            "GUARDRAIL_INTERVENED_EARLY: sessionId=%s trace=%s",
            session_id,
            json.dumps(early_guardrail_result["trace"], default=str),
        )
        is_masked_only = (
            "masked" in early_guardrail_result["action_reason"].lower()
            and "blocked" not in early_guardrail_result["action_reason"].lower()
        )
        if not is_masked_only and early_guardrail_result["blocked_message"]:
            return respond(
                "decline",
                early_guardrail_result["blocked_message"],
                log={"status": "guardrail_blocked_early"},
            )
        # Masked-only (e.g. PII in the raw message itself): not a block,
        # fall through to the normal pipeline unchanged.

    # --- 3. RAG Retrieval (always — no score-floor short-circuit) ---
    # The KB is English: translate Spanish-mode queries before vector search.
    if language_code == "es":
        search_query = translate_query_to_english(message)
        logger.info(
            "Original query: '%s' -> Search query: '%s'", message, search_query
        )
    else:
        search_query = message

    retrieved_chunks = retrieve_context(search_query, top_k=5)
    top_score = retrieved_chunks[0]["score"] if retrieved_chunks else 0.0

    if debug_chunks:
        logger.info(
            "=== Retrieved %d chunk(s) for: %s ===", len(retrieved_chunks), message
        )
        for i, c in enumerate(retrieved_chunks, start=1):
            logger.info(
                "[chunk %d] score=%.4f | title=%s | url=%s\n%s\n",
                i, c["score"], c.get("source_title", ""), c.get("source_url", ""),
                c.get("text", "")[:600],
            )

    # --- 4. Build prompt & invoke the model with forced tool-use ---
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        retrieved_chunks=_format_retrieved_chunks(retrieved_chunks)
    )
    if language_code == "es":
        system_prompt += SPANISH_OVERRIDE
    converse_messages = format_messages_for_converse(history, message)

    try:
        tool_calls = invoke_model(
            system_prompt=system_prompt,
            messages=converse_messages,
            tool_config=TOOL_CONFIG,
        )
    except Exception:
        # Infrastructure failure — retryable 500, NOT an escalation.
        logger.exception("LLM invocation failed.")
        return _build_response(
            500,
            {"error": "Sorry, I am having trouble connecting to Bedrock. Please try again later."},
        )

    # Note: when a Bedrock Guardrail blocks the model's OUTPUT during the
    # Converse call, no valid tool call is produced, so tool_calls is empty
    # and the request safely falls through to fail_safe() below (human
    # handoff). Input content-safety is handled earlier by the standalone
    # early guardrail check (Section 2b).
    common_log = {
        "chunks_returned": len(retrieved_chunks),
        "top_score": top_score,
        "user_requested_human": user_requested_human,
        "tools_called": [c.get("name") for c in tool_calls],
    }

    def fail_safe(why: str) -> Dict[str, Any]:
        """Unusable model output → route the student to a human, loudly."""
        logger.error("FAIL-SAFE ESCALATION: %s (tools=%s)", why, tool_calls)
        escalation = build_escalation(
            DEFAULT_OFFICE_KEY,
            f"Automatic handoff — the assistant could not produce a usable "
            f"response ({why}).",
            message,
            session_id,
        )
        return respond(
            "escalate",
            ESCALATION_MESSAGE,
            escalation=escalation,
            log={**common_log, "fail_safe": why},
        )

    # --- 5. Structural validation (llm.py) ---
    decision = validate_decision(tool_calls)
    if decision is None:
        return fail_safe("no usable tool decision")

    primary = decision["primary"]
    escalate_call = decision["escalation"]
    primary_name = primary["name"]
    primary_input = primary.get("input") or {}

    # Build the escalation payload once, if any escalate call is present.
    escalation_payload: Optional[dict] = None
    if escalate_call is not None:
        esc_input = escalate_call.get("input") or {}
        escalation_payload = build_escalation(
            esc_input.get("office"),
            esc_input.get("reason", ""),
            message,
            session_id,
        )

    # --- 6. Policy dispatch ---
    if primary_name == ANSWER_TOOL:
        answer_text = primary_input["answer"].strip()
        citations = _resolve_citations(
            primary_input.get("citations"), retrieved_chunks
        )
        if citations is None:
            # Ungrounded answer (empty/invalid citations) — never show it.
            return fail_safe("answer with empty or out-of-range citations")

        # Backstop: student explicitly asked for a human but the model
        # answered without pairing an escalate call.
        if user_requested_human and escalation_payload is None:
            logger.info("Backstop: forcing escalation for explicit human request.")
            escalation_payload = build_escalation(
                DEFAULT_OFFICE_KEY,
                "Student explicitly asked to speak with a person.",
                message,
                session_id,
            )
        if escalation_payload is not None:
            answer_text = f"{answer_text}\n\n---\n\n{ESCALATION_ADDENDUM}"

        return respond(
            "answer",
            answer_text,
            citations=citations,
            escalation=escalation_payload,
            log=common_log,
        )

    if primary_name == CLARIFY_TOOL:
        clarify_text = primary_input["question"].strip()
        if user_requested_human:
            # Still honor the explicit human request alongside the question.
            escalation_payload = build_escalation(
                DEFAULT_OFFICE_KEY,
                "Student explicitly asked to speak with a person.",
                message,
                session_id,
            )
        return respond(
            "clarify",
            clarify_text,
            escalation=escalation_payload,
            log=common_log,
        )

    if primary_name == ESCALATE_TOOL:
        return respond(
            "escalate",
            ESCALATION_MESSAGE,
            escalation=escalation_payload,
            log=common_log,
        )

    if primary_name == DECLINE_TOOL:
        decline_reason = (primary_input.get("reason") or "").strip()
        logger.info("Declined out-of-scope question. Reason: %s", decline_reason)
        if user_requested_human:
            escalation_payload = build_escalation(
                DEFAULT_OFFICE_KEY,
                "Student explicitly asked to speak with a person.",
                message,
                session_id,
            )
        return respond(
            "decline",
            DECLINE_MESSAGE,
            escalation=escalation_payload,
            log={**common_log, "decline_reason": decline_reason},
        )

    # Unreachable if validate_decision is correct, but never crash on it.
    return fail_safe(f"unhandled primary tool '{primary_name}'")
