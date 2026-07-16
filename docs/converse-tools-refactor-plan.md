# Implementation Plan — Converse Tool-Use Refactor

**Branch:** `converse-tools`
**Status:** design complete, ready to implement

## 1. Why this refactor

The LLM's decision-making is growing (answer / clarify / escalate to a specific
office / decline out-of-scope / language matching / …). Today those decisions are
encoded as **magic strings parsed out of prose** (`NO_ANSWER`, `CLARIFY:`) and
dispatched through a ~430-line linear `if`-ladder in the handler, with the routing
"when" rules piled into one system prompt where they **collide** (rules 1/4/7 all
emit `NO_ANSWER`, which forced the defensive carve-out at `prompts.py:58-62`).

Adding more behaviors makes the prompt more conflicted and the handler more
duplicated. This refactor replaces the sentinel-string design with **Converse
tool-use**: the model returns a *structured decision*, and the "when" rules move
out of conflicting prose into discrete tool descriptions.

## 2. Scope

**In scope (this branch):**
- **A** — move deterministic mechanics (map links, contact cards, ticket text) out
  of the prompt into code.
- **B** — replace sentinels with Converse tool-use (four tools, model picks).
- **D** — collapse the API response to a `type`-discriminated contract.
- Eval runner over `eval/single_turn_cases.json`.
- Thin frontend adapter to consume the new contract.

**Deferred (explicitly not this branch):**
- **C** — splitting into a separate triage → generation call. Do a *single*
  tool-use call first; only add a triage step if the single call proves inaccurate.
- **E** — full `App.jsx` decomposition into components/hooks. Frontend gets only the
  minimum change to read the new contract.
