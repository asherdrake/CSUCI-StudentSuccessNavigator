"""
Lambda orchestrator handler for the CSUCI Student Success Navigator.

Processes student messages through safety checks, RAG retrieval (with score floor),
unanswered sentinels, citation validation, and dynamic escalation routing.
All interactions are logged in structured JSON to CloudWatch for observability.
"""

import json
import logging
import os
import sys
import uuid
from typing import Any, Dict, List

# Make sure safety_filter (lambda/) and sibling orchestrator modules
# (retriever, prompts, llm, router — lambda/orchestrator/) are importable
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.join(_THIS_DIR, "..")
for _path in (_PARENT_DIR, _THIS_DIR):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from safety_filter import check_message  # noqa: E402
from retriever import retrieve_context  # noqa: E402
from prompts import ESCALATION_TEMPLATE, SYSTEM_PROMPT_TEMPLATE  # noqa: E402
from llm import check_guardrail_only, format_messages_for_converse, invoke_model, translate_query_to_english  # noqa: E402
from router import route_query  # noqa: E402

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# CORS response headers
_CORS_HEADERS: Dict[str, str] = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
    "Content-Type": "application/json",
}

# Score threshold floor for RAG matches
SCORE_FLOOR = 0.40

# Fallback clarification text to prompt student before ticket creation
CLARIFICATION_TEXT = (
    "I'm sorry, I couldn't find enough matching information about that in our database. "
    "Could you please rephrase or provide a bit more details so I can find the right info?"
)

# Bedrock Guardrails has no native input length limit (confirmed against the
# Converse API schema), so oversized input is rejected here before any
# retrieval or Bedrock call is made, to save cost/latency.
MAX_INPUT_LENGTH = 1000


def _validate_input_length(user_message: str) -> Dict[str, Any] | None:
    """Return an early-return response body if the message is too long, else None."""
    if len(user_message) > MAX_INPUT_LENGTH:
        return {
            "answered": False,
            "answer": (
                "That message is a bit long — could you shorten it to a specific "
                "question? I can help best with focused questions about CSUCI resources."
            ),
        }
    return None


def _has_already_clarified(history: List[dict]) -> bool:
    """Scan history from bottom up to see if the last bot response was a clarification prompt."""
    for turn in reversed(history):
        if turn.get("role") == "assistant":
            return turn.get("content") == CLARIFICATION_TEXT
    return False


