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
        "map_url": "https://maps.google.com/?q=Sage+Hall+CSU+Channel+Islands",
        "reason": "This request is routed to the Financial Aid office because it concerns FAFSA, scholarships, grants, loans, work-study programs, or fee waivers."
    },
    "advising": {
        "office": "Academic Advising",
        "phone": "805-437-8571",
        "url": "https://www.csuci.edu/advising/",
        "location": "Sage Hall, Room 1020",
        "map_url": "https://maps.google.com/?q=Sage+Hall+CSU+Channel+Islands",
        "reason": "This request is routed to Academic Advising because it requires guidance on major/minor plans, GE requirements, degree planners, or transfer credits."
    },
    "registrar": {
        "office": "Registrar's Office",
        "phone": "805-437-8500",
        "url": "https://www.csuci.edu/registrar/",
        "location": "Sage Hall, Room 1020 (Enrollment Center)",
        "map_url": "https://maps.google.com/?q=Sage+Hall+CSU+Channel+Islands",
        "reason": "This request is routed to the Registrar's Office because it involves registration holds, transcript requests, graduation applications, add/drop limits, or enrollment records."
    },
    "tutoring": {
        "office": "Learning Resource Center",
        "phone": "805-437-8409",
        "url": "https://www.csuci.edu/learningresourcecenter/",
        "location": "Broome Library, Room 2760",
        "map_url": "https://maps.google.com/?q=John+Spoor+Broome+Library+CSU+Channel+Islands",
        "reason": "This request is routed to the Learning Resource Center (LRC) because it involves tutoring availability, peer mentoring, study skills, or academic workshops."
    }
}

# Default routing destination
DEFAULT_OFFICE_KEY = "advising"


import re

def _score_office(text: str, keywords: list[str]) -> int:
    """Count the total occurrences of the keywords as distinct words in the text."""
    count = 0
    for kw in keywords:
        pattern = r'\b' + re.escape(kw) + r'\b'
        count += len(re.findall(pattern, text, re.IGNORECASE))
    return count

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
    
    # 1. Define expanded keyword categories (English and Spanish)
    fa_keywords = [
        "financial", "fafsa", "scholarship", "scholarships", "loan", "loans", 
        "grant", "grants", "aid", "dream act", "work-study", "tuition", "fees", "sap", "waiver", "waivers",
        "ayuda", "financiera", "beca", "becas", "préstamo", "préstamos", "gratis"
    ]
    reg_keywords = [
        "register", "registration", "add class", "drop class", "withdrawal", 
        "transcript", "transcripts", "diploma", "graduation", "prerequisite", 
        "override", "records", "hold", "holds", "grade", "grades", "gpa", "probation", "catalog", "verification",
        "registro", "registrar", "inscribirse", "inscribir", "clases", "calificaciones", "notas", "retirada"
    ]
    tutor_keywords = [
        "tutoring", "tutor", "tutors", "math center", "writing center", 
        "lrc", "study help", "homework", "workshop", "workshops", "study skills", "peer mentor",
        "tutoría", "tutorias", "tareas", "estudiar"
    ]
    adv_keywords = [
        "advisor", "advisors", "advising", "schedule advising", "major requirements", 
        "ge requirements", "double major", "academic requirements", "minor", "minors", 
        "transfer credits", "degree planner", "academic plan", "course plan",
        "consejero", "consejeros", "consejería", "asesor", "asesores", "asesoría", "requisitos"
    ]

    # 2. Score the user's direct message first (highest relevance)
    message_scores = {
        "financial_aid": _score_office(message_lower, fa_keywords),
        "registrar": _score_office(message_lower, reg_keywords),
        "tutoring": _score_office(message_lower, tutor_keywords),
        "advising": _score_office(message_lower, adv_keywords)
    }
    
    best_message_office = max(message_scores, key=message_scores.get)
    
    if message_scores[best_message_office] > 0:
        office_key = best_message_office
    else:
        # 3. Fallback: Score the retrieved context
        context_scores = {
            "financial_aid": _score_office(context_lower, fa_keywords),
            "registrar": _score_office(context_lower, reg_keywords),
            "tutoring": _score_office(context_lower, tutor_keywords),
            "advising": _score_office(context_lower, adv_keywords)
        }
        best_context_office = max(context_scores, key=context_scores.get)
        if context_scores[best_context_office] > 0:
            office_key = best_context_office
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
            f"Escalated office: {office_info['office']}. "
            f"Reason: {office_info['reason']} "
            f"Query context: '{message}'."
        )
    }

    return {
        "trigger": "no_answer",  # default, handler overrides if user_requested
        "office": office_info["office"],
        "reason": office_info["reason"],
        "contact": {
            "phone": office_info["phone"],
            "url": office_info["url"],
            "location": office_info["location"],
            "map_url": office_info["map_url"]
        },
        "ticket_draft": ticket_draft
    }
