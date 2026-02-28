# Project Context: Support Chat Quality Analysis System

## Task Origin
AI Test Task — automate support quality analysis.

## Goal
1. Generate a synthetic dataset of customer ↔ support-agent chats
2. Analyze each chat and return structured JSON results

## Required Chat Domains
- payment_issues
- technical_errors
- account_access
- tariff_questions
- refunds

## Required Case Types per Domain
- successful (simple_resolved, complex_resolved)
- problematic (escalated)
- conflicted / unresolved
- agent mistake cases

## Key Generation Requirements
- Some chats must contain **hidden dissatisfaction** (customer formally thanks but issue is unresolved)
- Some chats must contain **tonal or logical agent errors**
- Results must be **deterministic**
- **LLM usage is mandatory**

## Analysis Output (JSON per chat)
```json
{
  "intent": "<domain | other>",
  "satisfaction": "satisfied | neutral | unsatisfied",
  "quality_score": 1-5,
  "agent_mistakes": ["ignored_question", "incorrect_info", "rude_tone", "no_resolution", "unnecessary_escalation"]
}
```

## Evaluation Criteria
- Chat diversity & realism
- Hidden dissatisfaction detection
- Correct intent classification
- Quality scoring logic
- Agent mistake detection
- Code cleanliness
