"""
Office directory for the CSUCI Student Success Navigator.

Formerly a keyword-based routing engine; now a pure phone book. The LLM picks
the office (via the escalate_to_office tool — see tools.py); this module only
supplies verified contact details and assembles the staff-facing ticket.

The office keys here must stay in sync with tools.OFFICE_KEYS.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Office directory (verified contact points)
OFFICES: Dict[str, Dict[str, Any]] = {
    "financial_aid": {
        "office": "Financial Aid",
        "phone": "805-437-8530",
        "url": "https://www.csuci.edu/financialaid/",
        "location": "Sage Hall, Room 1020",
        "map_url": "https://maps.google.com/?q=Sage+Hall+CSU+Channel+Islands",
    },
    "advising": {
        "office": "Academic Advising",
        "phone": "805-437-8571",
        "url": "https://www.csuci.edu/advising/",
        "location": "Sage Hall, Room 1020",
        "map_url": "https://maps.google.com/?q=Sage+Hall+CSU+Channel+Islands",
    },
    "registrar": {
        "office": "Registrar's Office",
        "phone": "805-437-8500",
        "url": "https://www.csuci.edu/registrar/",
        "location": "Sage Hall, Room 1020 (Enrollment Center)",
        "map_url": "https://maps.google.com/?q=Sage+Hall+CSU+Channel+Islands",
    },
    "tutoring": {
        "office": "Learning Resource Center",
        "phone": "805-437-8409",
        "url": "https://www.csuci.edu/learningresourcecenter/",
        "location": "Broome Library, Room 2760",
        "map_url": "https://maps.google.com/?q=John+Spoor+Broome+Library+CSU+Channel+Islands",
    },
    # Catch-all: a CSUCI matter that needs a human but fits no office above
    # (housing, parking, IT, campus life, ...).
    # TODO(team): verify this is the right triage contact — currently the main
    # campus switchboard, not a dedicated Student Services desk.
    "general_support": {
        "office": "Student Support Services",
        "phone": "805-437-8400",
        "url": "https://www.csuci.edu/",
        "location": "One University Drive, Camarillo",
        "map_url": "https://maps.google.com/?q=CSU+Channel+Islands",
    },
}

# Fail-safe destination for unusable model output and unknown office keys.
DEFAULT_OFFICE_KEY = "general_support"


def resolve_office_key(office_key: str | None) -> str:
    """Coerce a model-supplied office key to a valid directory key."""
    if office_key in OFFICES:
        return office_key
    if office_key:
        logger.warning(
            "Unknown office key %r — coercing to %s.", office_key, DEFAULT_OFFICE_KEY
        )
    return DEFAULT_OFFICE_KEY


def build_escalation(
    office_key: str | None,
    reason: str,
    message: str,
    session_id: str,
) -> Dict[str, Any]:
    """Build the escalation payload for the API response.

    Args:
        office_key: Office key chosen by the LLM (coerced if invalid).
        reason:     The LLM's staff-facing note (or a code-supplied fallback).
        message:    The student's original message, verbatim, for staff context.
        session_id: Session identifier so staff can find the conversation logs.

    Returns:
        The ``escalation`` block of the API contract.
    """
    key = resolve_office_key(office_key)
    office_info = OFFICES[key]
    logger.info("Escalation routed to office: %s", office_info["office"])

    summary = reason.strip() if reason and reason.strip() else (
        f"Student needs human assistance with: '{message[:120]}'"
    )

    return {
        "office": office_info["office"],
        "contact": {
            "phone": office_info["phone"],
            "url": office_info["url"],
            "location": office_info["location"],
            "map_url": office_info["map_url"],
        },
        "ticket_draft": {
            "summary": summary,
            "raw_message": message,
            "office": office_info["office"],
            "sessionId": session_id,
        },
    }
