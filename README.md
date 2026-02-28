# Support Chat Quality Analysis System

Generates synthetic support chat datasets using LLM and analyzes each chat for customer intent, satisfaction level, agent quality score, and specific agent mistakes — including hidden dissatisfaction detection.

## Task Overview

The system consists of two parts:

1. **Generation** — produces realistic multi-turn support chats grounded in brand-specific context, with deterministic distribution of domains, case types, and error flags (hidden dissatisfaction, tonal errors, logical errors).
2. **Analysis** — evaluates each chat for intent classification, customer satisfaction, agent quality scoring (1–10), and detailed agent mistake extraction with root cause attribution.

## Frontend

A Next.js frontend is available at **https://test-front.igor-novykov.workers.dev** (separate repository). It provides a UI for creating chat groups, viewing generated conversations, and browsing analysis results.

## Key Features

- **Hidden dissatisfaction detection** — identifies cases where the customer uses polite language but the issue remains unresolved
- **Tonal and logical error detection** — flags agent communication style issues and factual/procedural mistakes
- **Root cause attribution** — each agent mistake includes a cause (e.g. hallucinated, knowledge gap, process error)
- **Deterministic scenario distribution** — modular arithmetic ensures even coverage of domains, case types, and flags
- **Brand-specific context** — 9 preset brand contexts (Brighterly, Dressly, Howly, etc.) or custom context via file/URL
- **Two-step LLM validation** — every generation and analysis is followed by an LLM meta-validation pass with retry
- **Website context gathering** — automatically scrapes and structures context from a provided URL

## Project Structure

```
src/chat_analysis/
├── models.py              # Shared enums and ChatMessage
├── data/
│   ├── context/           # Domain-specific .md context files
│   └── domains/           # Brand-specific .md support context files
├── core/
│   ├── config.py          # LLM factory, paths, generation params
│   └── security.py        # Input sanitization, path validation
├── generation/
│   ├── models.py          # Generation-specific Pydantic models
│   ├── prompts.py         # Generation and validation prompt templates
│   └── service.py         # Generation pipeline logic
├── analysis/
│   ├── models.py          # Analysis-specific Pydantic models
│   ├── prompts.py         # Analysis and meta-validation prompt templates
│   └── service.py         # Analysis pipeline logic
└── api/                   # FastAPI application
    ├── models.py          # API request/response schemas
    └── routers/           # API route handlers
generate.py                # Entry point: generate chat dataset
analyze.py                 # Entry point: analyze chats
main.py                    # Entry point: API server
tests/                     # Test suite
output/                    # Generated outputs (gitignored)
```

## Setup & Usage

### Install

```bash
pip install -r requirements.txt
cp .env.example .env  # then add your API key
```

### Generate chats (CLI)

```bash
python generate.py   # → output/generated_chats.json (20 chats)
```

### Analyze chats (CLI)

```bash
python analyze.py    # → output/analysis_results.json
```

### Run API server

```bash
python main.py       # starts on http://0.0.0.0:8000
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/groups/businesses` | List available preset business contexts |
| `GET` | `/groups` | List all groups (newest first) |
| `POST` | `/groups` | Create group and start generation (background) |
| `GET` | `/groups/{group_id}/chats` | Get group status and chat summaries |
| `POST` | `/groups/{group_id}/analyze` | Trigger analysis for all chats in group |
| `GET` | `/groups/{group_id}/chats/{chat_id}` | Get full chat detail (messages + analysis) |
| `POST` | `/groups/{group_id}/chats/{chat_id}/analyze` | Analyze a single chat |
| `POST` | `/groups/{group_id}/chats/{chat_id}/regenerate` | Regenerate a single failed chat |

## Scenario Distribution

5 domains × 4 case types = 20 deterministic scenarios per full run:

| Domain | Case Types |
|---|---|
| Payment Issues | simple_resolved, complex_resolved, escalated, unresolved |
| Technical Errors | simple_resolved, complex_resolved, escalated, unresolved |
| Account Access | simple_resolved, complex_resolved, escalated, unresolved |
| Tariff Questions | simple_resolved, complex_resolved, escalated, unresolved |
| Refunds | simple_resolved, complex_resolved, escalated, unresolved |

Flags are assigned via modular arithmetic (`idx % 4`): index 1 → hidden dissatisfaction, index 2 → tonal errors, index 3 → logical errors.

## Output Format

Each analyzed chat produces a `ChatAnalysis` object:

```json
{
  "chat_id": "chat_001",
  "intent": "request_refund",
  "satisfaction": "unsatisfied",
  "quality_score": 4,
  "agent_mistakes": [
    {
      "type": "logical",
      "description": "Agent quoted a non-existent 30-day refund policy",
      "cause": "hallucinated",
      "message_index": 3
    },
    {
      "type": "tonal",
      "description": "Dismissive response to customer frustration",
      "cause": "poor_communication",
      "message_index": 5
    }
  ],
  "reasoning": "Customer's refund request was denied based on fabricated policy. Agent showed lack of empathy despite clear frustration signals."
}
```

| Field | Values |
|---|---|
| `satisfaction` | `satisfied`, `neutral`, `unsatisfied` |
| `quality_score` | 1–10 (10 = perfect) |
| `agent_mistakes[].type` | `tonal`, `logical` |
| `agent_mistakes[].cause` | `lack_of_information`, `hallucinated`, `knowledge_gap`, `process_error`, `poor_communication`, `bad_system_prompt`, `misunderstood_customer` |

## Configuration

Environment variables (`.env`):

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai`, `anthropic`, or `google` |
| `LLM_MODEL` | `gpt-4o-mini` | Model name |
| `OPENAI_API_KEY` | — | Required when provider is `openai` |
| `ANTHROPIC_API_KEY` | — | Required when provider is `anthropic` |

`LLM_TEMPERATURE` is hardcoded to `0` and `seed=42` (OpenAI) for deterministic output.

## Docker

### Build and run manually

```bash
docker build -t chat-analysis .
docker run --env-file .env -p 8000:8000 chat-analysis
```

### Docker Compose

```bash
docker compose up -d
```

The compose file runs the API server on port 8000 with auto-restart and Watchtower for automatic image updates.

## Tech Stack

- **Python 3.12** — runtime
- **LangChain** — LLM orchestration with LCEL chains and structured output
- **FastAPI** — async API with background task processing
- **Pydantic** — data validation and structured LLM output schemas
- **Uvicorn** — ASGI server
