# API Reference — Student Success Navigator

Base URL (after deployment):

```
https://<api-id>.execute-api.us-west-2.amazonaws.com/prod
```

Local development: `http://localhost:8000/chat` (via `scratch/dev_server.py`).

---

## `POST /chat`

Send a student message and receive a **type-discriminated** response. The
`type` field says what kind of turn this is; `message` is always the
student-facing text; `citations` and `escalation` are structured sidecars
that are present only when relevant.

### Request

| Field | Type | Required | Description |
|---|---|---|---|
| `message` | string | **Yes** | The student's question. |
| `history` | array | No | Prior turns, each `{"role": "user"\|"assistant", "content": "..."}`. Conversation state is client-managed. |
| `sessionId` | string | No | UUID of an existing conversation. Omit to start a new one. |

**Headers:** `Content-Type: application/json`

**Example:**

```json
{
  "message": "How do I register for classes?",
  "history": [],
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

### Response shape (200)

```jsonc
{
  "type": "answer" | "clarify" | "escalate" | "decline" | "crisis",
  "message": "student-facing text (always present)",
  "citations": [ { "title": "...", "url": "...", "passages": [1, 3] } ],  // type=answer only
  "escalation": {                    // present for escalate, or answer+escalation pairs
    "office": "Financial Aid",
    "contact": { "phone": "...", "url": "...", "location": "...", "map_url": "..." },
    "ticket_draft": { "summary": "...", "raw_message": "...", "office": "...", "sessionId": "..." }
  },
  "sessionId": "...",
  "debug": { "retrieved_chunks": [...] }   // only when DEBUG_CHUNKS=1 on the backend
}
```

Rendering rule for clients: **render `message`; if `citations` is present,
render the source list; if `escalation` is present, render the handoff card.**
No other branching is needed — the answer+human pair is just an `answer` that
also carries `escalation`.

### The five types

| `type` | Meaning | `citations` | `escalation` |
|---|---|---|---|
| `answer` | Grounded answer from the knowledge base | yes | only when the student also needs/requested a human |
| `clarify` | The question was ambiguous; `message` is one clarifying question | no | no |
| `escalate` | A human is needed; `message` is a short lead-in | no | yes |
| `decline` | Out of scope for a CSUCI assistant; `message` is a standard decline | no | no |
| `crisis` | Crisis language detected; `message` is the hotline response (LLM bypassed) | no | no |

### Inline citations

Answers embed passage markers like `[1]` after each claim. Each entry in
`citations` lists which passage numbers (`passages`) resolve to that source,
so clients can turn `[N]` markers into links. The model never authors URLs —
all URLs come from retrieved knowledge-base metadata, resolved server-side.

---

### Response — Error (400)

```json
{ "error": "Missing required field: 'message'." }
```

### Response — Error (500)

Infrastructure failure (Bedrock timeout/throttle). Retryable — distinct from
an escalation, which is a *successful* response with `type: "escalate"`.

```json
{ "error": "Sorry, I am having trouble connecting to Bedrock. Please try again later." }
```

---

## Example `curl` commands

```bash
# Normal query
curl -X POST https://<api-id>.execute-api.us-west-2.amazonaws.com/prod/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I register for classes?"}'

# Continue a conversation (history is client-managed)
curl -X POST https://<api-id>.execute-api.us-west-2.amazonaws.com/prod/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What about the add/drop deadline?",
    "history": [
      {"role": "user", "content": "How do I register for classes?"},
      {"role": "assistant", "content": "You can register through myCI [1]..."}
    ],
    "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }'
```

---

## CORS

| Header | Value |
|---|---|
| `Access-Control-Allow-Origin` | `*` |
| `Access-Control-Allow-Headers` | `Content-Type, Authorization, X-Amz-Date, X-Api-Key` |
| `Access-Control-Allow-Methods` | `POST, OPTIONS` |

> **Production hardening:** Replace `*` with your frontend domain.

---

## Authentication (Future)

The current deployment does **not** require authentication. Planned:
CSUCI SSO (SAML/OIDC), API keys, or Cognito user pools.
