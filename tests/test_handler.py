"""
Unit tests for the Lambda orchestrator handler (tool-use contract).

The LLM is mocked at the invoke_model seam: it returns parsed
[{"name": ..., "input": ...}] tool calls (llm.py owns Converse parsing, tested
in test_llm.py). These tests cover policy dispatch and the API contract:

  - answer            → type "answer", passage numbers resolved to sources
  - clarify           → type "clarify", question as message
  - escalate          → type "escalate", contact card + ticket from reason
  - decline           → type "decline", canned message (model text internal)
  - answer + escalate → the one allowed pair
  - crisis            → type "crisis", pre-model bypass
  - fail-safe policy  → unusable output routes to general_support
  - backstop          → explicit human request always yields an escalation
  - infra errors      → HTTP 500, not an escalation
"""

import json
from unittest.mock import patch

import pytest

from handler import lambda_handler


@pytest.fixture(autouse=True)
def _guardrail_not_intervened():
    """The handler runs a Bedrock Guardrail input check on every non-crisis
    request. Default it to "not intervened" so the tool-use tests below never
    attempt a real AWS call; the guardrail-specific tests patch it explicitly.
    """
    with patch(
        "handler.check_guardrail_only",
        return_value={
            "intervened": False,
            "action_reason": "",
            "blocked_message": "",
            "trace": {},
        },
    ):
        yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAFE = {
    "safe": True,
    "crisis": False,
    "crisis_response": None,
    "escalation": {"needed": False, "category": None},
}

WANTS_HUMAN = {
    "safe": True,
    "crisis": False,
    "crisis_response": None,
    "escalation": {"needed": True, "category": "academic_advising"},
}

CHUNKS = [
    {
        "text": "Registration opens March 1 through myCI.",
        "source_url": "https://csuci.edu/registration",
        "source_title": "Registration Guide",
        "score": 0.82,
    },
    {
        "text": "The FAFSA school code is 039803.",
        "source_url": "https://csuci.edu/fafsa",
        "source_title": "FAFSA Info",
        "score": 0.71,
    },
    {
        "text": "Registration dates are listed in the academic calendar.",
        "source_url": "https://csuci.edu/registration",
        "source_title": "Registration Guide",
        "score": 0.65,
    },
]


def _event(message="How do I register?", history=None, session_id="sess-1"):
    return {
        "httpMethod": "POST",
        "body": json.dumps(
            {"message": message, "history": history or [], "sessionId": session_id}
        ),
    }


def _body(response):
    assert response["statusCode"] == 200, response
    return json.loads(response["body"])


def _answer_call(answer="Register via myCI starting March 1 [1].", citations=None, buildings_mentioned=None):
    inp = {"answer": answer, "citations": citations if citations is not None else [1]}
    if buildings_mentioned is not None:
        inp["buildings_mentioned"] = buildings_mentioned
    return {
        "name": "answer_from_context",
        "input": inp,
    }


def _escalate_call(office="advising", reason="Student asked for an advisor."):
    return {"name": "escalate_to_office", "input": {"office": office, "reason": reason}}


# ---------------------------------------------------------------------------
# Answer path
# ---------------------------------------------------------------------------


