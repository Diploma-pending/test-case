"""Prompt templates for chat generation, validation, and analysis."""

from models import ChatScenario


def build_special_requirements(scenario: ChatScenario) -> str:
    """Build dynamic prompt section based on scenario flags."""
    requirements = []

    if scenario.has_hidden_dissatisfaction:
        requirements.append(
            "- HIDDEN DISSATISFACTION: The customer is unhappy but does NOT say so directly. "
            "They use polite, neutral, or passive-aggressive language. They might say "
            "'I see', 'Okay, I understand', 'Sure, if that's the policy' while being "
            "frustrated inside. They do NOT use exclamation marks of anger or direct complaints. "
            "The dissatisfaction must be subtle — detectable only through context "
            "(e.g., unresolved issue, short replies, lack of enthusiasm)."
        )

    if scenario.has_tonal_errors:
        requirements.append(
            "- AGENT TONAL ERRORS: The agent makes at least 1-2 tone/style mistakes. "
            "Examples: being too informal ('lol', 'nah'), overly robotic/template-like "
            "responses, dismissive language ('that's not really our problem'), "
            "lacking empathy when customer is upset, using jargon the customer doesn't understand."
        )

    if scenario.has_logical_errors:
        requirements.append(
            "- AGENT LOGICAL ERRORS: The agent makes at least 1-2 factual or procedural mistakes. "
            "Examples: giving wrong information, contradicting themselves, skipping required "
            "verification steps, suggesting a solution that doesn't match the problem, "
            "promising something they can't deliver, misunderstanding the customer's issue."
        )

    if not requirements:
        requirements.append(
            "- CLEAN INTERACTION: The agent should be professional, empathetic, and accurate. "
            "The customer should express satisfaction naturally if the issue is resolved."
        )

    return "\n".join(requirements)


# --- Generation prompt ---

GENERATE_SYSTEM_TEMPLATE = """\
You are a support chat simulator. Generate a realistic customer support chat conversation.

## Scenario
- Domain: {domain}
- Case type: {case_type}
- Chat ID: {chat_id}

## Domain Context
{domain_context}

## Requirements
1. The conversation must have at least 6 messages, alternating between customer and agent.
2. Start with a customer message describing their issue.
3. The case type is "{case_type}":
   - simple_resolved: straightforward issue, agent resolves it quickly (3-5 exchanges)
   - complex_resolved: multi-step issue, requires investigation, eventually resolved (5-8 exchanges)
   - escalated: agent cannot fully resolve, escalates to a specialist or higher tier
   - unresolved: issue remains unresolved by the end of the conversation

## Special Requirements
{special_requirements}

## Style
- Use natural, varied language — not template-like.
- Customer messages should feel authentic (typos are okay, varied sentence lengths).
- Agent messages should follow support conventions (greeting, empathy, solution, closing).
- Include realistic details (order numbers, dates, error codes) relevant to the domain.
"""

# --- Validation prompt ---

VALIDATE_SYSTEM_TEMPLATE = """\
You are a quality assurance reviewer for generated support chat conversations.

Validate the following generated chat against its scenario requirements.

## Scenario Requirements
- Domain: {domain}
- Case type: {case_type}
- Hidden dissatisfaction: {has_hidden_dissatisfaction}
- Tonal errors by agent: {has_tonal_errors}
- Logical errors by agent: {has_logical_errors}

## Special Requirements Detail
{special_requirements}

## Chat to Validate
{chat_json}

## Validation Criteria
1. Does the conversation start with a customer message?
2. Do messages alternate between customer and agent?
3. Is there a minimum of 6 messages?
4. Does the case type match? (e.g., is it actually resolved/escalated/unresolved?)
5. If hidden dissatisfaction is required: is the customer polite on the surface but subtly unhappy? \
(NOT overtly angry)
6. If tonal errors are required: does the agent make clear tone/style mistakes?
7. If logical errors are required: does the agent make factual/procedural mistakes?
8. If NO errors are required: is the agent professional and accurate?
9. Is the domain/topic consistent throughout?
"""

# --- Analysis prompt ---

ANALYZE_SYSTEM_TEMPLATE = """\
You are a support chat quality analyst. Analyze the following customer support conversation.

## Chat to Analyze
Chat ID: {chat_id}
{chat_messages}

## Analysis Instructions

### 1. Intent
Identify the primary customer intent. Use a concise label like:
- request_refund, report_payment_failure, dispute_charge
- report_bug, app_crash, feature_not_working
- password_reset, account_locked, account_deletion
- plan_comparison, upgrade_request, billing_question
- refund_status, refund_request, partial_refund

### 2. Satisfaction
Determine customer satisfaction level:
- "satisfied": Customer is genuinely happy with the resolution
- "neutral": Customer accepts the outcome but without enthusiasm
- "unsatisfied": Customer is unhappy

**CRITICAL — HIDDEN DISSATISFACTION DETECTION:**
Pay close attention to these signals:
- Customer says "okay" or "I see" but their issue is NOT actually resolved
- Customer stops pushing back but the problem remains
- Short, terse replies after a long explanation
- Polite words with no warmth ("Sure, if that's the policy")
- Customer accepts an escalation or delay without expressing genuine satisfaction
- Agent made mistakes but customer didn't call them out

If ANY of these signals are present, do NOT mark as "satisfied". Use "neutral" or "unsatisfied".

### 3. Quality Score (1-10)
Rate the agent's performance:
- Start at 8 (baseline for adequate support)
- Deduct: tonal errors (-1 to -2), logical errors (-2 to -3), unresolved issues (-2), \
lack of empathy (-1)
- Add: exceptional empathy (+1), creative problem solving (+1)

### 4. Agent Mistakes
List each specific mistake with:
- type: "tonal" or "logical"
- description: what went wrong
- message_index: which message (0-based index)

### 5. Reasoning
Explain your assessment in 2-3 sentences, specifically addressing any hidden dissatisfaction signals.
"""

# --- Analysis validation prompt ---

ANALYZE_VALIDATE_TEMPLATE = """\
You are a meta-reviewer validating a chat analysis for correctness and completeness.

## Original Chat
Chat ID: {chat_id}
{chat_messages}

## Analysis to Validate
{analysis_json}

## Validation Instructions
Review the analysis and correct any errors:

1. **Intent**: Is the identified intent accurate and specific enough?
2. **Satisfaction**: Is the satisfaction level correct?
   - CRITICAL: If the customer shows ANY signs of hidden dissatisfaction (polite but unresolved, \
terse replies, passive acceptance), satisfaction MUST NOT be "satisfied"
   - If agent made mistakes, satisfaction should typically be "neutral" or "unsatisfied"
3. **Quality Score**: Is it calibrated correctly given the mistakes found?
   - Cross-check: if mistakes list is non-empty, score should be < 8
   - If no mistakes found, score should be >= 7
4. **Agent Mistakes**: Are all mistakes identified? Are there any missed?
   - Re-read each agent message looking for tonal and logical issues
5. **Reasoning**: Does it accurately explain the assessment?

Return the corrected analysis. If no corrections are needed, return the original analysis unchanged.
"""
