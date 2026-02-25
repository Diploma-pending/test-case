"""Pydantic models for context gathering."""

from pydantic import BaseModel


class GatheredContext(BaseModel):
    url: str
    raw_text: str
    context_document: str  # LLM-generated markdown
    char_count: int
