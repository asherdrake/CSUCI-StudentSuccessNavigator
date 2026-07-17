"""
Client demo test runner for the CSUCI Student Success Navigator.

Sends every question in EkhoQuestions.txt to the REAL deployed API endpoint
(not the in-process handler — this hits the actual public URL, exactly as a
real user's browser would), and logs the complete raw request/response for
each one. This is deliberately NOT a pass/fail scorecard like eval/run_eval.py
— EkhoQuestions.txt has no answer key, and many of its questions require
access to a specific student's real data (their FAFSA status, their specific
degree audit, etc.), which this system does not have. The point here is to
produce a complete, honest transcript for the client: what was asked, what
came back, verbatim.

Each question is also tagged against the six capabilities the client asked
us to demonstrate, based on its section in EkhoQuestions.txt and/or keyword
matching on its text (see CAPABILITY_RULES below). A question can match
more than one capability.

Usage (needs live AWS credentials — hits the real deployed endpoint):
    python eval/run_client_demo.py
    python eval/run_client_demo.py --url https://.../prod/chat
    python eval/run_client_demo.py --limit 5       # smoke-test a few first
    python eval/run_client_demo.py --delay 1.5     # seconds between requests

Output: eval/results/client_demo_log.json — one entry per question with the
full request sent, the full response received, timing, HTTP status, and its
capability tags. Also prints a running summary of the capability totals to
the console as it goes, and a section-by-section index at the end.
"""

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUESTIONS_PATH = os.path.join(PROJECT_ROOT, "EkhoQuestions.txt")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "eval", "results")
RESULTS_PATH = os.path.join(RESULTS_DIR, "client_demo_log.json")

DEFAULT_URL = "https://8ajq5s89ye.execute-api.us-west-2.amazonaws.com/prod/chat"

# ---------------------------------------------------------------------------
# Capability tagging
# ---------------------------------------------------------------------------
# Each rule is (capability_name, matcher). A question can match several.
# Section-based rules are the primary signal (the client's own document
# already groups questions by intent); keyword rules catch cross-cutting
# cases the section alone wouldn't (e.g. a Financial Aid question that's
# also a multi-step "what do I do next" question).

CAPABILITIES = [
    "natural_language",
    "resource_recommendations",
    "guided_workflow_graduation",
    "contextual_suggestions",
    "multi_step_handling",
    "source_summarization",
]


_RESOURCE_SECTIONS = (
    "Campus Resources",
    "Health & Wellness",
    "Accessibility",
    "Career Services",
    "Housing",
    "Campus Life",
    "Technology",
)
_GRADUATION_SECTIONS = ("Degree Planning", "Graduation")


def _section_rules(section: str) -> list[str]:
    """Section may be composite, e.g. "Campus Resources / Health & Wellness"
    (a sub-header folded in during parsing) — match by substring, not
    equality, so either half of a composite name is enough to tag it."""
    tags = ["natural_language"]  # every question exercises NL understanding
    if any(s in section for s in _RESOURCE_SECTIONS):
        tags.append("resource_recommendations")
    if any(s in section for s in _GRADUATION_SECTIONS):
        tags.append("guided_workflow_graduation")
    if "Personalized Prompts" in section:
        tags.append("contextual_suggestions")
    if "Stretch Goals" in section:
        tags += ["contextual_suggestions", "multi_step_handling"]
    return tags


_MULTI_STEP_PATTERNS = [
    r"\bplan\b", r"\bchecklist\b", r"\bsteps?\b", r"\bfastest path\b",
    r"\bwhat should i do\b", r"\bhow do i (apply|accept|declare|register)\b",
    r"\bbefore (my first|next|registration)\b",
]
_CONTEXTUAL_PATTERNS = [
    r"\bbased on\b", r"\bi('m| am)\b.*\b(struggling|overwhelmed|working|planning|missed)\b",
    r"\bam i on track\b", r"\brecommend\b", r"\bwhich office\b",
]
_SOURCE_SUMMARY_PATTERNS = [
    r"\bsummarize\b", r"\bexplain\b", r"\bin plain english\b", r"\bpolicy\b",
]
_RESOURCE_REC_PATTERNS = [
    r"\bwhere (can|do) i\b", r"\bhow do i (get|find|access|connect)\b",
    r"\bwhat resources\b", r"\brecommend\b",
]


def tag_capabilities(section: str, question: str) -> list[str]:
    tags = set(_section_rules(section))
    q = question.lower()

    def any_match(patterns: list[str]) -> bool:
        return any(re.search(p, q) for p in patterns)

    if any_match(_MULTI_STEP_PATTERNS):
        tags.add("multi_step_handling")
    if any_match(_CONTEXTUAL_PATTERNS):
        tags.add("contextual_suggestions")
    if any_match(_SOURCE_SUMMARY_PATTERNS):
        tags.add("source_summarization")
    if any_match(_RESOURCE_REC_PATTERNS):
        tags.add("resource_recommendations")
    if "graduat" in q or "degree" in q:
        tags.add("guided_workflow_graduation")

    # Preserve a stable, readable order rather than set iteration order.
    return [c for c in CAPABILITIES if c in tags]


# ---------------------------------------------------------------------------
# Question file parsing
# ---------------------------------------------------------------------------
# EkhoQuestions.txt mixes indentation-as-structure with inconsistent
# formatting (e.g. "Health & Wellness" and "Career Services" are sub-headers
# but indented exactly like the questions around them, and "Stretch Goals"
# questions are quoted and don't all end in "?" — e.g. "Compare these two
# majors for me."). Indentation alone can't disambiguate these, so a line is
# classified as a QUESTION only if it looks like one — ends in "?", or (for
# the two commentary sections, whose entries are quoted) is wrapped in
# quotes. Everything else indented is treated as a sub-header and folds into
# the current section name (e.g. "Campus Resources / Health & Wellness").
# The two plain-prose intro sentences under the commentary sections are
# skipped outright (no "?", not quoted, not all-title-case like a header).

