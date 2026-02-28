# Support Chat Quality Analysis System

A system that generates synthetic support chat datasets using LLM and analyzes each chat for intent, satisfaction, quality, and agent mistakes.

## Architecture

```
[Chat Domain] + [Context .md] → [Secure] → [System Prompt] → [LLM Generate] → [LLM Validate]
```

- **Generate pipeline**: Scenario matrix → Prompt assembly (with domain context) → LLM structured generation → LLM validation (retry up to 3×)
- **Analysis pipeline**: Load chats → Sanitize → LLM analysis → LLM meta-validation/correction

Built with LangChain LCEL chains and Pydantic structured output (`with_structured_output`).

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
docs/                      # Documentation (CONTEXT.md, python_coding_rules.md, etc.)
generate.py                # Entry point: generate chat dataset
analyze.py                 # Entry point: analyze chats
tests/                     # Test suite
output/                    # Generated outputs (gitignored)
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env and add your API key
   ```

## Usage

### Step 1: Generate chats

```bash
python generate.py
```

Generates 20 synthetic support chats (5 domains × 4 case types) with deterministic scenario distribution. Output: `output/generated_chats.json`

### Step 2: Analyze chats

```bash
python analyze.py
```

Analyzes each generated chat for intent, satisfaction, quality score, and agent mistakes. Output: `output/analysis_results.json`

## Scenario Distribution

Each chat is assigned one of 5 domains and one of 4 case types:

| Domain | Case Types |
|---|---|
| Payment Issues | simple_resolved, complex_resolved, escalated, unresolved |
| Technical Errors | simple_resolved, complex_resolved, escalated, unresolved |
| Account Access | simple_resolved, complex_resolved, escalated, unresolved |
| Tariff Questions | simple_resolved, complex_resolved, escalated, unresolved |
| Refunds | simple_resolved, complex_resolved, escalated, unresolved |

Flags (hidden dissatisfaction, tonal errors, logical errors) are assigned via modular arithmetic for even distribution.

## Configuration

Environment variables (`.env`):

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `openai` | LLM provider: `openai` or `anthropic` |
| `LLM_MODEL` | `gpt-4o-mini` | Model name |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |

## Docker (Optional)

```bash
docker build -t chat-analysis .
docker run --env-file .env chat-analysis python generate.py
docker run --env-file .env -v $(pwd)/output:/app/output chat-analysis python analyze.py
```
