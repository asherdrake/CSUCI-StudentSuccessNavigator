"""
Tests for the Lambda orchestrator handler.

Covers:
  - Valid message → returns answered: True, citations, escalation: null
  - Crisis message → returns crisis response, answered: True, bypasses LLM
  - Missing message field → 400 error
  - Empty body → 400 error
  - Low retrieval score → answered: False, bypasses LLM, triggers escalation
  - LLM NO_ANSWER sentinel → answered: False, triggers escalation
  - Citation validation failure → answered: False, triggers escalation
  - Escalation intent (user requested) → answered: True, appends escalation payload
"""

import json
import os
import sys
from unittest.mock import patch

import pytest

# Ensure the Lambda orchestrator source is on the path
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "lambda", "orchestrator")
)
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "lambda")
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _apigw_event(body: dict) -> dict:
    """Build a minimal API Gateway proxy integration event."""
    return {
        "httpMethod": "POST",
        "path": "/chat",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
        "isBase64Encoded": False,
        "requestContext": {},
        "pathParameters": None,
        "queryStringParameters": None,
    }


def _parse_response(response: dict) -> dict:
    """Parse the statusCode and JSON body from a Lambda proxy response."""
    return {
        "status": response["statusCode"],
        "body": json.loads(response["body"]),
    }