_QUOTED_LINE = re.compile(r'^"(.+)"$')


def parse_questions(path: str) -> list[dict]:
    with open(path) as f:
        raw_lines = [line.rstrip("\n") for line in f]

    questions = []
    section = None
    subsection = None

    for raw_line in raw_lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        is_indented = raw_line[:1] in (" ", "\t")

        quoted_match = _QUOTED_LINE.match(stripped)
        looks_like_question = stripped.endswith("?") or quoted_match is not None

        # A prose commentary sentence is never a section header, sub-header,
        # or question, regardless of indentation — the two intro sentences
        # in the file are themselves un-indented, same as a real section
        # header line, so this check must run first. Section/sub-headers
        # are short labels (a handful of words, no terminal punctuation);
        # prose sentences are long and end in "." or ":" — word count is
        # the reliable signal here, not the exact trailing punctuation.
        if not looks_like_question and len(stripped.split()) > 8:
            continue

        if not is_indented:
            # Top-level, un-indented line: a real section header.
            section = stripped
            subsection = None
            continue

        if not looks_like_question:
            # Indented, not question-shaped, not prose: a sub-header.
            subsection = stripped
            continue

        question_text = quoted_match.group(1) if quoted_match else stripped
        full_section = f"{section} / {subsection}" if subsection else section
        questions.append({"section": full_section, "question": question_text})

    return questions


# ---------------------------------------------------------------------------
# HTTP call
# ---------------------------------------------------------------------------
def call_chat_api(url: str, message: str, session_id: str, timeout: int = 30) -> dict:
    payload = {"message": message, "history": [], "sessionId": session_id, "language": "en"}
    body_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body_bytes,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed_ms = round((time.monotonic() - start) * 1000, 1)
            response_body = json.loads(resp.read().decode("utf-8"))
            return {
                "http_status": resp.status,
                "elapsed_ms": elapsed_ms,
                "request": payload,
                "response": response_body,
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        elapsed_ms = round((time.monotonic() - start) * 1000, 1)
        raw = exc.read().decode("utf-8")
        try:
            response_body = json.loads(raw)
        except json.JSONDecodeError:
            response_body = {"raw_body": raw}
        return {
            "http_status": exc.code,
            "elapsed_ms": elapsed_ms,
            "request": payload,
            "response": response_body,
            "error": f"HTTPError {exc.code}",
        }
    except Exception as exc:  # noqa: BLE001 — a demo run must never die mid-way
        elapsed_ms = round((time.monotonic() - start) * 1000, 1)
        return {
            "http_status": None,
            "elapsed_ms": elapsed_ms,
            "request": payload,
            "response": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run EkhoQuestions.txt through the live deployed API and log everything.")
    parser.add_argument("--url", default=DEFAULT_URL, help="Deployed /chat endpoint URL")
    parser.add_argument("--limit", type=int, default=None, help="Only run the first N questions (smoke test)")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds to wait between requests")
    args = parser.parse_args()

    questions = parse_questions(QUESTIONS_PATH)
    if args.limit:
        questions = questions[: args.limit]

    print(f"Loaded {len(questions)} questions from {os.path.relpath(QUESTIONS_PATH, PROJECT_ROOT)}")
    print(f"Target endpoint: {args.url}\n")

    entries = []
    capability_totals = {c: 0 for c in CAPABILITIES}

    for i, item in enumerate(questions, 1):
        section, question = item["section"], item["question"]
        tags = tag_capabilities(section, question)
        for t in tags:
            capability_totals[t] += 1

        session_id = f"demo-{i:04d}"
        print(f"[{i}/{len(questions)}] ({section}) {question}")
        result = call_chat_api(args.url, question, session_id)

        response = result["response"] or {}
        outcome_type = response.get("type", "error" if result["error"] else "unknown")
        preview = (response.get("message") or "")[:100]
        print(f"    -> {outcome_type} ({result['elapsed_ms']}ms): {preview}")
        if result["error"]:
            print(f"    !! ERROR: {result['error']}")

        entries.append(
            {
                "index": i,
                "section": section,
                "question": question,
                "capability_tags": tags,
                "session_id": session_id,
                "http_status": result["http_status"],
                "elapsed_ms": result["elapsed_ms"],
                "error": result["error"],
                "request_sent": result["request"],
                "response_received": result["response"],
            }
        )

        if i < len(questions):
            time.sleep(args.delay)

    # ---- Section index ----
    sections_seen = []
    for item in questions:
        if item["section"] not in sections_seen:
            sections_seen.append(item["section"])
    section_counts = {s: sum(1 for q in questions if q["section"] == s) for s in sections_seen}

    print("\n" + "=" * 70)
    print("CAPABILITY COVERAGE (question count tagged per capability)")
    print("=" * 70)
    for c in CAPABILITIES:
        print(f"  {c:<32} {capability_totals[c]}")

    print("\n" + "=" * 70)
    print("SECTION INDEX")
    print("=" * 70)
    for s in sections_seen:
        print(f"  {s:<45} {section_counts[s]} questions")

    error_count = sum(1 for e in entries if e["error"])
    print(f"\nTotal questions run: {len(entries)}  |  Errors: {error_count}")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(
            {
                "run_at": datetime.now(timezone.utc).isoformat(),
                "target_url": args.url,
                "total_questions": len(entries),
                "error_count": error_count,
                "capability_totals": capability_totals,
                "section_counts": section_counts,
                "entries": entries,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"\nFull log written to {os.path.relpath(RESULTS_PATH, PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
