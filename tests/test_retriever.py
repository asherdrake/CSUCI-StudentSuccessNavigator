"""
Tests for the retriever module (Bedrock Knowledge Base lookups).

Covers:
  - Successful retrieval returns formatted context chunks
  - Empty result set is handled gracefully
  - ClientError from Bedrock returns an empty list (no crash)
  - Result text and scores are extracted correctly

Uses unittest.mock.patch to mock the boto3 bedrock-agent-runtime client.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

# Ensure the Lambda source is on the path
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "lambda")
)

import retriever  # noqa: E402
from retriever import retrieve_context  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_retrieval_result(text: str, score: float = 0.85, uri: str = "s3://bucket/doc.pdf"):
    """Build a single RetrievalResult dict matching the Bedrock response shape."""
    return {
        "content": {"text": text},
        "score": score,
        "location": {"type": "S3", "s3Location": {"uri": uri}},
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestRetrieveContext:
    """Test the retrieve_context function."""

    @pytest.fixture(autouse=True)
    def reset_lazy_client(self):
        """Force the lazy-loaded client to re-initialize for every test mock."""
        retriever._client = None
        yield
        retriever._client = None

    @patch("retriever.boto3")
    def test_successful_retrieval(self, mock_boto3):
        """Valid response → list of context dicts with text, score, source."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.retrieve.return_value = {
            "retrievalResults": [
                _make_retrieval_result("Registration opens in March.", 0.92, "s3://docs/reg.pdf"),
                _make_retrieval_result("Add/drop deadline is week 2.", 0.88, "s3://docs/cal.pdf"),
            ]
        }

        results = retrieve_context("How do I register?")

        assert len(results) == 2
        assert results[0]["text"] == "Registration opens in March."
        assert results[0]["score"] == 0.92
        assert "reg" in results[0]["source_title"].lower()
        assert results[0]["source_url"] == "s3://docs/reg.pdf"

    @patch("retriever.boto3")
    def test_empty_results(self, mock_boto3):
        """No matching documents → empty list, no error."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.retrieve.return_value = {"retrievalResults": []}

        results = retrieve_context("some obscure question")
        assert results == []

    @patch("retriever.boto3")
    def test_client_error_returns_empty_list(self, mock_boto3):
        """Bedrock ClientError → empty list (graceful degradation)."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.retrieve.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Denied"}},
            "Retrieve",
        )

        results = retrieve_context("anything")
        assert results == []

    @patch("retriever.boto3")
    def test_result_scores_are_floats(self, mock_boto3):
        """Scores returned by retrieve_context should be numeric."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.retrieve.return_value = {
            "retrievalResults": [
                _make_retrieval_result("text", 0.75),
            ]
        }

        results = retrieve_context("query")
        assert isinstance(results[0]["score"], float)

    @patch("retriever.boto3")
    def test_multiple_results_order_preserved(self, mock_boto3):
        """Results should be returned in the same order Bedrock returns them."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.retrieve.return_value = {
            "retrievalResults": [
                _make_retrieval_result("First", 0.95),
                _make_retrieval_result("Second", 0.80),
                _make_retrieval_result("Third", 0.70),
            ]
        }

        results = retrieve_context("query")
        assert [r["text"] for r in results] == ["First", "Second", "Third"]
