"""
Shared pytest fixtures for the Student Success Navigator test suite.
"""

import os
import sys

import pytest

# ---------------------------------------------------------------------------
# Path helpers — let every test file import the Lambda modules directly.
# ---------------------------------------------------------------------------
LAMBDA_DIR = os.path.join(os.path.dirname(__file__), "..", "lambda")
ORCHESTRATOR_DIR = os.path.join(LAMBDA_DIR, "orchestrator")
sys.path.insert(0, LAMBDA_DIR)
sys.path.insert(0, ORCHESTRATOR_DIR)


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    """Set required environment variables for every test."""
    monkeypatch.setenv("BEDROCK_KB_ID", "test-kb-id")
    monkeypatch.setenv("MODEL_ID", "us.anthropic.claude-sonnet-5")
    monkeypatch.setenv("GUARDRAIL_ID", "test-guardrail-id")
    monkeypatch.setenv("GUARDRAIL_VERSION", "DRAFT")
    monkeypatch.setenv("SNS_TOPIC_ARN", "arn:aws:sns:us-west-2:123456789012:test-topic")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-2")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
