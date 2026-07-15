"""
Safety filter module for the CSUCI Student Success Navigator.

Detects crisis language (self-harm, suicide, emergency) and human-escalation
intent (requests to speak with an advisor, create a ticket, etc.).

Usage:
    from safety_filter import check_message
    result = check_message("I need help with financial aid")
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Crisis detection patterns
# ---------------------------------------------------------------------------
# Each pattern is compiled with IGNORECASE so casing never matters.
# Word-boundary anchors (\b) prevent false positives on substrings.

_CRISIS_PATTERNS: list[re.Pattern] = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        # Suicidal ideation
        r"\b(i\s+want\s+to\s+(die|kill\s+myself|end\s+(it|my\s+life)))\b",
        r"\b(suicid(e|al))\b",
        r"\b(kill\s+(myself|me))\b",
        r"\b(end\s+my\s+life)\b",
        r"\b(don'?t\s+want\s+to\s+(live|be\s+alive|exist))\b",
        r"\b(no\s+reason\s+to\s+live)\b",
        r"\b(better\s+off\s+dead)\b",
        r"\b(wish\s+i\s+were?\s+dead)\b",
        r"\b(end\s+it\s+all|ending\s+it\s+all)\b",
        # Self-harm
        r"\b(self[- ]?harm(ing)?)\b",
        r"\b(cut(ting)?\s+myself)\b",
        r"\b(hurt(ing)?\s+myself)\b",
        # Emergency / violence
        r"\b(i('?m|\s+am)\s+going\s+to\s+hurt\s+(myself|someone))\b",
        r"\b(i('?m|\s+am)\s+in\s+danger)\b",
        r"\b(someone\s+is\s+(hurting|threatening)\s+me)\b",
        r"\b(i\s+feel\s+unsafe)\b",
        r"\b(please\s+help\s+me\s+now)\b",
    ]
]

# Keywords that alone are strong crisis signals
_CRISIS_KEYWORDS: set[str] = {
    "suicide",
    "suicidal",
    "self-harm",
    "selfharm",
    "kill myself",
    "end my life",
}

# ---------------------------------------------------------------------------
# Escalation detection patterns
# ---------------------------------------------------------------------------
_ESCALATION_PATTERNS: list[re.Pattern] = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\b(talk\s+to\s+(a|an)\s+(person|human|advisor|counselor|staff))\b",
        r"\b(connect\s+me\s+to\s+(a|an)\s+(advisor|counselor|person|human|staff))\b",
        r"\b(speak\s+(to|with)\s+(a|an)\s+(person|human|advisor|counselor|staff))\b",
        r"\b(i\s+need\s+help\s+from\s+(a|an)\s+(human|person|advisor|counselor|staff))\b",
        r"\b(i\s+need\s+(a|an)?\s*(human|person|advisor|counselor|staff))\b",
        r"\b(create\s+a\s+ticket)\b",
        r"\b(submit\s+a\s+ticket)\b",
        r"\b(open\s+a\s+ticket)\b",
        r"\b(real\s+(person|human))\b",
        r"\b(human\s+(agent|support|help))\b",
        r"\b(transfer\s+me)\b",
        r"\b(escalate)\b",
        r"\b(can\s+i\s+(talk|speak)\s+(to|with)\s+someone)\b",
        r"\b(i\s+want\s+to\s+(talk|speak)\s+(to|with)\s+someone)\b",
    ]
]

# Map matched intent to a category for downstream routing
_ESCALATION_CATEGORY_MAP: dict[str, str] = {
    "advisor": "academic_advising",
    "counselor": "counseling",
    "ticket": "support_ticket",
    "staff": "general_staff",
    "person": "general_staff",
    "human": "general_staff",
}

# ---------------------------------------------------------------------------
# Hardcoded crisis response
# ---------------------------------------------------------------------------
_CRISIS_RESPONSE: str = (
    "I'm really concerned about what you've shared, and I want to make sure "
    "you get the support you need right away.\n\n"
    "**If you are in immediate danger, please call 911.**\n\n"
    "Here are resources available to you:\n\n"
    "• **988 Suicide & Crisis Lifeline** — Call or text **988** (available 24/7)\n"
    "• **CSUCI Counseling Services** — Call **(805) 437-8232** "
    "(Bell Tower 1867, Mon–Fri 8 AM – 5 PM)\n"
    "• **Crisis Text Line** — Text **HOME** to **741741**\n\n"
    "You are not alone, and there are people who care about you and want to help. "
    "Please reach out to one of these resources as soon as possible."
)


def _detect_crisis(message: str) -> bool:
    """Return True if the message contains crisis language.

    Args:
        message: The raw user message.

    Returns:
        True when crisis indicators are found.
    """
    lower_message = message.lower()

    # Fast keyword check first
    for keyword in _CRISIS_KEYWORDS:
        if keyword in lower_message:
            logger.warning("Crisis keyword detected: %s", keyword)
            return True

    # Regex pattern check
    for pattern in _CRISIS_PATTERNS:
        if pattern.search(message):
            logger.warning("Crisis pattern matched: %s", pattern.pattern)
            return True

    return False


def _detect_escalation(message: str) -> dict:
    """Detect whether the user wants to be connected to a human.

    Args:
        message: The raw user message.

    Returns:
        A dict with 'needed' (bool) and 'category' (str | None).
    """
    for pattern in _ESCALATION_PATTERNS:
        match = pattern.search(message)
        if match:
            matched_text = match.group(0).lower()
            logger.info("Escalation intent detected: %s", matched_text)

            # Determine category from the matched text
            category: Optional[str] = None
            for token, cat in _ESCALATION_CATEGORY_MAP.items():
                if token in matched_text:
                    category = cat
                    break
            category = category or "general_staff"

            return {"needed": True, "category": category}

    return {"needed": False, "category": None}


def check_message(message: str) -> dict:
    """Run all safety checks on an incoming user message.

    This is the single entry-point for the safety-filter module.  It performs
    crisis detection first (highest priority), then escalation detection.

    Args:
        message: The raw text sent by the user.

    Returns:
        A dict with the following shape::

            {
                "safe": bool,           # False only when crisis detected
                "crisis": bool,
                "crisis_response": str | None,
                "escalation": {
                    "needed": bool,
                    "category": str | None   # e.g. "academic_advising"
                }
            }
    """
    if not message or not message.strip():
        logger.debug("Empty message received — treating as safe.")
        return {
            "safe": True,
            "crisis": False,
            "crisis_response": None,
            "escalation": {"needed": False, "category": None},
        }

    # --- Crisis check (highest priority) ---
    crisis_detected = _detect_crisis(message)
    if crisis_detected:
        logger.warning("Crisis detected in message. Returning safe response.")
        return {
            "safe": False,
            "crisis": True,
            "crisis_response": _CRISIS_RESPONSE,
            "escalation": {"needed": False, "category": None},
        }

    # --- Escalation check ---
    escalation = _detect_escalation(message)

    return {
        "safe": True,
        "crisis": False,
        "crisis_response": None,
        "escalation": escalation,
    }
