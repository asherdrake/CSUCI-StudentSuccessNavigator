"""
Converse tool definitions for the CSUCI Student Success Navigator.

These tools ARE the model's decision surface: instead of emitting sentinel
strings (the old NO_ANSWER / CLARIFY: design), the model must call exactly one
of these tools — or the single allowed pair (answer_from_context +
escalate_to_office) when a message is both answerable and needs a human.

The tool descriptions carry the "when to pick me" routing rules that used to
live as competing prose rules in the system prompt. Keep them focused and
mutually exclusive: the decline/escalate boundary is "is this a CSUCI matter?"

Exports
-------
- ``TOOL_CONFIG``      – full Converse ``toolConfig`` (tools + toolChoice: any).
- ``ANSWER_TOOL`` etc. – tool-name constants used by llm.py and the handler.
- ``OFFICE_KEYS``      – the closed office enum (must match router.OFFICES).
"""

ANSWER_TOOL = "answer_from_context"
CLARIFY_TOOL = "ask_clarification"
ESCALATE_TOOL = "escalate_to_office"
DECLINE_TOOL = "decline_out_of_scope"

# Closed enum — must stay in sync with router.OFFICES keys.
OFFICE_KEYS = [
    "financial_aid",
    "advising",
    "registrar",
    "tutoring",
    "general_support",
]

_ANSWER_DESCRIPTION = """\
Answer the student's question using ONLY the numbered passages provided in the \
system prompt. Call this when the passages contain enough information to answer \
the question directly.

Rules for the answer:
- Cite by passage number: place the number in square brackets, like [1], \
immediately after each claim it supports. NEVER write a URL — only bracketed \
passage numbers. List every passage number you actually used in `citations`.
- Do NOT call this tool if no passage supports the answer; use \
escalate_to_office or decline_out_of_scope instead.
- If passages give materially different answers, first decide whether they \
describe DIFFERENT things (different programs, audiences, or years) or genuinely \
disagree about the SAME thing. Different things: answer for the one the student \
means, or present each under a heading naming what distinguishes it. Genuine \
contradiction: say the sources differ, give what each says with its passage \
citation, and recommend confirming with the relevant office.
- Prefer the most current passage. If only a dated source exists and timeliness \
matters, answer but note it may be out of date.
- Format sequential instructions as a numbered list.
- If your answer mentions, locates, or describes any major campus building or location (such as Sage Hall, Broome Library, Bell Tower, Sierra Hall, Malibu Hall, Aliso, Napa, Solano, Placer, Student Housing, or the main campus), you MUST list their corresponding enum keys in the `buildings_mentioned` parameter.\

"""

_CLARIFY_DESCRIPTION = """\
Ask the student ONE short clarifying question. Call this ONLY when the question \
could reasonably refer to more than one distinct thing the passages cover, and \
the correct answer depends on which — for example, two different degree programs \
with different requirements. Name the options in your question so the student \
can pick. Do NOT call this when the intent is obvious, and never combine it with \
any other tool: if you need clarification, you cannot yet know whether to \
answer, escalate, or decline.\
"""

_ESCALATE_DESCRIPTION = """\
Route the student to a human at a specific campus office. Call this when the \
question is a genuine CSUCI matter but cannot be resolved from the passages: \
the information is missing from the passages, OR the situation needs human \
judgment (advising exceptions, financial-aid appeals, disability \
accommodations, personal records like grades or holds on a specific student's \
account).

Choosing the office:
- financial_aid: FAFSA, scholarships, loans, grants, aid appeals.
- advising: degree planning, major changes, course substitutions, academic \
  exceptions.
- registrar: registration, transcripts, enrollment records, graduation \
  processing.
- tutoring: tutoring, writing help, learning support.
- general_support: the question needs a person and is a CSUCI matter, but NONE \
  of the offices above clearly apply (housing, parking, IT, campus life, ...).

`reason` is an internal note for the staff member who receives the handoff — \
one or two sentences saying what the student needs and why it requires a human. \
The student never sees it.

You may pair this tool with answer_from_context when a message contains BOTH an \
answerable question AND a request or need for a human (e.g. "How do I register? \
Also connect me to an advisor."). That is the only allowed combination.\
"""

_DECLINE_DESCRIPTION = """\
Politely decline the question. Call this ONLY when the question is NOT a CSUCI \
or higher-education matter at all (general trivia, personal advice, weather, \
investments, requests for other people's personal data). If the question IS a \
CSUCI matter but just isn't covered by the passages, use escalate_to_office \
instead — declining a real student need is worse than routing it to a person. \
`reason` is an internal log note (e.g. "off-topic: bicycle repair"); the \
student sees a standard message you do not write. Never combine this tool with \
any other.\
"""

TOOL_CONFIG = {
    "tools": [
        {
            "toolSpec": {
                "name": ANSWER_TOOL,
                "description": _ANSWER_DESCRIPTION,
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "answer": {
                                "type": "string",
                                "description": (
                                    "The full answer in markdown, with [N] "
                                    "passage-number citations after each claim. "
                                    "No URLs."
                                ),
                            },
                            "citations": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": (
                                    "The passage numbers actually used, e.g. [1, 3]. "
                                    "Must not be empty."
                                ),
                            },
                            "buildings_mentioned": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": [
                                        "sage_hall",
                                        "broome_library",
                                        "bell_tower",
                                        "sierra_hall",
                                        "malibu_hall",
                                        "aliso_hall",
                                        "napa_hall",
                                        "solano_hall",
                                        "placer_hall",
                                        "student_housing",
                                        "main_campus"
                                    ]
                                },
                                "description": (
                                    "Optional list of campus buildings or locations mentioned in your answer "
                                    "that need Google Maps links."
                                )
                            }
                        },
                        "required": ["answer", "citations"],
                    }
                },
            }
        },
        {
            "toolSpec": {
                "name": CLARIFY_TOOL,
                "description": _CLARIFY_DESCRIPTION,
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": (
                                    "One short clarifying question that names the "
                                    "options the student can pick between."
                                ),
                            },
                        },
                        "required": ["question"],
                    }
                },
            }
        },
        {
            "toolSpec": {
                "name": ESCALATE_TOOL,
                "description": _ESCALATE_DESCRIPTION,
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "office": {
                                "type": "string",
                                "enum": OFFICE_KEYS,
                                "description": "The campus office to route to.",
                            },
                            "reason": {
                                "type": "string",
                                "description": (
                                    "Internal staff-facing note: what the student "
                                    "needs and why it requires a human."
                                ),
                            },
                        },
                        "required": ["office", "reason"],
                    }
                },
            }
        },
        {
            "toolSpec": {
                "name": DECLINE_TOOL,
                "description": _DECLINE_DESCRIPTION,
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "reason": {
                                "type": "string",
                                "description": (
                                    "Internal log note on why this is out of scope."
                                ),
                            },
                        },
                        "required": ["reason"],
                    }
                },
            }
        },
    ],
    # The model MUST call a tool — free-text-only replies are a failure mode
    # the handler treats as unusable output.
    "toolChoice": {"any": {}},
}
