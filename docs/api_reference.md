# API Reference — Student Success Navigator

Base URL (after deployment):

```
https://<api-id>.execute-api.us-west-2.amazonaws.com/prod
```

---

## `POST /chat`

Send a student message and receive an AI-generated answer grounded in CSUCI documents.

### Request

| Field | Type | Required | Description |
|---|---|---|---|
| `message` | string | **Yes** | The student's question (1–2 000 characters). |
| `sessionId` | string | No | UUID of an existing conversation session. Omit to start a new session. |

**Headers:**

| Header | Value |
|---|---|
| `Content-Type` | `application/json` |

**Example:**

```json
{
  "message": "How do I register for classes?",
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

### Response — Success (200)

```json
{
  "answer": "You can register for classes through the myCI portal at https://myci.csuci.edu. Registration dates vary by class standing...",
  "sources": [
    "CSUCI_Catalog_2025.pdf",
    "Registration_Guide.pdf"
  ],
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "type": "normal"
}
```

| Field | Type | Description |
|---|---|---|
| `answer` | string | The AI-generated answer, grounded in retrieved documents. |
| `sources` | string[] | List of source document names used to generate the answer. |
| `sessionId` | string | Session UUID (new or existing). Pass this back to continue the conversation. |
| `type` | string | Response type: `"normal"`, `"crisis"`, or `"escalation"`. |

---

### Response — Crisis (200)

Returned when the safety filter detects crisis language (e.g., self-harm, suicide).

```json
{
  "answer": "I'm really concerned about what you've shared. Please reach out to the 988 Suicide and Crisis Lifeline by calling or texting 988. You can also contact CSUCI CAPS at (805) 437-2088. You are not alone.",
  "sources": [],
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "type": "crisis"
}
```

> **Note:** Crisis responses bypass the LLM entirely and return a pre-defined message with professional resources.

---

### Response — Escalation (200)

Returned when the student requests a human advisor.

```json
{
  "answer": "I'll connect you with a human advisor. A staff member has been notified and will reach out to you shortly. In the meantime, you can contact the Advising Center at (805) 437-8500 or visit Bell Tower 1548.",
  "sources": [],
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "type": "escalation"
}
```

---

### Response — Error (400)

Missing or invalid `message` field.

```json
{
  "error": "Missing required field: message",
  "statusCode": 400
}
```

### Response — Error (500)

Internal server error (e.g., Bedrock timeout).

```json
{
  "error": "An internal error occurred. Please try again later.",
  "statusCode": 500
}
```

---

## Example `curl` Commands

### Normal query

```bash
curl -X POST \
  https://<api-id>.execute-api.us-west-2.amazonaws.com/prod/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I register for classes?"}'
```

### Continue a session

```bash
curl -X POST \
  https://<api-id>.execute-api.us-west-2.amazonaws.com/prod/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What about the add/drop deadline?",
    "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }'
```

### Crisis message

```bash
curl -X POST \
  https://<api-id>.execute-api.us-west-2.amazonaws.com/prod/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to hurt myself"}'
```

---

## CORS

The API is configured with the following CORS headers:

| Header | Value |
|---|---|
| `Access-Control-Allow-Origin` | `*` |
| `Access-Control-Allow-Headers` | `Content-Type, Authorization` |
| `Access-Control-Allow-Methods` | `POST, OPTIONS` |

The `OPTIONS` pre-flight request is handled automatically by API Gateway.

> **Production hardening:** Replace `*` with your frontend domain (e.g., `https://navigator.csuci.edu`).

---

## Rate Limiting

API Gateway applies the following default throttling:

| Limit | Value |
|---|---|
| Steady-state rate | 10 000 requests/second |
| Burst | 5 000 requests |

For the student navigator, these defaults are more than sufficient. To add per-user rate limiting, configure a **Usage Plan** and **API Key** in the SAM template.

---

## Authentication (Future)

The current deployment does **not** require authentication. Planned enhancements:

1. **CSUCI SSO** — Integrate with the university's SAML/OIDC identity provider.
2. **API Key** — Issue keys to the frontend for basic access control.
3. **Cognito** — Add user pools for session-aware features (e.g., personalized advising).
