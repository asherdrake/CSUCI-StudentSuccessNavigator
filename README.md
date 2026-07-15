# CSUCI Student Success Navigator

An AI-powered chatbot that helps California State University Channel Islands (CSUCI) students get instant, accurate answers to questions about registration, advising, financial aid, graduation, and campus support services.

Built on **Amazon Bedrock** (Claude 3.5 Sonnet + Knowledge Bases) with a fully serverless AWS backend and a React frontend.

---

## Architecture

```mermaid
flowchart LR
    Student([Student]) -->|message| APIGW[API Gateway]
    APIGW --> Lambda[Lambda Orchestrator]
    Lambda --> Safety[Safety Filter]
    Safety -->|crisis| SNS[SNS Escalation]
    Safety -->|safe| KB[Bedrock Knowledge Base]
    KB --> Claude[Claude 3.5 Sonnet]
    Claude --> Lambda
    Lambda --> DDB[(DynamoDB Sessions)]
    Lambda -->|response| APIGW
    APIGW -->|answer| Student
```

### Component Summary

| Component | Purpose |
|---|---|
| **API Gateway** | HTTPS endpoint with CORS; routes `POST /chat` to Lambda |
| **Lambda Orchestrator** | Coordinates safety check → retrieval → LLM → session save |
| **Safety Filter** | Detects crisis language and escalation requests |
| **Bedrock Knowledge Base** | RAG retrieval over CSUCI catalog & policy PDFs |
| **Claude 3.5 Sonnet** | Generates grounded, student-friendly answers |
| **DynamoDB** | Stores multi-turn conversation sessions (TTL-enabled) |
| **SNS** | Sends email/SMS alerts when a student needs human help |

---

## Prerequisites

| Tool | Version |
|---|---|
| AWS Account | With Amazon Bedrock model access enabled |
| AWS SAM CLI | ≥ 1.100 |
| Python | 3.12 |
| Node.js | ≥ 18 (for the React frontend) |
| Docker | Optional, for `sam build --use-container` |

---

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd "CSUCI Student Success Navigation"
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in:
#   BEDROCK_KB_ID  — your Knowledge Base ID
#   AWS_REGION     — e.g. us-west-2
```

### 3. Deploy the backend

```bash
cd infra
sam build
sam deploy --guided
# Follow the prompts — provide your BedrockKBId when asked.
```

> **Tip:** After the first guided deploy the settings are saved in `samconfig.toml`. Future deploys only need `sam deploy`.

### 4. Note the outputs

After deployment, SAM prints:

```
Outputs:
  ApiEndpointUrl   = https://xxxxxxxxxx.execute-api.us-west-2.amazonaws.com/prod/chat
  SessionTableName = student-navigator-sessions-dev
  OrchestratorFunctionArn = arn:aws:lambda:...
```

Use the `ApiEndpointUrl` in your frontend `.env` file.

### 5. Run the tests

```bash
pip install -r requirements-dev.txt   # pytest, moto, boto3, etc.
pytest tests/ -v
```

---

## API Reference (Quick)

### `POST /chat`

**Request:**
```json
{
  "message": "How do I register for classes?",
  "sessionId": "optional-uuid"
}
```

**Response (200):**
```json
{
  "answer": "You can register via the myCI portal...",
  "sources": ["catalog.pdf"],
  "sessionId": "uuid-of-session"
}
```

For the full schema, error codes, and curl examples see **[docs/api_reference.md](docs/api_reference.md)**.

---

## Project Structure

```
CSUCI Student Success Navigation/
├── README.md                  ← you are here
├── .env.example
├── infra/
│   ├── template.yaml          ← AWS SAM / CloudFormation template
│   └── samconfig.toml         ← SAM CLI deployment defaults
├── lambda/
│   ├── orchestrator/
│   │   └── handler.py         ← Lambda entry point
│   ├── safety_filter.py       ← crisis & escalation detection
│   ├── session.py             ← DynamoDB session management
│   ├── retriever.py           ← Bedrock Knowledge Base retrieval
│   └── llm.py                 ← Claude response generation
├── tests/
│   ├── conftest.py            ← shared fixtures
│   ├── test_safety_filter.py
│   ├── test_session.py
│   ├── test_retriever.py
│   ├── test_handler.py
│   └── fixtures/
│       └── sample_queries.json
├── frontend/                  ← React app (separate README)
└── docs/
    ├── api_reference.md
    └── architecture.md
```

---

## Contributing

1. Create a feature branch from `main`.
2. Write tests for new behaviour.
3. Ensure `pytest tests/ -v` passes.
4. Open a pull request.

---

## Team

> _Add team member names and roles here._

---

## License

This project is developed for CSUCI coursework. See `LICENSE` for details.
