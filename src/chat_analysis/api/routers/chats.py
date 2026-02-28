"""Chat detail endpoint."""

from fastapi import APIRouter, HTTPException

from chat_analysis.api import storage
from chat_analysis.api.models import ChatDetailResponse

router = APIRouter(prefix="/groups", tags=["chats"])


@router.get("/{group_id}/chats/{chat_id}", response_model=ChatDetailResponse)
async def get_chat_detail(group_id: str, chat_id: str) -> ChatDetailResponse:
    """Return full chat detail including messages and analysis."""
    group_data = storage.load_group(group_id)
    if group_data is None:
        raise HTTPException(status_code=404, detail="Group not found")

    chat_data = storage.load_chat(group_id, chat_id)
    if chat_data is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    return ChatDetailResponse(
        chat_id=chat_data["chat_id"],
        status=chat_data["status"],
        messages=chat_data.get("messages"),
        analysis=chat_data.get("analysis"),
    )
