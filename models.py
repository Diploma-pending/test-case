"""Pydantic data models shared between generation and analysis scripts."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of the message sender in a support chat."""

    CUSTOMER = "customer"
    AGENT = "agent"


class ChatDomain(str, Enum):
    """Support chat topic domains."""

    PAYMENT_ISSUES = "payment_issues"
    TECHNICAL_ERRORS = "technical_errors"
    ACCOUNT_ACCESS = "account_access"
    TARIFF_QUESTIONS = "tariff_questions"
    REFUNDS = "refunds"


class CaseType(str, Enum):
    """Types of support cases by complexity and outcome."""

    SIMPLE_RESOLVED = "simple_resolved"
    COMPLEX_RESOLVED = "complex_resolved"
    ESCALATED = "escalated"
    UNRESOLVED = "unresolved"


class SatisfactionLevel(str, Enum):
    """Customer satisfaction level after the chat."""

    SATISFIED = "satisfied"
    NEUTRAL = "neutral"
    UNSATISFIED = "unsatisfied"


# --- Generation models ---


class ChatMessage(BaseModel):
    """A single message in a support chat conversation."""

    role: MessageRole = Field(description="Who sent this message: 'customer' or 'agent'")
    text: str = Field(description="The message content text")


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


# --- Analysis models ---


class AgentMistake(BaseModel):
    """A specific mistake made by the support agent."""

    type: str = Field(
        description="Category of mistake: 'tonal' (style/tone issue) "
        "or 'logical' (factual/procedural error)"
    )
    description: str = Field(description="Detailed description of what the agent did wrong")
    message_index: int = Field(
        description="Index of the message (0-based) where the mistake occurred"
    )


class ChatAnalysis(BaseModel):
    """Complete analysis of a single support chat."""

    chat_id: str = Field(description="ID of the analyzed chat")
    intent: str = Field(
        description="The primary customer intent/reason for contacting support, "
        "e.g. 'request_refund', 'report_payment_failure', 'password_reset'"
    )
    satisfaction: SatisfactionLevel = Field(
        description="Customer satisfaction level. Pay special attention to HIDDEN "
        "dissatisfaction — if the customer uses polite words but their issue is "
        "unresolved, they are escalating, or agent made mistakes, "
        "mark as 'unsatisfied' or 'neutral', NOT 'satisfied'"
    )
    quality_score: int = Field(
        description="Overall agent quality score from 1 to 10, where 10 is perfect. "
        "Deduct points for: tonal errors (-1 to -2 each), logical errors (-2 to -3 each), "
        "unresolved issues (-2), lack of empathy (-1)"
    )
    agent_mistakes: list[AgentMistake] = Field(
        default_factory=list,
        description="List of specific mistakes the agent made (empty if none)",
    )
    reasoning: str = Field(
        description="Brief explanation of why this satisfaction level and quality score "
        "were assigned, specifically noting any hidden dissatisfaction signals"
    )


class AnalysisValidationResult(BaseModel):
    """Result of validating an analysis for correctness."""

    original_analysis: ChatAnalysis = Field(description="The original analysis being validated")
    is_correct: bool = Field(
        description="Whether the original analysis is correct and complete"
    )
    corrections: Optional[str] = Field(
        default=None,
        description="Description of what needs to be corrected, if anything",
    )
    corrected_analysis: ChatAnalysis = Field(
        description="The corrected analysis (same as original if no corrections needed)"
    )


class AnalysisDataset(BaseModel):
    """Collection of chat analyses."""

    analyses: list[ChatAnalysis] = Field(description="List of chat analysis results")