- Structured `options[]` on clarify and `follow_ups[]` on answer (additive later).
- Automatic retry on bad model output (add only if logs show it's frequent).
- LLM-as-a-judge answer-quality / hallucination scoring (separate future tool).

## 3. Target model

**Claude Sonnet 5, via inference profile: `us.anthropic.claude-sonnet-5`.**

> **Corrected after a live probe (2026-07-15).** The originally-planned
> `anthropic.claude-3-5-sonnet-20241022-v2:0` — still the default in
> `infra/template.yaml` and `.env.example` — is **end-of-life on Bedrock** and
> returns `ResourceNotFoundException`. Claude Sonnet 5 is the current successor and
> was confirmed working with `toolConfig` + `toolChoice: {any}` on this account
> (`812227824078`, us-west-2). Haiku 4.5 (`us.anthropic.claude-haiku-4-5-20251001-v1:0`)
> also works with tool-use and is the cheaper fallback.

Two hard facts from the probe:
- **Inference-profile only, no on-demand.** The raw `anthropic.claude-sonnet-5` ID
  fails with `ValidationException`; you MUST use the `us.`-prefixed inference-profile
  ID. Update `.env`, the `llm.py` fallback, `.env.example`, and `template.yaml`.
- **IAM (deployed Lambda only):** `template.yaml` currently scopes
  `bedrock:InvokeModel` to `foundation-model/${ModelId}`. Inference profiles resolve
  to foundation models across regions, so the policy must allow the inference-profile
  ARN **and** the underlying cross-region foundation-model ARNs. Local runs are
  unaffected (the SSO role already has access — the probe succeeded).

Keep `MODEL_ID` configurable. If a later head-to-head favors cost, Haiku 4.5 is the
tool-capable fallback; Llama 3 70B is **not** an option (no Converse tool-use).

## 4. Tool schema (the structured decision)

```
answer_from_context(answer: markdown, citations: int[])        → type "answer"
ask_clarification(question: string)                            → type "clarify"
escalate_to_office(office: enum, reason: string)               → type "escalate"
decline_out_of_scope(reason: string)                           → type "decline"
```

- `toolChoice: {any}` — the model MUST call a tool (no free-text output).
- **Exactly one tool per turn**, with **one allowed pair**: `answer_from_context`
  **+** `escalate_to_office` (an answerable question that also needs/requests a
  human). Any other multi-tool combination is invalid (see §11).
- **`office` enum:** `financial_aid | advising | registrar | tutoring |
  general_support`. `general_support` is the honest catch-all for "needs a human,
  is a CSUCI matter, but no specific office fits" (e.g. housing). `advising` means
  *only* Academic Advising now — it is no longer the default dumping ground.
- **`citations` = passage numbers**, not URLs. The model cites the numbered passages
  it used (passages are already numbered "Passage 1…" in the prompt). Code resolves
  numbers → trusted `{title, url}`. The model never emits a URL anywhere.
- **`reason` fields are internal**, never shown to the student:
  - `escalate.reason` → the staff-facing ticket body (a real handoff note).
  - `decline.reason` → logging only (product signal on what's out of scope).

**Boundary:** the model authors student-facing prose only in `answer` and
`question`. For `escalate` and `decline`, the student sees code-owned text (a contact
card / a canned decline template).

## 5. Citation presentation

Option **C**: the model writes **inline numeric markers** in the answer prose
(`"…the deadline is October 1 [1]"`) — just the number. Code post-processes `[N]`
into a link built from the *resolved* citation, and also lists sources in the
sidecar. The model stays URL-free end-to-end. This replaces the hand-rolled
`parseMarkdownLinks` regex (`App.jsx:134`) with a smaller `[N]`→link resolver.

## 6. New handler control flow

```
1. CORS preflight            (unchanged)
2. Parse / validate body     (unchanged)
3. Crisis check              (deterministic, pre-LLM, UNCHANGED) → type "crisis"
4. Retrieve context (top_k=5)  ALWAYS — no score-floor short-circuit
5. Number passages, build thin system prompt + toolConfig
6. invoke_model(tools) → [{name, input}]   (parsing lives in llm.py)
7. Validate + dispatch (see §11 for failure handling):
     - answer            → resolve citations; empty/out-of-range ⇒ fail-safe escalate
     - clarify           → question becomes message
     - escalate          → coerce bad office; build ticket from reason; card from router
     - decline           → canned message; reason → log
     - answer + escalate → answer message + citations + escalation sidecar
8. Backstop: if safety_filter flagged an explicit human request but the model did
   NOT pair an escalate, force-append an escalation (general_support).
9. Structured CloudWatch log (adapt fields to new contract)
10. Return response
```

**Deleted by this refactor:**
- The 0.35 score-floor short-circuit (`handler.py:227-268`).
- The `NO_ANSWER` and `CLARIFY:` sentinel branches (`handler.py:296`, `:331`).
- The substring citation validator `_validate_citations` (`handler.py:89`) and the
  over-citation filter (`handler.py:395`) — both replaced by passage-number resolution.
- Keyword routing in `router.py` (the whole `_has_keyword` / category-matching block).

## 7. `router.py` → phone book

Collapses to a pure `office_key → {phone, url, location, map_url}` lookup. Add a
`general_support` entry. **TODO: obtain a real Student Services contact** for it.
The model picks the office; the code only looks up contact details and assembles the
ticket (`{summary: reason, raw_message, office, sessionId}`).

## 8. Response contract (change D)

```jsonc
{
  "type": "answer" | "clarify" | "escalate" | "decline" | "crisis",
  "message": "student-facing text (always present)",
  "citations": [{ "title": "...", "url": "..." }],   // present for type=answer
  "escalation": {                                     // present for escalate OR the pair
    "office": "...", "contact": { "phone","url","location","map_url" },
    "ticket_draft": { "summary","raw_message","office","sessionId" }
  },
  "sessionId": "...",
  "debug": { "retrieved_chunks": [...] }              // only when DEBUG_CHUNKS=1
}
```

- **`answered` is deleted.** Anything needing it computes `type === "answer"`.
- Frontend logic: render `message`; if `citations`, render them; if `escalation`,
  render the card. The pair needs no special case — it's an answer that also carries
  the escalation sidecar.

## 9. Prompt rewrite — three homes

Every current rule goes to exactly one home:

| Current rule | New home |
|---|---|
| Identity, tone (3), privacy (8), "answer only from numbered passages" (1), language-matching | **System prompt** (thin global core) + "call one tool, or the answer+escalate pair" |
| `NO_ANSWER` mechanism (1, 4, 7) | **Deleted** — replaced by tool *selection* |
| Cite sources (2) | `answer_from_context` desc (passage #s, `[N]` markers) |
| Escalate when human judgment needed (4) | `escalate_to_office` desc |
| Decline off-topic (7) | `decline_out_of_scope` desc |
| Numbered steps (5), related topics (6) | `answer_from_context` desc |
| Ambiguous → clarify (10) | `ask_clarification` desc |
| Conflicting / dated sources (9, 11) | `answer_from_context` desc (answer *composition*, not tool selection) |

The carve-out at `prompts.py:58-62` **disappears** — "return NO_ANSWER" is no longer
a prose instruction competing with "present the conflict," so the collision it
patched is gone by construction. Tool schemas + descriptions live in a new
`tools.py` module (they now carry the routing logic).

## 10. `llm.py` — the structuring seam

`llm.py` is the ONLY place that knows Converse exists (our own tiny `bind_tools`).
`invoke_model` builds `toolConfig` + `toolChoice: {any}`, calls Converse, unwraps
the `toolUse` blocks, and returns a clean `[{name, input}]` list. Structural
validation (known tool? required args present? combination allowed?) lives here;
domain policy does not. No LangChain — this replaces ~40 lines of stable Converse
parsing that a framework dependency isn't worth.

## 11. Failure handling — fail safe toward a human

| Failure | Handling |
|---|---|
| Zero tools / text-only reply | `escalate(general_support)`, log loudly |
| Nonsense combo (e.g. clarify+decline, 3 tools) | reject → `escalate(general_support)`, log |
| `answer` with empty / out-of-range citations | ungrounded ⇒ `escalate(general_support)`, log |
| `escalate` office not in enum | coerce to `general_support` |
| Bedrock API error / throttle / timeout | keep **HTTP 500** (retryable), not an escalation |

- "Model gave junk" (successful call, unusable decision) → human handoff.
  "Infrastructure broke" → 500 so the client retries. Kept distinct.
- **No auto-retry in v1** — fail safe + log; add retry later only if logs justify it.
- Split: `llm.py` does structural validation; the **handler** applies policy and
  range-checks citation numbers against the retrieved chunks (only it has the list).

## 12. Frontend thin adapter (minimal — full split deferred)

- `handleSubmit` reads the new contract; drop reliance on `answered` (use `type`).
- Replace `parseMarkdownLinks` with a `[N]`→link resolver keyed off `citations`.
- Message render switches on `type`; escalation/citation sidecars render by presence.
- No component/hook decomposition yet (that's change E, a separate branch).

## 13. Eval runner (`eval/run_eval.py`)

- **Live stack**: real handler → real Bedrock Retrieve → real Claude. ~28 queries,
  pennies/run. Needs AWS creds + KB, so it's a **manual/opt-in** eval, not pytest.
- **Scores:** outcome accuracy (chosen tool vs expected `type`), routing accuracy
  (`escalation.office` vs `expected_office`, on `needs_human` rows), and a
  **confusion matrix** over the five outcomes (the key artifact — shows *which*
  misroutes happen).
- **Scorecard, not a hard gate** — establish the new-system baseline, watch for
  regressions on later tweaks.
- **Prereq:** relabel `single_turn_cases.json` `type` to the four-outcome taxonomy
  (`answerable | needs_human | out_of_scope | ambiguous`) and add a few
  non-answerable / ambiguous cases. It's a human answer key (exact-match), **not**
  LLM-as-a-judge.

## 14. Tests

- **Keep unchanged:** `test_safety_filter.py`, `test_retriever.py` (those modules
  don't change).
- **Rewrite `test_handler.py`** to the new contract. Delete obsolete tests
  (score-floor skip, `NO_ANSWER` sentinel, substring citation). Add: each tool →
  its `type`/sidecars, the answer+escalate pair, passage-number resolution, clarify,
  decline, fail-safe escalate, crisis-bypasses-LLM. Mock the LLM at the new seam:
  `mock_invoke.return_value = [{"name": "...", "input": {...}}]`.
- **New `test_llm.py`** — unit-test Converse-response parsing into `{name, input}`
  in isolation (the one gnarly bit).

## 15. Implementation sequence

Each step is an independent checkpoint:

1. **Config**: point `.env` + `llm.py` fallback to Claude 3.5 Sonnet.
2. **`tools.py`**: define the four tool schemas + descriptions (the "when" rules).
3. **`prompts.py`**: shrink to the thin global core (§9).
4. **`llm.py`**: `toolConfig` + `toolChoice`, return parsed `[{name, input}]`;
   `test_llm.py`.
5. **`router.py`**: collapse to phone book; add `general_support`.
6. **`handler.py`**: new flow (§6), dispatch, citation resolution, fail-safe (§11),
   backstop; delete dead branches.
7. **Contract**: emit the §8 shape; delete `answered`.
8. **Frontend**: thin adapter (§12).
9. **Tests**: rewrite `test_handler.py`.
10. **Eval**: relabel golden set + add cases; write `run_eval.py`; capture baseline.
11. **Docs**: update `docs/architecture.md` (currently describes Llama/DynamoDB/SNS
    that don't match the code).

## 16. Open to-dos

- Real contact details for `general_support` in `router.py`.
- Add `not_answerable` / `ambiguous` / `out_of_scope` rows to `single_turn_cases.json`.
- Decide whether to keep the "always suggest related topics" mandate (a product
  choice; adds tokens, can cause padding) — orthogonal to the schema.
