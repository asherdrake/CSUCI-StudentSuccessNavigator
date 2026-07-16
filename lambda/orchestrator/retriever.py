"""
Retriever module for the CSUCI Student Success Navigator.

Wraps the Amazon Bedrock Knowledge Base ``Retrieve`` API to fetch
semantically relevant passages for a student's question.

Environment variables
---------------------
- ``BEDROCK_KB_ID`` — ID of the Bedrock Knowledge Base to query.
"""

import logging
import os
from typing import Any

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Lazy-initialised client
_client = None


def _get_client():
    """Return the ``bedrock-agent-runtime`` client, creating it on first use.

    Returns:
        boto3 client for the ``bedrock-agent-runtime`` service.
    """
    global _client
    if _client is None:
        _client = boto3.client(
            "bedrock-agent-runtime",
            region_name=os.environ.get("AWS_REGION", "us-west-2"),
        )
        logger.info("bedrock-agent-runtime client initialised.")
    return _client


def _clean_web_title(url: str) -> str:
    """Extract a clean, human-readable title from a web URL path."""
    if not url:
        return "CSUCI Webpage"
    # Strip protocol and www
    clean_url = url.replace("https://", "").replace("http://", "").replace("www.", "")
    # Split path
    parts = [p for p in clean_url.split("/") if p]
    if not parts:
        return "CSUCI Homepage"
    
    # Get the last segment
    last_segment = parts[-1]
    # If the last segment is an index/home file extension, check the preceding directory name
    if last_segment.split(".")[-1] in ["html", "htm", "php", "asp", "aspx"] or last_segment == "index":
        if len(parts) > 1:
            last_segment = parts[-2]
            
    # Remove file extensions, hyphens, and underscores
    name = last_segment.rsplit(".", 1)[0].replace("-", " ").replace("_", " ")
    return name.title() if name else "CSUCI Page"


def _extract_source_metadata(
    retrieval_result: dict[str, Any],
) -> tuple[str, str]:
    """Extract source URL and title from a single retrieval result.

    The Bedrock Retrieve API nests source information under
    ``location`` → ``s3Location`` / ``webLocation`` and may include
    metadata with a title.  This helper normalises that into a
    simple ``(url, title)`` tuple.

    Args:
        retrieval_result: A single item from the ``retrievalResults``
                          list returned by the Retrieve API.

    Returns:
        A ``(source_url, source_title)`` tuple.  Values default to
        empty strings when metadata is unavailable.
    """
    location: dict = retrieval_result.get("location", {})
    source_url = ""
    source_title = ""

    # S3 location (most common for document-based KBs)
    if location.get("type") == "S3":
        s3_loc = location.get("s3Location", {})
        source_url = s3_loc.get("uri", "")
        # Derive a readable title from the S3 key if available
        s3_key = source_url.rsplit("/", 1)[-1] if source_url else ""
        source_title = s3_key.replace("_", " ").rsplit(".", 1)[0] if s3_key else ""

    # Web location
    elif location.get("type") == "WEB":
        web_loc = location.get("webLocation", {})
        source_url = web_loc.get("url", "")
        source_title = _clean_web_title(source_url)

    # Confluence / custom
    elif location.get("type") == "CONFLUENCE":
        confluence_loc = location.get("confluenceLocation", {})
        source_url = confluence_loc.get("url", "")
        source_title = _clean_web_title(source_url)

    # Override title/URL with metadata if the KB provides one
    metadata: dict = retrieval_result.get("metadata", {})
    
    if metadata.get("source_url"):
        source_url = metadata["source_url"]
    
    if metadata.get("x-amz-bedrock-kb-source-title"):
        source_title = metadata["x-amz-bedrock-kb-source-title"]
    elif metadata.get("title"):
        source_title = metadata["title"]

    return source_url, source_title


def retrieve_context(
    query: str,
    top_k: int = 5,
) -> list[dict]:
    """Retrieve relevant passages from the Bedrock Knowledge Base.

    Args:
        query:  The student's question or search query.
        top_k:  Maximum number of passages to return (default 5).

    Returns:
        A list of dicts, each with:

        - ``text``         – The retrieved passage text.
        - ``source_url``   – URL or S3 URI of the source document.
        - ``source_title`` – Human-readable title of the source.
        - ``score``        – Relevance score (float, 0–1).

        Returns an empty list on any error to ensure the orchestrator
        can still attempt an answer or inform the user gracefully.
    """
    kb_id = os.environ.get("BEDROCK_KB_ID", "")
    if not kb_id:
        logger.error("BEDROCK_KB_ID environment variable is not set.")
        return []

    try:
        response = _get_client().retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": top_k,
                }
            },
        )
    except Exception:
        logger.exception(
            "Failed to retrieve context from Bedrock Knowledge Base (KB=%s).",
            kb_id,
        )
        return []

    results: list[dict] = []
    for item in response.get("retrievalResults", []):
        text = item.get("content", {}).get("text", "")
        score = float(item.get("score", 0.0))
        source_url, source_title = _extract_source_metadata(item)

        results.append(
            {
                "text": text,
                "source_url": source_url,
                "source_title": source_title,
                "score": score,
            }
        )

    logger.info(
        "Retrieved %d passages from Knowledge Base (KB=%s) for query: %.80s...",
        len(results),
        kb_id,
        query,
    )
    return results
