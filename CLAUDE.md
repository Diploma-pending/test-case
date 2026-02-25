# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Setup
```bash
pip install -r requirements.txt
cp .env.example .env  # then add your API key
```

### Run
```bash
python generate.py   # Step 1: generate 20 chats → output/generated_chats.json
python analyze.py    # Step 2: analyze chats → output/analysis_results.json
```

### Docker
```bash
docker build -t chat-analysis .
docker run --env-file .env chat-analysis python generate.py
docker run --env-file .env -v $(pwd)/output:/app/output chat-analysis python analyze.py
```

### Tests
```bash
pytest tests/
```

The tests directory currently only contains `__init__.py` (no tests yet). Tests should be added to `tests/`.

## Architecture

The system has two sequential pipelines, each using a **two-step LangChain LCEL chain** pattern: generate/analyze → validate/correct.

### Generation pipeline (`generate.py` → `src/chat_analysis/generation/`)

1. `build_scenario_matrix()` creates 20 deterministic scenarios (5 domains × 4 case types), assigning flags (hidden dissatisfaction, tonal errors, logical errors) via modular arithmetic (`idx % 4`).
2. Per scenario: `generate_chain = prompt | llm.with_structured_output(GeneratedChat)` generates a chat, then `validate_chain = prompt | llm.with_structured_output(ChatValidationResult)` validates it. Retries up to `MAX_RETRIES` (3) times on failure.
3. Domain-specific context is loaded from `context/<domain>.md` via `security.load_context_safely()`, which also sanitizes prompt injection patterns.
4. Brand-specific support context is loaded from `domains/<brand>.md` to ground generated chats in realistic product details, policies, and edge cases.

### Analysis pipeline (`analyze.py` → `src/chat_analysis/analysis/`)

1. Loads `output/generated_chats.json`, sanitizes each message via `security.sanitize_text()`.
2. Per chat: `analyze_chain = prompt | llm.with_structured_output(ChatAnalysis)` produces initial analysis, then `validate_chain = prompt | llm.with_structured_output(AnalysisValidationResult)` may correct it.
3. Saves results to `output/analysis_results.json`.

### Package layout

```
src/chat_analysis/
├── models.py              # Shared enums: MessageRole, ChatDomain, CaseType, SatisfactionLevel + ChatMessage
├── core/
│   ├── config.py          # get_llm() factory; BASE_DIR, OUTPUT_DIR, CONTEXT_DIR paths; NUM_CHATS_PER_DOMAIN, MAX_RETRIES
│   └── security.py        # sanitize_text(), validate_context_file(), load_context_safely()
├── generation/
│   ├── models.py          # ChatScenario, GeneratedChat, GeneratedDataset, ChatValidationResult
│   ├── prompts.py         # GENERATE_SYSTEM_TEMPLATE, VALIDATE_SYSTEM_TEMPLATE, build_special_requirements()
│   └── service.py         # build_scenario_matrix(), generate_single_chat(), main()
└── analysis/
    ├── models.py          # AgentMistake, ChatAnalysis, AnalysisValidationResult, AnalysisDataset
    ├── prompts.py         # ANALYZE_SYSTEM_TEMPLATE, ANALYZE_VALIDATE_TEMPLATE
    └── service.py         # analyze_single_chat(), main()
```

## Domain Context Files

The `domains/` directory contains brand-specific support context documents used to make generated chats realistic. Each file covers:
- Business overview, pricing tiers, and key features
- Support domain context per category (payment, technical, account, tariff, refunds)
- Support policies, SLAs, and self-service options
- Edge cases and emotionally charged scenarios
- Agent pitfall areas (common mistakes to model in problematic chats)

Available brand contexts:

| File | Brand |
|---|---|
| `domains/brighterly.md` | Brighterly — online math tutoring for kids |
| `domains/dressly.md` | Dressly — fashion/clothing subscription |
| `domains/howly.md` | Howly — on-demand expert Q&A platform |
| `domains/liven.md` | Liven — CBT-based mental health & well-being app |
| `domains/maxbeauty.md` | MaxBeauty — beauty/cosmetics e-commerce |
| `domains/pawchamp.md` | PawChamp — dog training & care platform |
| `domains/relatio.md` | Relatio — relationship coaching app |
| `domains/riseguide.md` | RiseGuide — personal development & coaching |
| `domains/storyby.md` | Storyby — personalized children's storybooks |

These files are injected into generation prompts alongside the support-category context from `context/<domain>.md`.

## Configuration

Environment variables in `.env`:

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai`, `anthropic`, or `google` |
| `LLM_MODEL` | `gpt-4o-mini` | Model name |
| `OPENAI_API_KEY` | — | Required when provider is `openai` |
| `ANTHROPIC_API_KEY` | — | Required when provider is `anthropic` |

`LLM_TEMPERATURE` is hardcoded to `0` and `seed=42` for OpenAI to ensure deterministic output.

## Coding Standards

See `python_coding_rules.md` for full standards. Key rules:
- **Python 3.11+**, Black (88-char lines), Ruff, mypy/Pyright, pytest
- `snake_case` for functions/variables, `CapWords` for classes, `UPPER_SNAKE_CASE` for constants
- Standard library → third-party → local import ordering (Ruff `I` rule enforces this)
- Explicit dependency injection (pass `llm` into functions, don't create globals)
- Full type annotations on all public functions
