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

# Make sure safety_filter and orchestrator modules are importable
_PARENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)

from safety_filter import check_message  # noqa: E402
from retriever import retrieve_context  # noqa: E402
from prompts import ESCALATION_TEMPLATE, SYSTEM_PROMPT_TEMPLATE  # noqa: E402
from llm import format_messages_for_converse, invoke_model, translate_query_to_english  # noqa: E402
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
        assistant_answer = invoke_model(
            system_prompt=system_prompt,
            messages=converse_messages,
        )
    except Exception:
        logger.exception("LLM invocation failed.")
        return _build_response(
            500,
            {"error": "Sorry, I am having trouble connecting to Bedrock. Please try again later."},
        )

    # Clean LLM output whitespace
    assistant_answer = assistant_answer.strip()

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
