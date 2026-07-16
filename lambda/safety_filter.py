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
# Small-talk detection (greetings / closings)
# ---------------------------------------------------------------------------
# Matched only against the ENTIRE message (after stripping trailing
# punctuation), not as a substring search — this is deliberately narrow so it
# only catches messages that are purely a greeting/closing, not a real
# question that happens to start with "hi" (e.g. "hi, how do I register?").
_GREETING_PATTERNS: list[re.Pattern] = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"^(hi|hello|hey|hiya|yo)$",
        r"^(hi|hello|hey)\s+there$",
        r"^good\s+(morning|afternoon|evening)$",
        r"^what'?s\s+up$",
    ]
]

_CLOSING_PATTERNS: list[re.Pattern] = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"^(bye|goodbye|see\s+you|see\s+ya)$",
        r"^thanks?(\s+you)?$",
        r"^thank\s+you$",
        r"^(thanks|thank\s+you)[,!\s]*(for\s+(the|your)\s+help)?$",
        r"^i('?m|\s+am)\s+(done|good|all\s+set)[,!\s]*(thanks?( you)?( for( the| your)? help)?)?$",
        r"^that'?s\s+all[,!\s]*(thanks?( you)?)?$",
        r"^that\s+(helps?|answers?\s+my\s+question)[,!\s]*(thanks?( you)?)?$",
        # "thanks" and "I'm done" combined in either order, plus optional
        # trailing filler like "cool" / "great" / "awesome".
        r"^thanks?[,!\s]+i('?m|\s+am)\s+(done|good|all\s+set)[,!\s]*(cool|great|awesome)?$",
        r"^i('?m|\s+am)\s+(done|good|all\s+set)[,!\s]+thanks?[,!\s]*(cool|great|awesome)?$",
        # Casual acknowledgments — deliberately excludes short filler like
        # "ok"/"cool"/"okay"/"alright" that students commonly use as a
        # mid-conversation continuer ("ok, and what about...") rather than
        # an ending; only phrases unambiguous enough to signal "I'm done"
        # are included here.
        r"^(gotcha|got\s+it|sounds\s+good|makes\s+sense)$",
    ]
]

_GREETING_RESPONSE: str = (
    "Hi there! 👋 I'm the CSUCI Student Success Navigator. "
    "Ask me anything about registration, advising, financial aid, graduation, or campus support."
)

_CLOSING_RESPONSE: str = (
    "You're welcome! Feel free to come back anytime you have more questions. Good luck! 🎓"
)


def _detect_smalltalk(message: str) -> Optional[str]:
    """Return a canned response if the message is purely a greeting or
    closing, else None.

    Args:
        message: The raw user message.

    Returns:
        The canned response string, or None if this isn't small talk.
    """
    normalized = message.strip().rstrip(".!?").strip()
    if not normalized:
        return None

    for pattern in _GREETING_PATTERNS:
        if pattern.match(normalized):
            return _GREETING_RESPONSE

    for pattern in _CLOSING_PATTERNS:
        if pattern.match(normalized):
            return _CLOSING_RESPONSE

    return None

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
                },
                "smalltalk_response": str | None,  # set for pure greetings/closings
            }
    """
    if not message or not message.strip():
        logger.debug("Empty message received — treating as safe.")
        return {
            "safe": True,
            "crisis": False,
            "crisis_response": None,
            "escalation": {"needed": False, "category": None},
            "smalltalk_response": None,
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
            "smalltalk_response": None,
        }

    # --- Escalation check ---
    escalation = _detect_escalation(message)

    # --- Small-talk check (only relevant when not escalating to a human) ---
    smalltalk_response = None if escalation["needed"] else _detect_smalltalk(message)

    return {
        "safe": True,
        "crisis": False,
        "crisis_response": None,
        "escalation": escalation,
        "smalltalk_response": smalltalk_response,
    }
