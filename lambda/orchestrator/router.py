"""
Routing engine for the CSUCI Student Success Navigator.

Maps query content and retrieved context keywords to the correct target
department office, providing contact info and drafting human agent tickets.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Topic-to-Office directory mapping (verified contact points)
OFFICES: Dict[str, Dict[str, Any]] = {
    "financial_aid": {
        "office": "Financial Aid",
        "phone": "805-437-8530",
        "url": "https://www.csuci.edu/financialaid/",
        "location": "Sage Hall, Room 1020",
        "map_url": "https://maps.google.com/?q=Sage+Hall+CSU+Channel+Islands"
    },
    "advising": {
        "office": "Academic Advising",
        "phone": "805-437-8571",
        "url": "https://www.csuci.edu/advising/",
        "location": "Sage Hall, Room 1020",
        "map_url": "https://maps.google.com/?q=Sage+Hall+CSU+Channel+Islands"
    },
    "registrar": {
        "office": "Registrar's Office",
        "phone": "805-437-8500",
        "url": "https://www.csuci.edu/registrar/",
        "location": "Sage Hall, Room 1020 (Enrollment Center)",
        "map_url": "https://maps.google.com/?q=Sage+Hall+CSU+Channel+Islands"
    },
    "tutoring": {
        "office": "Learning Resource Center",
        "phone": "805-437-8409",
        "url": "https://www.csuci.edu/learningresourcecenter/",
        "location": "Broome Library, Room 2760",
        "map_url": "https://maps.google.com/?q=John+Spoor+Broome+Library+CSU+Channel+Islands"
    }
}

# Default routing destination
DEFAULT_OFFICE_KEY = "advising"


import re

def _has_keyword(text: str, keywords: list[str]) -> bool:
    """Check if the text contains any of the keywords as distinct words."""
    for kw in keywords:
        # Match using word boundaries (\b) to prevent partial substring matches
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def route_query(message: str, context: str = "") -> Dict[str, Any]:
    """Classify the target office based on query keywords and context.

    Generates contact information and a ticket draft containing a summary
    and the context surrounding why the request escalated to a human.

    Args:
        message: The student's original query.
        context: The text context retrieved from Bedrock KB (if any).

    Returns:
        Dict conforming to the 'escalation' block in the API contract.
    """
    message_lower = message.lower()
    context_lower = context.lower()
    
    # 1. Define keyword categories
    fa_keywords = ["financial", "fafsa", "scholarship", "scholarships", "loan", "loans", "grant", "grants", "aid"]
    reg_keywords = ["register", "registration", "add class", "drop class", "withdrawal", "transcript", "transcripts", "diploma", "graduation", "prerequisite", "override", "records"]
    tutor_keywords = ["tutoring", "tutor", "tutors", "math center", "writing center", "lrc", "study help"]
    adv_keywords = ["advisor", "advisors", "advising", "schedule advising", "major requirements", "ge requirements", "double major", "academic requirements"]

    # 2. Check the user's message first (highest accuracy)
    office_key = None
    if _has_keyword(message_lower, fa_keywords):
        office_key = "financial_aid"
    elif _has_keyword(message_lower, reg_keywords):
        office_key = "registrar"
    elif _has_keyword(message_lower, tutor_keywords):
        office_key = "tutoring"
    elif _has_keyword(message_lower, adv_keywords):
        office_key = "advising"
        
    # 3. Fallback to check context if message was inconclusive
    if not office_key:
        if _has_keyword(context_lower, fa_keywords):
            office_key = "financial_aid"
        elif _has_keyword(context_lower, reg_keywords):
            office_key = "registrar"
        elif _has_keyword(context_lower, tutor_keywords):
            office_key = "tutoring"
        elif _has_keyword(context_lower, adv_keywords):
            office_key = "advising"
        else:
            office_key = DEFAULT_OFFICE_KEY

    office_info = OFFICES[office_key]
    logger.info("Routed query to office: %s", office_info["office"])

    # Draft a clean ticket description for the human advisor
    summary = f"Student is asking: '{message}'"
    if len(summary) > 120:
        summary = summary[:117] + "..."

    ticket_draft = {
        "summary": summary,
        "context": (
            f"Escalated target office: {office_info['office']}. "
            f"Query context: '{message}'. "
            f"System matches this category for specialized human support."
        )
    }

    return {
        "trigger": "no_answer",  # default, handler overrides if user_requested
        "office": office_info["office"],
        "contact": {
            "phone": office_info["phone"],
            "url": office_info["url"],
            "location": office_info["location"],
            "map_url": office_info["map_url"]
        },
        "ticket_draft": ticket_draft
    }
