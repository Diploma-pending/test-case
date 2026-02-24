"""Shared Pydantic models and enums used across generation and analysis."""

from enum import Enum

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


class ChatMessage(BaseModel):
    """A single message in a support chat conversation."""

    role: MessageRole = Field(description="Who sent this message: 'customer' or 'agent'")
    text: str = Field(description="The message content text")