# ---------------------------------------------------------------------------
# Tests — valid messages
# ---------------------------------------------------------------------------
class TestValidMessage:
    """A well-formed message should return an answer and sources."""

    @patch("handler.invoke_model")
    @patch("handler.retrieve_context")
    @patch("handler.check_message")
    def test_returns_200_with_answer(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        # Safety filter — safe message
        mock_check.return_value = {
            "safe": True,
            "crisis": False,
            "crisis_response": None,
            "escalation": {"needed": False, "category": None},
        }
        # Retriever
        mock_retrieve.return_value = [
            {
                "text": "Registration opens March 1.",
                "source_url": "https://csuci.edu/registration",
                "source_title": "Registration Info",
                "score": 0.9,
            }
        ]
        # LLM (citations: must include the retrieved URL for validation)
        mock_invoke.return_value = "You can register starting March 1. See https://csuci.edu/registration"

        event = _apigw_event({"message": "How do I register?"})
        from handler import lambda_handler

        response = lambda_handler(event, {})
        parsed = _parse_response(response)

        assert parsed["status"] == 200
        assert parsed["body"]["answered"] is True
        assert "register starting March 1" in parsed["body"]["answer"]
        assert parsed["body"]["citations"] == [
            {"title": "Registration Info", "url": "https://csuci.edu/registration"}
        ]
        assert parsed["body"]["escalation"] is None


# ---------------------------------------------------------------------------
# Tests — crisis messages
# ---------------------------------------------------------------------------
class TestCrisisMessage:
    """Crisis messages must return a crisis response and skip the LLM."""

    @patch("handler.invoke_model")
    @patch("handler.retrieve_context")
    @patch("handler.check_message")
    def test_crisis_bypasses_llm(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = {
            "safe": False,
            "crisis": True,
            "crisis_response": "Please call 988 for immediate help.",
            "escalation": {"needed": False, "category": None},
        }

        event = _apigw_event({"message": "I want to hurt myself"})
        from handler import lambda_handler

        response = lambda_handler(event, {})
        parsed = _parse_response(response)

        assert parsed["status"] == 200
        assert parsed["body"]["answered"] is True
        assert "988" in parsed["body"]["answer"]
        assert parsed["body"]["citations"] == []
        assert parsed["body"]["escalation"] is None
        # LLM & Retriever should NOT have been called
        mock_invoke.assert_not_called()
        mock_retrieve.assert_not_called()


# ---------------------------------------------------------------------------
# Tests — validation
# ---------------------------------------------------------------------------
class TestValidation:
    """Requests without a 'message' field should return 400."""

    def test_missing_message_returns_400(self):
        event = _apigw_event({"not_message": "oops"})
        from handler import lambda_handler

        response = lambda_handler(event, {})
        assert response["statusCode"] == 400

    def test_empty_body_returns_400(self):
        event = _apigw_event({})
        from handler import lambda_handler

        response = lambda_handler(event, {})
        assert response["statusCode"] == 400

    def test_options_preflight_returns_200(self):
        event = {"httpMethod": "OPTIONS", "path": "/chat"}
        from handler import lambda_handler

        response = lambda_handler(event, {})
        assert response["statusCode"] == 200


# ---------------------------------------------------------------------------
# Tests — Hallucination Guardrails
# ---------------------------------------------------------------------------
class TestHallucinationGuardrails:
    """Verify that score floors, sentinel responses, and citations are validated."""

    @patch("handler.invoke_model")
    @patch("handler.retrieve_context")
    @patch("handler.check_message")
    def test_low_score_skips_llm_and_escalates(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = {
            "safe": True,
            "crisis": False,
            "crisis_response": None,
            "escalation": {"needed": False, "category": None},
        }
        # Low retrieval score (0.25 < floor of 0.35)
        mock_retrieve.return_value = [
            {
                "text": "Irrelevant info",
                "source_url": "https://csuci.edu/irrelevant",
                "source_title": "Irrelevant Page",
                "score": 0.25,
            }
        ]

        event = _apigw_event({"message": "What is the capital of France?"})
        from handler import lambda_handler

        response = lambda_handler(event, {})
        parsed = _parse_response(response)

        assert parsed["status"] == 200
        assert parsed["body"]["answered"] is False
        assert parsed["body"]["answer"] is None
        assert parsed["body"]["escalation"]["trigger"] == "no_answer"
        assert parsed["body"]["escalation"]["office"] == "Academic Advising"
        # LLM should not have been called
        mock_invoke.assert_not_called()

    @patch("handler.invoke_model")
    @patch("handler.retrieve_context")
    @patch("handler.check_message")
    def test_no_answer_sentinel_escalates(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = {
            "safe": True,
            "crisis": False,
            "crisis_response": None,
            "escalation": {"needed": False, "category": None},
        }
        # High retrieval score but LLM can't find direct answer
        mock_retrieve.return_value = [
            {
                "text": "Some general registration rules.",
                "source_url": "https://csuci.edu/reg",
                "source_title": "Rules",
                "score": 0.85,
            }
        ]
        # LLM returns exact NO_ANSWER sentinel
        mock_invoke.return_value = "NO_ANSWER"

        event = _apigw_event({"message": "How do I override physics prerequisites?"})
        from handler import lambda_handler

        response = lambda_handler(event, {})
        parsed = _parse_response(response)

        assert parsed["status"] == 200
        assert parsed["body"]["answered"] is False
        assert parsed["body"]["answer"] is None
        assert parsed["body"]["escalation"]["trigger"] == "no_answer"
        assert parsed["body"]["escalation"]["office"] == "Registrar's Office"  # routed via 'registration' context keyword

    @patch("handler.invoke_model")
    @patch("handler.retrieve_context")
    @patch("handler.check_message")
    def test_citation_validation_failure_escalates(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = {
            "safe": True,
            "crisis": False,
            "crisis_response": None,
            "escalation": {"needed": False, "category": None},
        }
        mock_retrieve.return_value = [
            {
                "text": "Official details.",
                "source_url": "https://csuci.edu/official",
                "source_title": "Official",
                "score": 0.90,
            }
        ]
        # LLM writes a fluent answer but neglects to include the retrieved URL citation
        mock_invoke.return_value = "You can request this at Sage Hall. (No link included)"

        event = _apigw_event({"message": "How do I request a card?"})
        from handler import lambda_handler

        response = lambda_handler(event, {})
        parsed = _parse_response(response)

        assert parsed["status"] == 200
        assert parsed["body"]["answered"] is False
        assert parsed["body"]["answer"] is None
        assert parsed["body"]["escalation"]["trigger"] == "no_answer"


# ---------------------------------------------------------------------------
# Tests — escalation
# ---------------------------------------------------------------------------
class TestEscalation:
    """Escalation intent (user requested) should route and return answered: True."""

    @patch("handler.invoke_model")
    @patch("handler.retrieve_context")
    @patch("handler.check_message")
    def test_user_requested_escalation_succeeds_with_escalation_payload(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = {
            "safe": True,
            "crisis": False,
            "crisis_response": None,
            "escalation": {"needed": True, "category": "academic_advising"},
        }
        mock_retrieve.return_value = [
            {
                "text": "Schedule advisor appointments online.",
                "source_url": "https://csuci.edu/advising",
                "source_title": "Advising Page",
                "score": 0.85,
            }
        ]
        mock_invoke.return_value = "Go to https://csuci.edu/advising to schedule."

        event = _apigw_event({"message": "I need to talk to an advisor"})
        from handler import lambda_handler

        response = lambda_handler(event, {})
        parsed = _parse_response(response)

        assert parsed["status"] == 200
        # The bot answered the query successfully
        assert parsed["body"]["answered"] is True
        assert "schedule" in parsed["body"]["answer"]
        # Escalation is also attached
        assert parsed["body"]["escalation"] is not None
        assert parsed["body"]["escalation"]["trigger"] == "user_requested"
        assert parsed["body"]["escalation"]["office"] == "Academic Advising"
