"""API request/response Pydantic schemas."""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class BusinessContext(str, Enum):
    """Preset Scalara business context from src/chat_analysis/data/domains/ or custom user-provided context."""

    BRIGHTERLY = "brighterly"
    DRESSLY = "dressly"
    HOWLY = "howly"
    LIVEN = "liven"
    MAXBEAUTY = "maxbeauty"
    PAWCHAMP = "pawchamp"
    RELATIO = "relatio"
    RISEGUIDE = "riseguide"
    STORYBY = "storyby"
    CUSTOM = "custom"


class GroupCreateResponse(BaseModel):
    group_id: str
    status: str
    num_chats: int


class GroupAnalyzeResponse(BaseModel):
    group_id: str
    status: str


class ChatSummary(BaseModel):
    chat_id: str
    status: str
    analysis: Optional[dict[str, Any]] = None


class BusinessContextItem(BaseModel):
    """Single business context option for UI dropdown."""

    id: str
    label: str


class GroupChatsResponse(BaseModel):
    group_id: str
    topic: str
    status: str
    num_chats: int
    created_at: str
    chats: list[ChatSummary]
    website_url: Optional[str] = None
    context_gathering_error: Optional[str] = None
    business: Optional[str] = None


class GroupSummary(BaseModel):
    group_id: str
    topic: str
    status: str
    num_chats: int
    created_at: str
    website_url: Optional[str] = None
    context_gathering_error: Optional[str] = None
    business: Optional[str] = None


class ChatDetailResponse(BaseModel):
    chat_id: str
    status: str
    messages: Optional[list[dict[str, Any]]] = None
    analysis: Optional[dict[str, Any]] = None
