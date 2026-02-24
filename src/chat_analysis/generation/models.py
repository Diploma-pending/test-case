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
