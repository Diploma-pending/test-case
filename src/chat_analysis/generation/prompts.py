"""Prompt templates for chat generation and validation."""

from chat_analysis.generation.models import ChatScenario


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
