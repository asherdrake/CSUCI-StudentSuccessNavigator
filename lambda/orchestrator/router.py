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
        "url": "https://www.csuci.edu/financialaid/"
    },
    "advising": {
        "office": "Academic Advising",
        "phone": "805-437-8571",
        "url": "https://www.csuci.edu/advising/"
    },
    "registrar": {
        "office": "Registrar's Office",
        "phone": "805-437-8500",
        "url": "https://www.csuci.edu/registrar/"
    },
    "tutoring": {
        "office": "Learning Resource Center",
        "phone": "805-437-8409",
        "url": "https://www.csuci.edu/learningresourcecenter/"
    }
}

# Default routing destination
DEFAULT_OFFICE_KEY = "advising"


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
    combined_text = (message + " " + context).lower()
    
    # Classification matching rules
    office_key = DEFAULT_OFFICE_KEY
    if any(kw in combined_text for kw in ["financial", "fafsa", "scholarship", "loan", "grant", "aid"]):
        office_key = "financial_aid"
    elif any(kw in combined_text for kw in ["register", "add class", "drop class", "withdrawal", "transcript", "diploma", "graduation deadline", "prerequisite", "override"]):
        office_key = "registrar"
    elif any(kw in combined_text for kw in ["tutoring", "tutor", "math center", "writing center", "lrc", "study help"]):
        office_key = "tutoring"
    elif any(kw in combined_text for kw in ["advisor", "advising", "schedule advising", "major requirements", "ge requirements", "double major"]):
        office_key = "advising"

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
            "url": office_info["url"]
        },
        "ticket_draft": ticket_draft
    }