def _build_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Return an API Gateway proxy-integration response dict."""
    return {
        "statusCode": status_code,
        "headers": _CORS_HEADERS,
        "body": json.dumps(body, default=str),
    }


def _format_retrieved_chunks(chunks: List[dict]) -> str:
    """Format RAG context passages into a readable block for the LLM prompt."""
    if not chunks:
        return "(No relevant context was found in the knowledge base.)"

    lines: List[str] = []
    for i, chunk in enumerate(chunks, start=1):
        title = chunk.get("source_title", "Unknown Source")
        url = chunk.get("source_url", "")
        text = chunk.get("text", "").strip()
        # Truncate extremely long scraped roadmap pages to prevent token limits overflow
        if len(text) > 2500:
            text = text[:2500] + "\n... [truncated for length] ..."
        source_ref = f"[{title}]({url})" if url else title
        lines.append(f"**Passage {i}** (source: {source_ref}):\n{text}")

    return "\n\n".join(lines)


def _extract_unique_sources(chunks: List[dict]) -> List[Dict[str, str]]:
    """Return deduplicated list of source metadata from chunks."""
    seen_urls = set()
    sources = []
    for chunk in chunks:
        url = chunk.get("source_url", "")
        title = chunk.get("source_title", "Unknown Source")
        if url and url not in seen_urls:
            seen_urls.add(url)
            sources.append({"title": title, "url": url})
    return sources


def _validate_citations(answer: str, sources: List[Dict[str, str]]) -> bool:
    """Verify that an answered response contains at least one retrieved URL citation.

    Protects against the LLM inventing facts outside our KB sources.
    """
    if not sources:
        return False
    
    # Check if the answer text references any of the retrieved source URLs
    for src in sources:
        url = src.get("url", "")
        if url and url in answer:
            return True
    return False


def _log_interaction(
    *,
    status: str,
    message: str,
    answered: bool,
    safety_result: dict,
    chunks_count: int,
    top_score: float,
    answer: str | None,
    citations: list,
    escalation: dict | None,
    session_id: str
) -> None:
    """Log the request details to CloudWatch in a structured JSON schema."""
    logger.info(
        json.dumps(
            {
                "interaction": {
                    "status": status,
                    "sessionId": session_id,
                    "message": message,
                    "answered": answered,
                    "safety": {
                        "crisis": safety_result.get("crisis", False),
                        "user_requested_escalation": safety_result.get("escalation", {}).get("needed", False)
                    },
                    "retrieval": {
                        "chunks_returned": chunks_count,
                        "top_score": top_score
                    },
                    "answer_preview": (answer[:300] + "...") if answer else None,
                    "citations_count": len(citations),
                    "escalation_office": escalation.get("office") if escalation else None,
                    "escalation_trigger": escalation.get("trigger") if escalation else None
                }
            }
        )
    )


# ---------------------------------------------------------------------------
# Lambda Handler
# ---------------------------------------------------------------------------


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda entry point for the Student Success Navigator."""
    logger.info("Received event: %s", json.dumps(event, default=str))

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

    # Client-passed multi-turn history & session identifier
    history: List[dict] = body.get("history", [])
    session_id: str = body.get("sessionId") or str(uuid.uuid4())
    language_code = body.get("language", "en")
    target_language = "Spanish" if language_code == "es" else "English"

    # --- 1b. Input Length Guard (before any retrieval/Bedrock calls) ---
    length_guard_result = _validate_input_length(message)
    if length_guard_result is not None:
        logger.warning("Input length guard tripped (length=%d).", len(message))
        return _build_response(
            200,
            {
                **length_guard_result,
                "citations": [],
                "escalation": None,
                "sessionId": session_id,
            },
        )

    # --- 2. Crisis Check (Highest Priority pre-model filter) ---
    safety_result = check_message(message)
    if safety_result["crisis"]:
        logger.warning("Crisis detected - bypassing LLM.")
        crisis_answer = safety_result["crisis_response"]
        _log_interaction(
            status="crisis",
            message=message,
            answered=True,
            safety_result=safety_result,
            chunks_count=0,
            top_score=0.0,
            answer=crisis_answer,
            citations=[],
            escalation=None,
            session_id=session_id
        )
        return _build_response(
            200,
            {
                "answer": crisis_answer,
                "answered": True,
                "citations": [],
                "escalation": None,
                "sessionId": session_id,
            },
        )

    # --- 2a. Small-Talk Check (greetings/closings — before RAG/score-floor) ---
    # Pure greetings ("hi") and closings ("thanks, I'm done") aren't real
    # questions, so they always score below the KB-relevance floor (Section
    # 4) and would otherwise get treated as "couldn't find info" or even
    # escalated to a support ticket on a second turn. Handled here instead
    # with a canned, friendly response, before any retrieval/Bedrock call.
    if safety_result.get("smalltalk_response"):
        smalltalk_answer = safety_result["smalltalk_response"]
        _log_interaction(
            status="smalltalk",
            message=message,
            answered=True,
            safety_result=safety_result,
            chunks_count=0,
            top_score=0.0,
            answer=smalltalk_answer,
            citations=[],
            escalation=None,
            session_id=session_id,
        )
        return _build_response(
            200,
            {
                "answer": smalltalk_answer,
                "answered": True,
                "citations": [],
                "escalation": None,
                "sessionId": session_id,
            },
        )

    # --- 2b. Guardrail Check on Raw Message (before RAG/score-floor) ---
    # The main Converse-call guardrail check (below, Section 6) only runs if
    # the message passes the KB-relevance score floor (Section 4) — messages
    # unrelated to CSUCI content (off-topic, abusive, etc.) often score below
    # that floor and would otherwise never reach the guardrail at all. This
    # runs the guardrail directly on the raw message first, independent of
    # KB relevance, so denied-topic/content-policy blocks apply regardless.
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
            blocked_message = early_guardrail_result["blocked_message"]
            _log_interaction(
                status="guardrail_blocked_early",
                message=message,
                answered=True,
                safety_result=safety_result,
                chunks_count=0,
                top_score=0.0,
                answer=blocked_message,
                citations=[],
                escalation=None,
                session_id=session_id,
            )
            return _build_response(
                200,
                {
                    "answer": blocked_message,
                    "answered": True,
                    "citations": [],
                    "escalation": None,
                    "sessionId": session_id,
                },
            )
        # Masked-only (e.g. PII in the raw message itself): not a block,
        # fall through to the normal pipeline unchanged.

    # --- 3. RAG Retrieval ---
    if language_code == "es":
        search_query = translate_query_to_english(message)
    else:
        search_query = message

    logger.info("Original query: '%s' -> Search query: '%s'", message, search_query)
    retrieved_chunks = retrieve_context(search_query, top_k=3)
    top_score = retrieved_chunks[0]["score"] if retrieved_chunks else 0.0

    # Extract unique source list
    citations = _extract_unique_sources(retrieved_chunks)

    # --- 4. Hallucination Guardrail 1: Score Floor check ---
    if not retrieved_chunks or top_score < SCORE_FLOOR:
        logger.warning(
            "Low retrieval score (top_score=%f < floor=%f) - checking clarification loop.",
            top_score,
            SCORE_FLOOR,
        )
        
        if _has_already_clarified(history):
            # Already clarified once, perform full human escalation
            context_text = (
                f"Zero matching passages retrieved." if not retrieved_chunks
                else f"Top match score was {top_score:.4f} which is below the floor of {SCORE_FLOOR}."
            )
            escalation_payload = route_query(message, context_text)
            escalation_payload["trigger"] = "no_answer"
            
            if safety_result["escalation"]["needed"]:
                escalation_payload["trigger"] = "user_requested"

            _log_interaction(
                status="low_score_escalate",
                message=message,
                answered=False,
                safety_result=safety_result,
                chunks_count=len(retrieved_chunks),
                top_score=top_score,
                answer=None,
                citations=[],
                escalation=escalation_payload,
                session_id=session_id
            )
            return _build_response(
                200,
                {
                    "answer": None,
                    "answered": False,
                    "citations": [],
                    "escalation": escalation_payload,
                    "sessionId": session_id,
                },
            )
        else:
            # First turn failure, prompt for clarification
            _log_interaction(
                status="low_score_clarify",
                message=message,
                answered=True,
                safety_result=safety_result,
                chunks_count=len(retrieved_chunks),
                top_score=top_score,
                answer=CLARIFICATION_TEXT,
                citations=[],
                escalation=None,
                session_id=session_id
            )
            return _build_response(
                200,
                {
                    "answer": CLARIFICATION_TEXT,
                    "answered": True,
                    "citations": [],
                    "escalation": None,
                    "sessionId": session_id,
                },
            )

    # --- 5. Build system prompt ---
    formatted_chunks = _format_retrieved_chunks(retrieved_chunks)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        retrieved_chunks=formatted_chunks,
        conversation_history="(Conversation history managed client-side.)",
        target_language=target_language
    )

    # --- 6. Invoke LLM (Claude 3.5 Sonnet, temp=0.2) ---
    converse_messages = format_messages_for_converse(history, message)

    try:
        llm_result = invoke_model(
            system_prompt=system_prompt,
            messages=converse_messages,
        )
    except Exception:
        logger.exception("LLM invocation failed.")
        return _build_response(
            500,
            {"error": "Sorry, I am having trouble connecting to Bedrock. Please try again later."},
        )

    logger.info(
        "GUARDRAIL_CHECK: sessionId=%s stopReason=%s",
        session_id,
        llm_result.get("stop_reason"),
    )
    if llm_result.get("stop_reason") == "guardrail_intervened":
        guardrail_trace = llm_result.get("trace", {})
        logger.warning(
            "GUARDRAIL_INTERVENED: sessionId=%s trace=%s",
            session_id,
            json.dumps(guardrail_trace, default=str),
        )

        # Bedrock reports both hard blocks and PII masking via the same
        # stopReason; only a hard block should short-circuit here — masking
        # just redacts sensitive text in-place and the (redacted) answer
        # should continue through the normal pipeline below.
        action_reason = guardrail_trace.get("actionReason", "")
        is_masked_only = "masked" in action_reason.lower() and "blocked" not in action_reason.lower()

        if not is_masked_only:
            blocked_message = llm_result["text"].strip()
            _log_interaction(
                status="guardrail_blocked",
                message=message,
                answered=True,
                safety_result=safety_result,
                chunks_count=len(retrieved_chunks),
                top_score=top_score,
                answer=blocked_message,
                citations=[],
                escalation=None,
                session_id=session_id,
            )
            return _build_response(
                200,
                {
                    "answer": blocked_message,
                    "answered": True,
                    "citations": [],
                    "escalation": None,
                    "sessionId": session_id,
                },
            )

    # Clean LLM output whitespace
    assistant_answer = llm_result["text"].strip()

    # --- 7. Hallucination Guardrail 2: NO_ANSWER Sentinel Check ---
    if assistant_answer == "NO_ANSWER":
        logger.warning("LLM returned NO_ANSWER sentinel. Checking clarification loop.")
        
        if _has_already_clarified(history):
            # Already clarified, perform human escalation
            escalation_payload = route_query(message, formatted_chunks)
            escalation_payload["trigger"] = "no_answer"
            
            if safety_result["escalation"]["needed"]:
                escalation_payload["trigger"] = "user_requested"

            _log_interaction(
                status="sentinel_escalate",
                message=message,
                answered=False,
                safety_result=safety_result,
                chunks_count=len(retrieved_chunks),
                top_score=top_score,
                answer=None,
                citations=[],
                escalation=escalation_payload,
                session_id=session_id
            )
            return _build_response(
                200,
                {
                    "answer": None,
                    "answered": False,
                    "citations": [],
                    "escalation": escalation_payload,
                    "sessionId": session_id,
                },
            )
        else:
            # First turn failure, prompt for clarification
            _log_interaction(
                status="sentinel_clarify",
                message=message,
                answered=True,
                safety_result=safety_result,
                chunks_count=len(retrieved_chunks),
                top_score=top_score,
                answer=CLARIFICATION_TEXT,
                citations=[],
                escalation=None,
                session_id=session_id
            )
            return _build_response(
                200,
                {
                    "answer": CLARIFICATION_TEXT,
                    "answered": True,
                    "citations": [],
                    "escalation": None,
                    "sessionId": session_id,
                },
            )

    # --- 8. Hallucination Guardrail 3: Citation Validation Check ---
    if not _validate_citations(assistant_answer, citations):
        logger.warning(
            "Citation validation failed (Answer contains no URLs from citations). Checking clarification loop."
        )
        
        if _has_already_clarified(history):
            # Already clarified, perform human escalation
            escalation_payload = route_query(message, formatted_chunks)
            escalation_payload["trigger"] = "no_answer"
            
            if safety_result["escalation"]["needed"]:
                escalation_payload["trigger"] = "user_requested"

            _log_interaction(
                status="citation_validation_failed_escalate",
                message=message,
                answered=False,
                safety_result=safety_result,
                chunks_count=len(retrieved_chunks),
                top_score=top_score,
                answer=None,
                citations=[],
                escalation=escalation_payload,
                session_id=session_id
            )
            return _build_response(
                200,
                {
                    "answer": None,
                    "answered": False,
                    "citations": [],
                    "escalation": escalation_payload,
                    "sessionId": session_id,
                },
            )
        else:
            # First turn failure, prompt for clarification
            _log_interaction(
                status="citation_validation_clarify",
                message=message,
                answered=True,
                safety_result=safety_result,
                chunks_count=len(retrieved_chunks),
                top_score=top_score,
                answer=CLARIFICATION_TEXT,
                citations=[],
                escalation=None,
                session_id=session_id
            )
            return _build_response(
                200,
                {
                    "answer": CLARIFICATION_TEXT,
                    "answered": True,
                    "citations": [],
                    "escalation": None,
                    "sessionId": session_id,
                },
            )

    # --- 9. Check Safety Handoff / User-Requested Escalation ---
    # Append physical location details to final text answer if user asked for locations/maps and it is missing
    location_keywords = ["location", "address", "map", "maps", "directions", "where is", "located", "room number"]
    if assistant_answer and any(kw in message.lower() for kw in location_keywords) and "maps.google.com" not in assistant_answer:
        answer_lower = assistant_answer.lower()
        
        # Parse which building is referenced to generate an accurate maps query
        location_name = "CSUCI Campus"
        map_query = "California+State+University+Channel+Islands"
        
        if "sage hall" in answer_lower or "sage" in answer_lower:
            location_name = "Sage Hall"
            map_query = "Sage+Hall+CSU+Channel+Islands"
        elif "broome library" in answer_lower or "broome" in answer_lower or "library" in answer_lower:
            location_name = "John Spoor Broome Library"
            map_query = "John+Spoor+Broome+Library+CSU+Channel+Islands"
        elif "beacon hall" in answer_lower or "beacon" in answer_lower:
            location_name = "Beacon Hall"
            map_query = "Beacon+Hall+CSU+Channel+Islands"
        elif "bell tower" in answer_lower:
            location_name = "Bell Tower"
            map_query = "Bell+Tower+CSU+Channel+Islands"
            
        assistant_answer += (
            f"\n\n**Location Directions:**\n"
            f"View building location on the map: [{location_name} Google Maps Link](https://maps.google.com/?q={map_query})"
        )

    escalation_payload = None
    if safety_result["escalation"]["needed"]:
        # If student asked for a human, route to the right office but keep answered=True
        # because the LLM successfully generated a valid, cited answer for the rest of the message.
        escalation_payload = route_query(message, formatted_chunks)
        escalation_payload["trigger"] = "user_requested"
        assistant_answer = f"{assistant_answer}\n\n---\n\n{ESCALATION_TEMPLATE}"

    # Log successful execution to CloudWatch
    _log_interaction(
        status="success",
        message=message,
        answered=True,
        safety_result=safety_result,
        chunks_count=len(retrieved_chunks),
        top_score=top_score,
        answer=assistant_answer,
        citations=citations,
        escalation=escalation_payload,
        session_id=session_id
    )

    return _build_response(
        200,
        {
            "answer": assistant_answer,
            "answered": True,
            "citations": citations,
            "escalation": escalation_payload,
            "sessionId": session_id,
        },
    )
