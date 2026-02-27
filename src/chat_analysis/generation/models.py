"""Pydantic models for the chat generation pipeline."""

from pydantic import BaseModel, Field

from chat_analysis.models import CaseType, ChatDomain, ChatMessage


class ChatScenario(BaseModel):
    """Scenario parameters that define what kind of chat to generate."""

    domain: ChatDomain = Field(description="The support topic domain")
    case_type: CaseType = Field(description="The type and outcome of the support case")
    has_hidden_dissatisfaction: bool = Field(
        description="If true, the customer is dissatisfied but does NOT express it "
        "directly — they use polite language while being unhappy"
    )
    has_tonal_errors: bool = Field(
        description="If true, the agent makes tone/style mistakes "
        "(e.g., too informal, dismissive, robotic)"
    )
    has_logical_errors: bool = Field(
        description="If true, the agent makes logical mistakes "
        "(e.g., wrong information, contradictions, skipped steps)"
    )


class StructuredContext(BaseModel):
    """LLM-extracted product reference with structured sections from raw context."""

    product_name: str = Field(description="The product or service name")
    business_summary: str = Field(description="Brief overview of the business and target customers")
    plans_and_pricing: str = Field(
        description="Subscription tiers, pricing, billing cycles, trial offers"
    )
    billing_and_payments: str = Field(
        description="Accepted payment methods, auto-renewal, failed payment handling"
    )
    refund_policy: str = Field(
        description="Refund eligibility, timeframes, process, exceptions"
    )
    account_and_security: str = Field(
        description="Login methods, account recovery, 2FA, suspension policies"
    )
    technical_platform: str = Field(
        description="Platforms supported, integrations, common technical issues"
    )
    known_issues_and_edge_cases: str = Field(
        description="Frequently reported problems, edge cases, emotionally charged scenarios"
    )
    escalation_rules: str = Field(
        description="When to escalate, escalation tiers, SLA commitments"
    )
    tone_guidelines: str = Field(
        description="Expected agent tone, empathy rules, brand voice"
    )
    valid_entities: list[str] = Field(
        description="Allowed vocabulary of real entity names: plan names, feature names, "
        "error codes, department names, URLs, etc. Conversations must only reference "
        "entities from this list."
    )

    def to_prompt_text(self) -> str:
        """Format structured context as a readable prompt section."""
        entities_str = ", ".join(self.valid_entities) if self.valid_entities else "None specified"
        return (
            f"## Product: {self.product_name}\n\n"
            f"### Business Summary\n{self.business_summary}\n\n"
            f"### Plans & Pricing\n{self.plans_and_pricing}\n\n"
            f"### Billing & Payments\n{self.billing_and_payments}\n\n"
            f"### Refund Policy\n{self.refund_policy}\n\n"
            f"### Account & Security\n{self.account_and_security}\n\n"
            f"### Technical Platform\n{self.technical_platform}\n\n"
            f"### Known Issues & Edge Cases\n{self.known_issues_and_edge_cases}\n\n"
            f"### Escalation Rules\n{self.escalation_rules}\n\n"
            f"### Tone Guidelines\n{self.tone_guidelines}\n\n"
            f"### Valid Entities (allowed vocabulary)\n{entities_str}"
        )


class AgentErrorPlan(BaseModel):
    """A planned agent error to be injected into the conversation."""

    error_type: str = Field(description="Type of error: 'tonal' or 'logical'")
    description: str = Field(
        description="Specific description of the error to make, "
        "e.g. 'Use dismissive language when customer explains the problem'"
    )
    target_message_index: int = Field(
        description="Approximate message index (0-based) where this error should appear"
    )


class ScenarioBrief(BaseModel):
    """Rich scenario brief that guides conversation writing."""

    customer_persona: str = Field(
        description="Persona code (P1-P8): P1=frustrated-verbose, P2=polite-concise, "
        "P3=tech-savvy-impatient, P4=elderly-confused, P5=passive-aggressive, "
        "P6=first-time-user, P7=returning-complainer, P8=business-professional"
    )
    communication_style: str = Field(
        description="How the customer communicates: formal, casual, terse, rambling, etc."
    )
    customer_situation: str = Field(
        description="Specific situation the customer is in, including relevant details "
        "like what product/plan they have, what went wrong, and their goal"
    )
    urgency_level: str = Field(
        description="How urgent this is for the customer: low, medium, high, critical"
    )
    emotional_arc: str = Field(
        description="How the customer's emotional state evolves through the conversation, "
        "e.g. 'frustrated → reassured → satisfied' or 'calm → confused → resigned'"
    )
    agent_error_plan: list[AgentErrorPlan] = Field(
        default_factory=list,
        description="Planned agent errors to inject (empty for clean interactions)",
    )
    required_entities: list[str] = Field(
        description="Specific entity names from valid_entities that MUST appear in the conversation"
    )
    target_message_count: int = Field(
        description="Target number of messages for this conversation"
    )
    target_outcome: str = Field(
        description="How the conversation should end: 'resolved', 'escalated', 'unresolved'"
    )

    def to_prompt_text(self) -> str:
        """Format brief as a readable prompt section."""
        errors_str = "None (clean interaction)"
        if self.agent_error_plan:
            errors_str = "\n".join(
                f"  - [{e.error_type}] at ~message {e.target_message_index}: {e.description}"
                for e in self.agent_error_plan
            )
        return (
            f"## Scenario Brief\n\n"
            f"**Customer Persona**: {self.customer_persona}\n"
            f"**Communication Style**: {self.communication_style}\n"
            f"**Situation**: {self.customer_situation}\n"
            f"**Urgency**: {self.urgency_level}\n"
            f"**Emotional Arc**: {self.emotional_arc}\n"
            f"**Target Messages**: {self.target_message_count}\n"
            f"**Target Outcome**: {self.target_outcome}\n\n"
            f"**Required Entities**: {', '.join(self.required_entities)}\n\n"
            f"**Agent Error Plan**:\n{errors_str}"
        )


class GeneratedChat(BaseModel):
    """A single generated support chat with its scenario metadata."""

    chat_id: str = Field(description="Unique identifier for this chat, e.g. 'chat_001'")
    scenario: ChatScenario = Field(description="The scenario parameters used to generate this chat")
    messages: list[ChatMessage] = Field(
        description="The conversation messages in chronological order, "
        "alternating between customer and agent. "
        "Must start with a customer message. Minimum 6 messages."
    )


class GeneratedDataset(BaseModel):
    """Collection of generated support chats."""

    chats: list[GeneratedChat] = Field(description="List of generated support chats")


class ChatValidationResult(BaseModel):
    """Result of validating a generated chat against its scenario requirements."""

    is_valid: bool = Field(
        description="Whether the generated chat correctly follows all scenario requirements"
    )
    issues: list[str] = Field(
        default_factory=list,
        description="List of specific issues found (empty if valid)",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Suggestions for improving the chat to match the scenario better",
    )
    entity_accuracy: bool = Field(
        default=True,
        description="Whether all entity names match the valid_entities list",
    )
    pii_placeholders_used: bool = Field(
        default=True,
        description="Whether PII placeholders are used instead of real personal data",
    )
    persona_match: bool = Field(
        default=True,
        description="Whether the customer voice matches the assigned persona",
    )
    emotional_arc_match: bool = Field(
        default=True,
        description="Whether the emotional arc matches the brief",
    )
    agent_errors_as_planned: bool = Field(
        default=True,
        description="Whether agent errors appear as specified in the error plan",
    )
