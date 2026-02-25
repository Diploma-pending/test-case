"""API request/response Pydantic schemas."""

from typing import Any, Optional

from pydantic import BaseModel


class GroupCreateResponse(BaseModel):
    group_id: str
    status: str
    num_chats: int


class GroupAnalyzeResponse(BaseModel):
    group_id: str
    status: str


class ChatSummary(BaseModel):
    chat_id: str
    case_type: str
    status: str
    analysis: Optional[dict[str, Any]] = None


class GroupChatsResponse(BaseModel):
    group_id: str
    topic: str
    status: str
    num_chats: int
    created_at: str
    chats: list[ChatSummary]


class ChatDetailResponse(BaseModel):
    chat_id: str
    case_type: str
    status: str
    messages: Optional[list[dict[str, Any]]] = None
    scenario: Optional[dict[str, Any]] = None
    analysis: Optional[dict[str, Any]] = None
