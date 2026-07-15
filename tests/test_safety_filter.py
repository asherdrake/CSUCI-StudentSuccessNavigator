"""
Tests for the safety_filter module.

Covers:
  - Crisis detection (suicide, self-harm, emergency keywords)
  - Safe messages that should pass through
  - Escalation detection ("talk to a person", "I need a human")
  - Edge cases (empty string, very long input, mixed case)
"""

import os
import sys

import pytest

# Ensure the Lambda source is on the path
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "lambda")
)

from safety_filter import check_message  # noqa: E402


# ---------------------------------------------------------------------------
# Crisis-keyword tests
# ---------------------------------------------------------------------------
class TestCrisisDetection:
    """Messages containing crisis/self-harm language must be flagged."""

    @pytest.mark.parametrize(
        "message",
        [
            "I'm thinking about hurting myself",
            "I want to kill myself",
            "I'm going to commit suicide",
            "I don't want to live anymore",
            "I am having thoughts of self-harm",
            "I feel like ending it all",
            "I want to hurt myself so badly",
        ],
    )
    def test_crisis_keywords_detected(self, message):
        result = check_message(message)
        assert result["crisis"] is True
        assert result["safe"] is False
        assert "crisis_response" in result
        assert result["crisis_response"] is not None

    def test_crisis_response_contains_hotline(self):
        """The crisis response should reference professional resources."""
        result = check_message("I want to kill myself")
        assert result["crisis"] is True
        response_lower = result["crisis_response"].lower()
        # Should mention at least one of: 988, hotline, crisis, counseling
        assert any(
            kw in response_lower
            for kw in ["988", "hotline", "crisis", "counseling"]
        )


# ---------------------------------------------------------------------------
# Safe-message tests
# ---------------------------------------------------------------------------
class TestSafeMessages:
    """Benign academic queries must NOT trigger crisis or escalation."""

    @pytest.mark.parametrize(
        "message",
        [
            "How do I register for classes?",
            "What is the add/drop deadline?",
            "Where is the tutoring center?",
            "How do I apply for financial aid?",
            "What are the GE requirements?",
            "Can you explain the graduation process?",
        ],
    )
    def test_safe_message_passes_through(self, message):
        result = check_message(message)
        assert result["crisis"] is False
        assert result["safe"] is True
        assert result["escalation"]["needed"] is False


# ---------------------------------------------------------------------------
# Escalation tests
# ---------------------------------------------------------------------------
class TestEscalationDetection:
    """Requests for a human advisor must be flagged as escalation."""

    @pytest.mark.parametrize(
        "message",
        [
            "I need to talk to a real person",
            "Can I speak with a human?",
            "I want to talk to an advisor",
            "Please connect me to a counselor",
            "I need a human",
            "talk to a person",
        ],
    )
    def test_escalation_detected(self, message):
        result = check_message(message)
        assert result["escalation"]["needed"] is True

    def test_escalation_not_crisis(self):
        """Escalation alone should not be flagged as a crisis."""
        result = check_message("I want to talk to a real person")
        assert result["crisis"] is False
        assert result["safe"] is True
        assert result["escalation"]["needed"] is True


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------
class TestEdgeCases:
    """Boundary conditions that should be handled gracefully."""

    def test_empty_string(self):
        result = check_message("")
        assert result["crisis"] is False
        assert result["safe"] is True
        assert result["escalation"]["needed"] is False

    def test_whitespace_only(self):
        result = check_message("     ")
        assert result["crisis"] is False
        assert result["safe"] is True
        assert result["escalation"]["needed"] is False

    def test_very_long_message(self):
        """A 10,000-character benign message should still be safe."""
        long_msg = "How do I register? " * 500
        result = check_message(long_msg)
        assert result["crisis"] is False
        assert result["safe"] is True

    def test_mixed_case_crisis(self):
        """Crisis detection should be case-insensitive."""
        result = check_message("I Want To KILL Myself")
        assert result["crisis"] is True
        assert result["safe"] is False

    def test_mixed_case_escalation(self):
        """Escalation detection should be case-insensitive."""
        result = check_message("I NEED A HUMAN")
        assert result["escalation"]["needed"] is True

    def test_gibberish(self):
        result = check_message("asdfghjkl zxcvbnm qwerty")
        assert result["crisis"] is False
        assert result["safe"] is True
        assert result["escalation"]["needed"] is False
