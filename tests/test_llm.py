"""
Unit tests for llm.py — the Converse tool-use seam.

Covers the two jobs the module owns:
  1. extract_tool_calls: unwrapping raw Converse responses into clean
     [{name, input}] lists.
  2. validate_decision: structural validation of the tool-call combination
     (one tool, or the single allowed answer+escalate pair).
"""

from unittest.mock import MagicMock, patch

from llm import (
    contextualize_query,
    extract_tool_calls,
    format_messages_for_converse,
    validate_decision,
)
from tools import ANSWER_TOOL, CLARIFY_TOOL, DECLINE_TOOL, ESCALATE_TOOL


def _converse_response(content_blocks):
    """Build a minimal Converse response envelope around content blocks."""
    return {
        "output": {"message": {"role": "assistant", "content": content_blocks}},
        "stopReason": "tool_use",
        "usage": {"inputTokens": 100, "outputTokens": 50},
    }


class TestExtractToolCalls:
    def test_extracts_single_tool_use_block(self):
        response = _converse_response(
            [
                {
                    "toolUse": {
                        "toolUseId": "t1",
                        "name": ESCALATE_TOOL,
                        "input": {"office": "financial_aid", "reason": "aid appeal"},
                    }
                }
            ]
        )
        calls = extract_tool_calls(response)
        assert calls == [
            {
                "name": ESCALATE_TOOL,
                "input": {"office": "financial_aid", "reason": "aid appeal"},
            }
        ]

    def test_ignores_interleaved_text_blocks(self):
        response = _converse_response(
            [
                {"text": "Let me route this for you."},
                {
                    "toolUse": {
                        "toolUseId": "t1",
                        "name": DECLINE_TOOL,
                        "input": {"reason": "off-topic"},
                    }
                },
            ]
        )
        calls = extract_tool_calls(response)
        assert len(calls) == 1
        assert calls[0]["name"] == DECLINE_TOOL

    def test_extracts_the_allowed_pair(self):
        response = _converse_response(
            [
                {
                    "toolUse": {
                        "toolUseId": "t1",
                        "name": ANSWER_TOOL,
                        "input": {"answer": "Register via myCI [1].", "citations": [1]},
                    }
                },
                {
                    "toolUse": {
                        "toolUseId": "t2",
                        "name": ESCALATE_TOOL,
                        "input": {"office": "advising", "reason": "asked for advisor"},
                    }
                },
            ]
        )
        calls = extract_tool_calls(response)
        assert [c["name"] for c in calls] == [ANSWER_TOOL, ESCALATE_TOOL]

    def test_text_only_response_yields_empty_list(self):
        response = _converse_response([{"text": "I cannot use tools right now."}])
        assert extract_tool_calls(response) == []

    def test_missing_input_defaults_to_empty_dict(self):
        response = _converse_response(
            [{"toolUse": {"toolUseId": "t1", "name": DECLINE_TOOL}}]
        )
        assert extract_tool_calls(response) == [{"name": DECLINE_TOOL, "input": {}}]

    def test_empty_response_envelope(self):
        assert extract_tool_calls({}) == []


