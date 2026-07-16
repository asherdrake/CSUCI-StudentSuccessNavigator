"""
LLM invocation module for the CSUCI Student Success Navigator.

Wraps Amazon Bedrock's **Converse** API to communicate with Claude 3.5
Sonnet.  The Converse API is preferred over raw ``InvokeModel`` because
it provides a model-agnostic message interface with built-in token
management.

Environment variables
---------------------
- ``MODEL_ID`` — Bedrock model identifier.  Defaults to
  ``meta.llama3-70b-instruct-v1:0``.
"""

import logging
import os
import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_MODEL_ID: str = os.environ.get(
    "MODEL_ID",
    "meta.llama3-70b-instruct-v1:0",
)

# Lazy-initialised client
_client = None


def _get_client():
    """Return the ``bedrock-runtime`` client, creating it on first use.

    Returns:
        boto3 client for the ``bedrock-runtime`` service.
    """
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime")
        logger.info("bedrock-runtime client initialised.")
    return _client


def format_messages_for_converse(
    conversation_history: list[dict],
    current_user_message: str,
) -> list[dict]:
    """Convert internal session turns into Bedrock Converse message format.

    The Bedrock Converse API expects messages in this shape::

        [
            {"role": "user",      "content": [{"text": "..."}]},
            {"role": "assistant", "content": [{"text": "..."}]},
            ...
        ]

    Our client-passed history stores each turn as::

        {"role": "user"|"assistant", "content": "..."}

    This helper wraps the ``content`` string in the required ``[{"text": ...}]``
    list structure, then appends the current user message at the end.
    To prevent context token limit overflow on Bedrock, we only retain
    the last 10 turns (5 user-assistant exchanges) of history.

    Args:
        conversation_history: Prior turns passed directly from the client.
        current_user_message: The latest message from the student.

    Returns:
        A list of messages in Bedrock Converse format.
    """
    messages: list[dict] = []

    # Retain only the last 10 turns to avoid exceeding the 8192 context token limit
    pruned_history = (
        conversation_history[-10:]
        if len(conversation_history) > 10
        else conversation_history
    )

    for turn in pruned_history:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        messages.append(
            {
                "role": role,
                "content": [{"text": content}],
            }
        )

    # Append the current user message
    messages.append(
        {
            "role": "user",
            "content": [{"text": current_user_message}],
        }
    )

    return messages


def invoke_model(
    system_prompt: str,
    messages: list[dict],
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> str:
    """Invoke Claude 3.5 Sonnet via the Bedrock Converse API.

    Args:
        system_prompt: The system-level instruction prompt (built from
            :data:`prompts.SYSTEM_PROMPT_TEMPLATE`).
        messages:      Conversation messages in Bedrock Converse format
            (as returned by :func:`format_messages_for_converse`).
        temperature:   Sampling temperature (0–1).  Lower values produce
            more deterministic answers.  Default ``0.3``.
        max_tokens:    Maximum tokens in the response.  Default ``1024``.

    Returns:
        The assistant's text response as a plain string.

    Raises:
        Exception: Re-raised after logging if the Bedrock call fails.
    """
    try:
        response = _get_client().converse(
            modelId=_MODEL_ID,
            system=[{"text": system_prompt}],
            messages=messages,
            inferenceConfig={
                "temperature": temperature,
                "maxTokens": max_tokens,
            },
        )
    except Exception:
        logger.exception(
            "Failed to invoke Bedrock model %s via Converse API.", _MODEL_ID
        )
        raise

    # Extract assistant text from the response
    output_message = response.get("output", {}).get("message", {})
    content_blocks = output_message.get("content", [])

    # The Converse API may return multiple content blocks; concatenate all
    # text blocks into a single string.
    assistant_text = "".join(
        block.get("text", "")
        for block in content_blocks
        if "text" in block
    )

    if not assistant_text:
        logger.warning("Bedrock Converse returned an empty response.")

    # Log token usage for cost monitoring
    usage = response.get("usage", {})
    logger.info(
        "Bedrock Converse usage — input_tokens: %s, output_tokens: %s",
        usage.get("inputTokens", "N/A"),
        usage.get("outputTokens", "N/A"),
    )

    return assistant_text


def translate_query_to_english(query: str) -> str:
    """Translate the student's query to English to optimize vector search.

    If already in English, it returns the query unchanged.
    """
    system_prompt = (
        "You are a translation helper. Translate the user's message into plain English. "
        "If it is already in English, return it exactly as is. "
        "Output ONLY the final English translation text, with no introduction, no surrounding quotes, and no extra notes."
    )
    messages = [
        {
            "role": "user",
            "content": [{"text": query}]
        }
    ]
    try:
        translation = invoke_model(
            system_prompt=system_prompt,
            messages=messages,
            temperature=0.0,
            max_tokens=64
        )
        return translation.strip().strip('"').strip("'")
    except Exception:
        logger.warning("Query translation failed, falling back to original text.")
        return query
