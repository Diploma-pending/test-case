"""Chat detail and single-chat analysis endpoints."""

import asyncio
import logging
import time

from fastapi import APIRouter, BackgroundTasks, HTTPException

from chat_analysis.analysis.service import analyze_single_chat
from chat_analysis.api import storage
from chat_analysis.api.models import ChatDetailResponse
from chat_analysis.core.config import get_llm
from chat_analysis.generation.models import CaseType, ChatScenario
from chat_analysis.generation.service import generate_single_chat
from chat_analysis.models import ChatDomain

router = APIRouter(prefix="/groups", tags=["chats"])

logger = logging.getLogger(__name__)


def _analyze_chat_sync(group_id: str, chat_id: str) -> None:
    """Synchronous single-chat analysis — run via asyncio.to_thread."""
    llm = get_llm()
    chat_data = storage.load_chat(group_id, chat_id)
    if chat_data is None:
        logger.error("[group=%s] [%s] Chat not found during background analysis", group_id, chat_id)
        return

    t0 = time.perf_counter()
    try:
        analysis = analyze_single_chat(chat_data, llm)
        chat_data["status"] = "analyzed"
        chat_data["analysis"] = analysis.model_dump()
        storage.save_chat(group_id, chat_id, chat_data)
        logger.info("[group=%s] [%s] Analysis complete (%.1fs)", group_id, chat_id, time.perf_counter() - t0)
    except Exception as exc:
        logger.error("[group=%s] [%s] Analysis failed: %s", group_id, chat_id, exc, exc_info=True)
        storage.update_chat_status(group_id, chat_id, "failed")


async def _run_analyze_chat(group_id: str, chat_id: str) -> None:
    await asyncio.to_thread(_analyze_chat_sync, group_id, chat_id)


def _regenerate_chat_sync(group_id: str, chat_id: str) -> None:
    """Synchronous single-chat regeneration — run via asyncio.to_thread."""
    group_data = storage.load_group(group_id)
    if group_data is None:
        logger.error("[group=%s] Group not found during regeneration", group_id)
        return

    context_str = storage.load_context(group_id)
    topic = group_data.get("topic", "")

    # Reconstruct scenario from chat_id index (same arithmetic as build_group_scenarios)
    chat_index = int(chat_id.split("_")[1]) - 1
    domains = list(ChatDomain)
    case_types = list(CaseType)
    scenario = ChatScenario(
        domain=domains[chat_index % len(domains)],
        case_type=case_types[chat_index % len(case_types)],
        has_hidden_dissatisfaction=chat_index % 4 == 1,
        has_tonal_errors=chat_index % 4 == 2,
        has_logical_errors=chat_index % 4 == 3,
    )

    llm = get_llm()
    t0 = time.perf_counter()
    try:
        chat = generate_single_chat(
            scenario,
            chat_id,
            llm,
            context_override=context_str or None,
            topic_override=topic or None,
        )
        storage.save_chat(group_id, chat_id, {
            "chat_id": chat_id,
            "status": "generated",
            "messages": [m.model_dump() for m in chat.messages],
            "analysis": None,
        })
        logger.info("[group=%s] [%s] Regeneration complete (%.1fs)", group_id, chat_id, time.perf_counter() - t0)
    except Exception as exc:
        logger.error("[group=%s] [%s] Regeneration failed: %s", group_id, chat_id, exc, exc_info=True)
        storage.update_chat_status(group_id, chat_id, "failed")


async def _run_regenerate_chat(group_id: str, chat_id: str) -> None:
    await asyncio.to_thread(_regenerate_chat_sync, group_id, chat_id)


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


@router.post("/{group_id}/chats/{chat_id}/analyze", status_code=202, response_model=ChatDetailResponse)
async def analyze_chat(
    group_id: str,
    chat_id: str,
    background_tasks: BackgroundTasks,
) -> ChatDetailResponse:
    """Trigger async analysis for a single chat. Chat must be in 'generated' or 'failed' status."""
    group_data = storage.load_group(group_id)
    if group_data is None:
        raise HTTPException(status_code=404, detail="Group not found")

    chat_data = storage.load_chat(group_id, chat_id)
    if chat_data is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    if chat_data["status"] not in {"generated", "failed"}:
        raise HTTPException(
            status_code=409,
            detail=f"Chat is not ready for analysis. Current status: {chat_data['status']}",
        )

    if not chat_data.get("messages"):
        raise HTTPException(status_code=422, detail="Chat has no messages to analyze")

    storage.update_chat_status(group_id, chat_id, "analyzing")
    background_tasks.add_task(_run_analyze_chat, group_id, chat_id)

    return ChatDetailResponse(chat_id=chat_id, status="analyzing")


@router.post("/{group_id}/chats/{chat_id}/regenerate", status_code=202, response_model=ChatDetailResponse)
async def regenerate_chat(
    group_id: str,
    chat_id: str,
    background_tasks: BackgroundTasks,
) -> ChatDetailResponse:
    """Trigger async regeneration for a single failed chat."""
    group_data = storage.load_group(group_id)
    if group_data is None:
        raise HTTPException(status_code=404, detail="Group not found")

    chat_data = storage.load_chat(group_id, chat_id)
    if chat_data is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    if chat_data["status"] != "failed":
        raise HTTPException(
            status_code=409,
            detail=f"Only failed chats can be regenerated. Current status: {chat_data['status']}",
        )

    try:
        int(chat_id.split("_")[1])
    except (IndexError, ValueError):
        raise HTTPException(status_code=422, detail="chat_id format must be chat_NNN")

    storage.update_chat_status(group_id, chat_id, "generating")
    background_tasks.add_task(_run_regenerate_chat, group_id, chat_id)

    return ChatDetailResponse(chat_id=chat_id, status="generating")