class TestValidateDecision:
    def test_single_answer_call_is_primary(self):
        calls = [
            {"name": ANSWER_TOOL, "input": {"answer": "Yes [1].", "citations": [1]}}
        ]
        decision = validate_decision(calls)
        assert decision is not None
        assert decision["primary"]["name"] == ANSWER_TOOL
        assert decision["escalation"] is None

    def test_single_escalate_call_is_both_primary_and_escalation(self):
        calls = [
            {"name": ESCALATE_TOOL, "input": {"office": "registrar", "reason": "x"}}
        ]
        decision = validate_decision(calls)
        assert decision["primary"]["name"] == ESCALATE_TOOL
        assert decision["escalation"] is calls[0]

    def test_allowed_pair_answer_plus_escalate(self):
        calls = [
            {"name": ANSWER_TOOL, "input": {"answer": "Yes [2].", "citations": [2]}},
            {"name": ESCALATE_TOOL, "input": {"office": "advising", "reason": "y"}},
        ]
        decision = validate_decision(calls)
        assert decision["primary"]["name"] == ANSWER_TOOL
        assert decision["escalation"]["name"] == ESCALATE_TOOL

    def test_pair_order_does_not_matter(self):
        calls = [
            {"name": ESCALATE_TOOL, "input": {"office": "advising", "reason": "y"}},
            {"name": ANSWER_TOOL, "input": {"answer": "Yes [1].", "citations": [1]}},
        ]
        decision = validate_decision(calls)
        assert decision["primary"]["name"] == ANSWER_TOOL

    def test_disallowed_pair_clarify_plus_decline_rejected(self):
        calls = [
            {"name": CLARIFY_TOOL, "input": {"question": "Which program?"}},
            {"name": DECLINE_TOOL, "input": {"reason": "z"}},
        ]
        assert validate_decision(calls) is None

    def test_disallowed_pair_clarify_plus_escalate_rejected(self):
        calls = [
            {"name": CLARIFY_TOOL, "input": {"question": "Which degree?"}},
            {"name": ESCALATE_TOOL, "input": {"office": "advising", "reason": "z"}},
        ]
        assert validate_decision(calls) is None

    def test_three_calls_rejected(self):
        calls = [
            {"name": ANSWER_TOOL, "input": {"answer": "A [1]", "citations": [1]}},
            {"name": ESCALATE_TOOL, "input": {"office": "advising", "reason": "y"}},
            {"name": DECLINE_TOOL, "input": {"reason": "z"}},
        ]
        assert validate_decision(calls) is None

    def test_empty_calls_rejected(self):
        assert validate_decision([]) is None

    def test_unknown_tool_rejected(self):
        calls = [{"name": "make_coffee", "input": {}}]
        assert validate_decision(calls) is None

    def test_answer_without_answer_text_rejected(self):
        calls = [{"name": ANSWER_TOOL, "input": {"citations": [1]}}]
        assert validate_decision(calls) is None

    def test_answer_with_blank_text_rejected(self):
        calls = [{"name": ANSWER_TOOL, "input": {"answer": "   ", "citations": [1]}}]
        assert validate_decision(calls) is None

    def test_answer_without_citations_list_rejected(self):
        calls = [{"name": ANSWER_TOOL, "input": {"answer": "Yes."}}]
        assert validate_decision(calls) is None

    def test_clarify_without_question_rejected(self):
        calls = [{"name": CLARIFY_TOOL, "input": {}}]
        assert validate_decision(calls) is None

    def test_escalate_without_office_is_structurally_valid(self):
        # Office coercion is handler policy, not structural validation.
        calls = [{"name": ESCALATE_TOOL, "input": {"reason": "needs a person"}}]
        assert validate_decision(calls) is not None

    def test_pair_with_malformed_answer_rejected(self):
        calls = [
            {"name": ANSWER_TOOL, "input": {"answer": "", "citations": [1]}},
            {"name": ESCALATE_TOOL, "input": {"office": "advising", "reason": "y"}},
        ]
        assert validate_decision(calls) is None


class TestFormatMessages:
    def test_wraps_history_and_appends_current(self):
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        messages = format_messages_for_converse(history, "How do I register?")
        assert messages == [
            {"role": "user", "content": [{"text": "Hi"}]},
            {"role": "assistant", "content": [{"text": "Hello!"}]},
            {"role": "user", "content": [{"text": "How do I register?"}]},
        ]

    def test_empty_history(self):
        messages = format_messages_for_converse([], "Hello")
        assert messages == [{"role": "user", "content": [{"text": "Hello"}]}]


class TestContextualizeQuery:
    def test_empty_history_returns_message_without_llm_call(self):
        with patch("llm._get_client") as mock_client:
            result = contextualize_query([], "the completion degree version")
        assert result == "the completion degree version"
        mock_client.assert_not_called()

    def test_history_only_whitespace_returns_message_without_llm_call(self):
        history = [{"role": "assistant", "content": "   "}]
        with patch("llm._get_client") as mock_client:
            result = contextualize_query(history, "tell me more")
        assert result == "tell me more"
        mock_client.assert_not_called()

    def test_rewrites_followup_using_history(self):
        history = [
            {"role": "user", "content": "CS degree lower division requirements?"},
            {"role": "assistant", "content": "Here are the on-campus CS requirements..."},
        ]
        mock_client = MagicMock()
        mock_client.converse.return_value = {
            "output": {
                "message": {
                    "content": [
                        {"text": "Computer Science B.S. Completion Degree requirements"}
                    ]
                }
            }
        }
        with patch("llm._get_client", return_value=mock_client):
            result = contextualize_query(history, "yes, the completion degree version")
        assert result == "Computer Science B.S. Completion Degree requirements"
        mock_client.converse.assert_called_once()

    def test_strips_surrounding_quotes_from_rewrite(self):
        history = [{"role": "user", "content": "prior turn"}]
        mock_client = MagicMock()
        mock_client.converse.return_value = {
            "output": {"message": {"content": [{"text": '"CS completion degree"'}]}}
        }
        with patch("llm._get_client", return_value=mock_client):
            result = contextualize_query(history, "that one")
        assert result == "CS completion degree"

    def test_falls_back_to_message_on_error(self):
        history = [{"role": "user", "content": "prior turn"}]
        mock_client = MagicMock()
        mock_client.converse.side_effect = RuntimeError("boom")
        with patch("llm._get_client", return_value=mock_client):
            result = contextualize_query(history, "that one")
        assert result == "that one"

    def test_empty_rewrite_falls_back_to_message(self):
        history = [{"role": "user", "content": "prior turn"}]
        mock_client = MagicMock()
        mock_client.converse.return_value = {
            "output": {"message": {"content": [{"text": "   "}]}}
        }
        with patch("llm._get_client", return_value=mock_client):
            result = contextualize_query(history, "that one")
        assert result == "that one"
