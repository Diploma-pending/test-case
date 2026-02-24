"""Pydantic models for the chat analysis pipeline."""

from typing import Optional

from pydantic import BaseModel, Field

from chat_analysis.models import SatisfactionLevel


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
