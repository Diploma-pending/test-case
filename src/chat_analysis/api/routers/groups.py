"""Group endpoints: create, trigger analysis, list chats."""

import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from chat_analysis.analysis.service import analyze_single_chat
from chat_analysis.api import storage
from chat_analysis.api.models import (
    ChatSummary,
    GroupAnalyzeResponse,
    GroupChatsResponse,
    GroupCreateResponse,
)
from chat_analysis.core.config import get_llm
from chat_analysis.core.security import sanitize_text
from chat_analysis.generation.models import CaseType, ChatScenario
from chat_analysis.generation.service import generate_single_chat
from chat_analysis.models import ChatDomain

router = APIRouter(prefix="/groups", tags=["groups"])

MAX_CONTEXT_SIZE = 1 * 1024 * 1024  # 1 MB


def build_group_scenarios(num_chats: int) -> list[ChatScenario]:
    """Build a list of scenarios for a custom group by cycling through case types.

    Uses the same modular arithmetic for flags as build_scenario_matrix().
    Domain is set to PAYMENT_ISSUES as a placeholder (overridden by context_override).
    """
    case_types = list(CaseType)
    scenarios = []
    for i in range(num_chats):
        case_type = case_types[i % len(case_types)]
        scenarios.append(
            ChatScenario(
                domain=ChatDomain.PAYMENT_ISSUES,
                case_type=case_type,
                has_hidden_dissatisfaction=i % 4 == 1,
                has_tonal_errors=i % 4 == 2,
                has_logical_errors=i % 4 == 3,
            )
        )
    return scenarios


def _generate_group_sync(group_id: str, topic: str, context_str: str, num_chats: int) -> None:
    """Synchronous generation task — run via asyncio.to_thread."""
    scenarios = build_group_scenarios(num_chats)
    llm = get_llm()

    # Pre-create all chat records so the FE can see them immediately
    for i, scenario in enumerate(scenarios):
        chat_id = f"chat_{i + 1:03d}"
        storage.save_chat(group_id, chat_id, {
            "chat_id": chat_id,
            "case_type": scenario.case_type.value,
            "status": "pending",
            "messages": None,
            "scenario": None,
            "analysis": None,
        })

    try:
        for i, scenario in enumerate(scenarios):
            chat_id = f"chat_{i + 1:03d}"
            storage.update_chat_status(group_id, chat_id, "generating")
            try:
                chat = generate_single_chat(
                    scenario,
                    chat_id,
                    llm,
                    context_override=context_str,
                    topic_override=topic,
                )
                storage.save_chat(group_id, chat_id, {
                    "chat_id": chat_id,
                    "case_type": scenario.case_type.value,
                    "status": "generated",
                    "messages": [m.model_dump() for m in chat.messages],
                    "scenario": chat.scenario.model_dump(),
                    "analysis": None,
                })
            except Exception:
                storage.update_chat_status(group_id, chat_id, "failed")

        group_data = storage.load_group(group_id)
        group_data["status"] = "generated"
        storage.save_group(group_id, group_data)

    except Exception:
        group_data = storage.load_group(group_id)
        group_data["status"] = "generation_failed"
        storage.save_group(group_id, group_data)
        raise


def _analyze_group_sync(group_id: str) -> None:
    """Synchronous analysis task — run via asyncio.to_thread."""
    llm = get_llm()
    chats = storage.load_all_chats(group_id)

    try:
        for chat_data in chats:
            chat_id = chat_data["chat_id"]

            if not chat_data.get("messages"):
                storage.update_chat_status(group_id, chat_id, "failed")
                continue

            storage.update_chat_status(group_id, chat_id, "analyzing")
            try:
                analysis = analyze_single_chat(chat_data, llm)
                chat_data["status"] = "analyzed"
                chat_data["analysis"] = analysis.model_dump()
                storage.save_chat(group_id, chat_id, chat_data)
            except Exception:
                storage.update_chat_status(group_id, chat_id, "failed")

        group_data = storage.load_group(group_id)
        group_data["status"] = "completed"
        storage.save_group(group_id, group_data)

    except Exception:
        group_data = storage.load_group(group_id)
        group_data["status"] = "analysis_failed"
        storage.save_group(group_id, group_data)
        raise


async def _run_generate_group(group_id: str, topic: str, context_str: str, num_chats: int) -> None:
    await asyncio.to_thread(_generate_group_sync, group_id, topic, context_str, num_chats)


async def _run_analyze_group(group_id: str) -> None:
    await asyncio.to_thread(_analyze_group_sync, group_id)


@router.post("", status_code=202, response_model=GroupCreateResponse)
async def create_group(
    background_tasks: BackgroundTasks,
    topic: str = Form(...),
    context_file: UploadFile = File(...),
    num_chats: int = Form(default=8),
) -> GroupCreateResponse:
    """Create a new chat group from a topic and context file, then generate chats in the background."""
    if not context_file.filename or not context_file.filename.endswith(".md"):
        raise HTTPException(status_code=422, detail="context_file must be a .md file")

    content = await context_file.read()
    if len(content) > MAX_CONTEXT_SIZE:
        raise HTTPException(status_code=422, detail="context_file must be ≤ 1 MB")

    context_str = sanitize_text(content.decode("utf-8", errors="replace"))

    group_id = str(uuid.uuid4())
    group_data = {
        "group_id": group_id,
        "topic": topic,
        "status": "generating",
        "num_chats": num_chats,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    storage.save_group(group_id, group_data)
    storage.save_context(group_id, context_str)

    background_tasks.add_task(_run_generate_group, group_id, topic, context_str, num_chats)

    return GroupCreateResponse(group_id=group_id, status="generating", num_chats=num_chats)


@router.post("/{group_id}/analyze", status_code=202, response_model=GroupAnalyzeResponse)
async def analyze_group(
    group_id: str,
    background_tasks: BackgroundTasks,
) -> GroupAnalyzeResponse:
    """Trigger async analysis for a generated group. Group must be in 'generated' status."""
    group_data = storage.load_group(group_id)
    if group_data is None:
        raise HTTPException(status_code=404, detail="Group not found")

    if group_data["status"] != "generated":
        raise HTTPException(
            status_code=409,
            detail=f"Group is not ready for analysis. Current status: {group_data['status']}",
        )

    # Set all chats to "analyzing" immediately so the FE sees the transition at once
    for chat in storage.load_all_chats(group_id):
        chat["status"] = "analyzing"
        storage.save_chat(group_id, chat["chat_id"], chat)

    group_data["status"] = "analyzing"
    storage.save_group(group_id, group_data)

    background_tasks.add_task(_run_analyze_group, group_id)

    return GroupAnalyzeResponse(group_id=group_id, status="analyzing")


@router.get("/{group_id}/chats", response_model=GroupChatsResponse)
async def get_group_chats(group_id: str) -> GroupChatsResponse:
    """Return group status and a summary list of all chats (no full messages — lightweight for polling)."""
    group_data = storage.load_group(group_id)
    if group_data is None:
        raise HTTPException(status_code=404, detail="Group not found")

    chats = storage.load_all_chats(group_id)
    chat_summaries = [
        ChatSummary(
            chat_id=c["chat_id"],
            case_type=c["case_type"],
            status=c["status"],
            analysis=c.get("analysis"),
        )
        for c in chats
    ]

    return GroupChatsResponse(
        group_id=group_data["group_id"],
        topic=group_data["topic"],
        status=group_data["status"],
        num_chats=group_data["num_chats"],
        created_at=group_data["created_at"],
        chats=chat_summaries,
    )