@patch("handler.invoke_model")
@patch("handler.retrieve_context")
@patch("handler.check_message")
class TestAnswerPath:
    def test_answer_resolves_passage_numbers_to_sources(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [_answer_call(citations=[1, 2])]

        body = _body(lambda_handler(_event(), None))

        assert body["type"] == "answer"
        assert "March 1" in body["message"]
        assert body["citations"] == [
            {"title": "Registration Guide", "url": "https://csuci.edu/registration", "passages": [1]},
            {"title": "FAFSA Info", "url": "https://csuci.edu/fafsa", "passages": [2]},
        ]
        assert "escalation" not in body

    def test_duplicate_sources_dedupe_and_merge_passages(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        # Passages 1 and 3 share the same source URL+title.
        mock_invoke.return_value = [_answer_call(citations=[1, 3])]

        body = _body(lambda_handler(_event(), None))

        assert body["citations"] == [
            {"title": "Registration Guide", "url": "https://csuci.edu/registration", "passages": [1, 3]},
        ]

    def test_answered_flag_is_gone(self, mock_check, mock_retrieve, mock_invoke):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [_answer_call()]

        body = _body(lambda_handler(_event(), None))
        assert "answered" not in body
        assert "answer" not in body  # old field name; text is in "message"

    def test_session_id_passthrough(self, mock_check, mock_retrieve, mock_invoke):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [_answer_call()]

        body = _body(lambda_handler(_event(session_id="my-session"), None))
        assert body["sessionId"] == "my-session"


# ---------------------------------------------------------------------------
# The allowed pair: answer + escalate
# ---------------------------------------------------------------------------


@patch("handler.invoke_model")
@patch("handler.retrieve_context")
@patch("handler.check_message")
class TestAnswerEscalatePair:
    def test_pair_returns_answer_with_escalation_sidecar(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [_answer_call(), _escalate_call(office="advising")]

        body = _body(lambda_handler(_event(), None))

        assert body["type"] == "answer"
        assert body["citations"]
        assert body["escalation"]["office"] == "Academic Advising"
        assert body["escalation"]["contact"]["phone"] == "805-437-8571"
        assert (
            body["escalation"]["ticket_draft"]["summary"]
            == "Student asked for an advisor."
        )

    def test_ticket_carries_raw_message_and_session(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [_answer_call(), _escalate_call()]

        body = _body(
            lambda_handler(_event(message="Help me register", session_id="s-9"), None)
        )
        ticket = body["escalation"]["ticket_draft"]
        assert ticket["raw_message"] == "Help me register"
        assert ticket["sessionId"] == "s-9"


# ---------------------------------------------------------------------------
# Clarify path
# ---------------------------------------------------------------------------


@patch("handler.invoke_model")
@patch("handler.retrieve_context")
@patch("handler.check_message")
class TestClarifyPath:
    def test_clarify_question_becomes_message(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [
            {
                "name": "ask_clarification",
                "input": {"question": "Do you mean the B.S. or the Completion Degree?"},
            }
        ]

        body = _body(lambda_handler(_event("CS degree requirements?"), None))

        assert body["type"] == "clarify"
        assert body["message"] == "Do you mean the B.S. or the Completion Degree?"
        assert "citations" not in body
        assert "escalation" not in body


# ---------------------------------------------------------------------------
# Escalate path
# ---------------------------------------------------------------------------


@patch("handler.invoke_model")
@patch("handler.retrieve_context")
@patch("handler.check_message")
class TestEscalatePath:
    def test_escalate_builds_contact_card_and_ticket(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [
            _escalate_call(office="financial_aid", reason="Aid appeal needs a counselor.")
        ]

        body = _body(lambda_handler(_event("I lost my scholarship"), None))

        assert body["type"] == "escalate"
        assert body["message"]  # code-owned lead-in, non-empty
        assert body["escalation"]["office"] == "Financial Aid"
        assert body["escalation"]["contact"]["map_url"]
        assert body["escalation"]["ticket_draft"]["summary"] == "Aid appeal needs a counselor."

    def test_unknown_office_coerced_to_general_support(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [_escalate_call(office="housing_office")]

        body = _body(lambda_handler(_event("Can I have a pet in the dorms?"), None))

        assert body["type"] == "escalate"
        assert body["escalation"]["office"] == "Student Support Services"

    def test_missing_office_coerced_to_general_support(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [
            {"name": "escalate_to_office", "input": {"reason": "needs a person"}}
        ]

        body = _body(lambda_handler(_event(), None))
        assert body["escalation"]["office"] == "Student Support Services"

    def test_empty_reason_gets_fallback_summary(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [_escalate_call(office="registrar", reason="")]

        body = _body(lambda_handler(_event("transcript problem"), None))
        assert "transcript problem" in body["escalation"]["ticket_draft"]["summary"]


# ---------------------------------------------------------------------------
# Language preference (explicit UI selection)
# ---------------------------------------------------------------------------


@patch("handler.translate_query_to_english")
@patch("handler.invoke_model")
@patch("handler.retrieve_context")
@patch("handler.check_message")
class TestLanguagePreference:
    def _event_with_language(self, language):
        return {
            "httpMethod": "POST",
            "body": json.dumps(
                {"message": "¿Dónde está la biblioteca?", "language": language}
            ),
        }

    def test_spanish_translates_query_for_retrieval(
        self, mock_check, mock_retrieve, mock_invoke, mock_translate
    ):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_translate.return_value = "Where is the library?"
        mock_invoke.return_value = [
            _answer_call(answer="La biblioteca está en Broome [1].", citations=[1])
        ]

        body = _body(lambda_handler(self._event_with_language("es"), None))

        assert body["type"] == "answer"
        assert "biblioteca" in body["message"]
        mock_translate.assert_called_once_with("¿Dónde está la biblioteca?")
        # Retrieval must use the TRANSLATED query (the KB is English).
        mock_retrieve.assert_called_once_with("Where is the library?", top_k=5)

    def test_spanish_appends_language_override_to_system_prompt(
        self, mock_check, mock_retrieve, mock_invoke, mock_translate
    ):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_translate.return_value = "Where is the library?"
        mock_invoke.return_value = [_answer_call()]

        lambda_handler(self._event_with_language("es"), None)

        system_prompt = mock_invoke.call_args.kwargs["system_prompt"]
        assert "Language override" in system_prompt
        assert "Spanish" in system_prompt

    def test_english_default_skips_translation_and_override(
        self, mock_check, mock_retrieve, mock_invoke, mock_translate
    ):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [_answer_call()]

        lambda_handler(_event("Where is the library?"), None)

        mock_translate.assert_not_called()
        system_prompt = mock_invoke.call_args.kwargs["system_prompt"]
        assert "selected English in the interface" in system_prompt
        assert "selected Spanish" not in system_prompt


@patch("handler.invoke_model")
@patch("handler.retrieve_context")
@patch("handler.check_message")
class TestLocationLinkResolution:
    def test_answer_resolves_location_links_in_english(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [
            _answer_call(
                answer="Academic Advising is in Sage Hall.",
                citations=[1],
                buildings_mentioned=["sage_hall", "broome_library"],
            )
        ]

        body = _body(lambda_handler(_event("Where is advising?"), None))

        assert body["type"] == "answer"
        assert "Campus Map link(s):" in body["message"]
        assert "[Sage Hall](https://maps.google.com/?q=Sage+Hall+CSU+Channel+Islands)" in body["message"]
        assert "[John Spoor Broome Library](https://maps.google.com/?q=John+Spoor+Broome+Library+CSU+Channel+Islands)" in body["message"]

    def test_answer_resolves_location_links_in_spanish(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [
            _answer_call(
                answer="Advising está en Sage.",
                citations=[1],
                buildings_mentioned=["sage_hall"],
            )
        ]

        event = {
            "httpMethod": "POST",
            "body": json.dumps({"message": "¿Dónde está Sage?", "language": "es"}),
        }
        body = _body(lambda_handler(event, None))

        assert body["type"] == "answer"
        assert "Enlace del mapa del campus:" in body["message"]
        assert "[Sage Hall](https://maps.google.com/?q=Sage+Hall+CSU+Channel+Islands)" in body["message"]


# ---------------------------------------------------------------------------
# Decline path
# ---------------------------------------------------------------------------


@patch("handler.invoke_model")
@patch("handler.retrieve_context")
@patch("handler.check_message")
class TestDeclinePath:
    def test_decline_uses_canned_message_not_model_text(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = []
        mock_invoke.return_value = [
            {
                "name": "decline_out_of_scope",
                "input": {"reason": "off-topic: bicycle repair"},
            }
        ]

        body = _body(lambda_handler(_event("How do I fix a flat tire?"), None))

        assert body["type"] == "decline"
        assert "CSUCI topics" in body["message"]
        assert "bicycle" not in body["message"]  # internal reason never shown
        assert "escalation" not in body


# ---------------------------------------------------------------------------
# Crisis path (unchanged behavior, new contract)
# ---------------------------------------------------------------------------


@patch("handler.invoke_model")
@patch("handler.retrieve_context")
@patch("handler.check_message")
class TestCrisisPath:
    def test_crisis_bypasses_llm_and_retrieval(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = {
            "safe": False,
            "crisis": True,
            "crisis_response": "Please call 988 now.",
            "escalation": {"needed": False, "category": None},
        }

        body = _body(lambda_handler(_event("I want to hurt myself"), None))

        assert body["type"] == "crisis"
        assert "988" in body["message"]
        mock_invoke.assert_not_called()
        mock_retrieve.assert_not_called()


# ---------------------------------------------------------------------------
# Fail-safe policy: unusable model output → human handoff
# ---------------------------------------------------------------------------


@patch("handler.invoke_model")
@patch("handler.retrieve_context")
@patch("handler.check_message")
class TestFailSafePolicy:
    def _assert_fail_safe(self, body):
        assert body["type"] == "escalate"
        assert body["escalation"]["office"] == "Student Support Services"

    def test_no_tool_calls(self, mock_check, mock_retrieve, mock_invoke):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = []
        self._assert_fail_safe(_body(lambda_handler(_event(), None)))

    def test_unknown_tool(self, mock_check, mock_retrieve, mock_invoke):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [{"name": "make_coffee", "input": {}}]
        self._assert_fail_safe(_body(lambda_handler(_event(), None)))

    def test_disallowed_combo(self, mock_check, mock_retrieve, mock_invoke):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [
            {"name": "ask_clarification", "input": {"question": "Which one?"}},
            {"name": "decline_out_of_scope", "input": {"reason": "x"}},
        ]
        self._assert_fail_safe(_body(lambda_handler(_event(), None)))

    def test_answer_with_empty_citations(self, mock_check, mock_retrieve, mock_invoke):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [_answer_call(citations=[])]
        self._assert_fail_safe(_body(lambda_handler(_event(), None)))

    def test_answer_with_out_of_range_citation(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS  # 3 chunks
        mock_invoke.return_value = [_answer_call(citations=[1, 7])]
        self._assert_fail_safe(_body(lambda_handler(_event(), None)))

    def test_answer_with_non_integer_citation(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [_answer_call(citations=["the registration guide"])]
        self._assert_fail_safe(_body(lambda_handler(_event(), None)))

    def test_answer_with_zero_retrieved_chunks(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        # Zero chunks retrieved: any citation is out of range, so an answer
        # attempt can never be grounded — must fail safe.
        mock_check.return_value = SAFE
        mock_retrieve.return_value = []
        mock_invoke.return_value = [_answer_call(citations=[1])]
        self._assert_fail_safe(_body(lambda_handler(_event(), None)))


# ---------------------------------------------------------------------------
# Backstop: explicit human request always produces an escalation
# ---------------------------------------------------------------------------


@patch("handler.invoke_model")
@patch("handler.retrieve_context")
@patch("handler.check_message")
class TestHumanRequestBackstop:
    def test_answer_without_pair_gets_forced_escalation(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = WANTS_HUMAN
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [_answer_call()]  # model forgot to pair

        body = _body(
            lambda_handler(_event("How do I register? I want to talk to someone."), None)
        )

        assert body["type"] == "answer"
        assert body["escalation"]["office"] == "Student Support Services"

    def test_model_pair_takes_precedence_over_backstop(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = WANTS_HUMAN
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [_answer_call(), _escalate_call(office="advising")]

        body = _body(lambda_handler(_event(), None))
        # The model's office choice wins; backstop only fills the gap.
        assert body["escalation"]["office"] == "Academic Advising"

    def test_decline_with_human_request_still_escalates(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = WANTS_HUMAN
        mock_retrieve.return_value = []
        mock_invoke.return_value = [
            {"name": "decline_out_of_scope", "input": {"reason": "gibberish"}}
        ]

        body = _body(lambda_handler(_event("asdfgh! give me a human"), None))
        assert body["type"] == "decline"
        assert body["escalation"]["office"] == "Student Support Services"


# ---------------------------------------------------------------------------
# Request validation & infra errors
# ---------------------------------------------------------------------------


class TestRequestValidation:
    def test_missing_message_returns_400(self):
        response = lambda_handler({"httpMethod": "POST", "body": json.dumps({})}, None)
        assert response["statusCode"] == 400

    def test_empty_body_returns_400(self):
        response = lambda_handler({"httpMethod": "POST", "body": None}, None)
        assert response["statusCode"] == 400

    def test_invalid_json_returns_400(self):
        response = lambda_handler({"httpMethod": "POST", "body": "{not json"}, None)
        assert response["statusCode"] == 400

    def test_options_preflight_returns_200(self):
        response = lambda_handler({"httpMethod": "OPTIONS"}, None)
        assert response["statusCode"] == 200


@patch("handler.invoke_model")
@patch("handler.retrieve_context")
@patch("handler.check_message")
class TestInfraErrors:
    def test_bedrock_failure_returns_500_not_escalation(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = SAFE
        mock_retrieve.return_value = CHUNKS
        mock_invoke.side_effect = RuntimeError("throttled")

        response = lambda_handler(_event(), None)
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body
        assert "escalation" not in body


# ---------------------------------------------------------------------------
# Input length guard (merged from guardrails, adapted to the new contract)
# ---------------------------------------------------------------------------


@patch("handler.invoke_model")
@patch("handler.retrieve_context")
@patch("handler.check_message")
class TestInputLengthGuard:
    def test_oversized_message_clarifies_before_any_bedrock_call(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = SAFE
        body = _body(lambda_handler(_event("x " * 800), None))  # > 1000 chars

        assert body["type"] == "clarify"
        assert "shorten" in body["message"]
        # Runs before crisis/retrieval/model — none of those should fire.
        mock_check.assert_not_called()
        mock_retrieve.assert_not_called()
        mock_invoke.assert_not_called()


# ---------------------------------------------------------------------------
# Small-talk (merged from guardrails, adapted to the new contract)
# ---------------------------------------------------------------------------

SMALLTALK = {
    "safe": True,
    "crisis": False,
    "crisis_response": None,
    "escalation": {"needed": False, "category": None},
    "smalltalk_response": "Hi there! 👋 Ask me anything about CSUCI.",
}


@patch("handler.invoke_model")
@patch("handler.retrieve_context")
@patch("handler.check_message")
class TestSmallTalk:
    def test_greeting_answers_without_retrieval_or_model(
        self, mock_check, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = SMALLTALK

        body = _body(lambda_handler(_event("hi"), None))

        assert body["type"] == "answer"
        assert body["message"] == SMALLTALK["smalltalk_response"]
        assert "citations" not in body
        assert "escalation" not in body
        mock_retrieve.assert_not_called()
        mock_invoke.assert_not_called()


# ---------------------------------------------------------------------------
# Early Bedrock Guardrail check on the raw message (merged from guardrails)
# ---------------------------------------------------------------------------


@patch("handler.invoke_model")
@patch("handler.retrieve_context")
@patch("handler.check_guardrail_only")
@patch("handler.check_message")
class TestEarlyGuardrail:
    def test_hard_block_declines_before_retrieval_or_model(
        self, mock_check, mock_guardrail, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = SAFE
        mock_guardrail.return_value = {
            "intervened": True,
            "action_reason": "Guardrail blocked.",
            "blocked_message": "I can't help with that. Let's keep it focused on CSUCI.",
            "trace": {"contentPolicy": {"filters": [{"type": "INSULTS"}]}},
        }

        body = _body(lambda_handler(_event("you are an idiot"), None))

        assert body["type"] == "decline"
        assert body["message"] == "I can't help with that. Let's keep it focused on CSUCI."
        mock_retrieve.assert_not_called()
        mock_invoke.assert_not_called()

    def test_masked_only_continues_to_retrieval_and_model(
        self, mock_check, mock_guardrail, mock_retrieve, mock_invoke
    ):
        mock_check.return_value = SAFE
        # PII masking, not a hard block — must NOT short-circuit.
        mock_guardrail.return_value = {
            "intervened": True,
            "action_reason": "No action.\nGuardrail masked.",
            "blocked_message": "",
            "trace": {},
        }
        mock_retrieve.return_value = CHUNKS
        mock_invoke.return_value = [_answer_call()]

        body = _body(
            lambda_handler(_event("my email is a@b.com, how do I register?"), None)
        )

        assert body["type"] == "answer"
        mock_retrieve.assert_called_once()
        mock_invoke.assert_called_once()
