"""Group endpoints: create, trigger analysis, list chats."""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from chat_analysis.analysis.service import analyze_single_chat
from chat_analysis.api import storage
from chat_analysis.api.models import (
    ChatSummary,
    GroupAnalyzeResponse,
    GroupChatsResponse,
    GroupCreateResponse,
)
from chat_analysis.context_gathering.service import ContextGatheringError, gather_context
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


def _combine_contexts(file_context: str, website_context: str, website_url: str) -> str:
    """Merge uploaded file context with website-gathered context.

    If both are present: file context first, separator, then website context.
    If only one is non-empty: return that one.
    """
    has_file = bool(file_context and file_context.strip())
    has_web = bool(website_context and website_context.strip())

    if has_file and has_web:
        return (
            f"{file_context}\n\n---\n\n"
            f"## Context gathered from {website_url}\n\n{website_context}"
        )
    if has_file:
        return file_context
    return website_context


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


def _gather_and_generate_sync(
    group_id: str,
    topic: str,
    file_context: str,
    website_url: str,
    num_chats: int,
) -> None:
    """Gather context from website, merge with file context, then generate chats."""
    llm = get_llm()

    try:
        gathered = gather_context(website_url, llm)
        website_context = gathered.context_document
    except ContextGatheringError as exc:
        group_data = storage.load_group(group_id)
        group_data["status"] = "context_gathering_failed"
        group_data["context_gathering_error"] = str(exc)
        storage.save_group(group_id, group_data)
        return

    merged = _combine_contexts(file_context, website_context, website_url)
    storage.save_context(group_id, merged)

    group_data = storage.load_group(group_id)
    group_data["status"] = "generating"
    storage.save_group(group_id, group_data)

    _generate_group_sync(group_id, topic, merged, num_chats)


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


async def _run_gather_and_generate_group(
    group_id: str,
    topic: str,
    file_context: str,
    website_url: str,
    num_chats: int,
) -> None:
    await asyncio.to_thread(
        _gather_and_generate_sync, group_id, topic, file_context, website_url, num_chats
    )


async def _run_analyze_group(group_id: str) -> None:
    await asyncio.to_thread(_analyze_group_sync, group_id)


@router.post("", status_code=202, response_model=GroupCreateResponse)
async def create_group(
    background_tasks: BackgroundTasks,
    topic: str = Form(...),
    context_file: Optional[UploadFile] = File(None),
    website_url: Optional[str] = Form(None),
    num_chats: int = Form(default=8),
) -> GroupCreateResponse:
    """Create a new chat group from a topic and context source, then generate chats in the background.

    Provide either context_file (.md), website_url, or both.
    """
    if context_file is None and website_url is None:
        raise HTTPException(
            status_code=422,
            detail="Provide at least one of: context_file (.md) or website_url",
        )

    # Eager URL format validation before creating the group
    if website_url is not None:
        parsed = urlparse(website_url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise HTTPException(
                status_code=422,
                detail="website_url must be a valid http or https URL with a hostname",
            )

    file_context = ""
    if context_file is not None:
        if not context_file.filename or not context_file.filename.endswith(".md"):
            raise HTTPException(status_code=422, detail="context_file must be a .md file")
        content = await context_file.read()
        if len(content) > MAX_CONTEXT_SIZE:
            raise HTTPException(status_code=422, detail="context_file must be ≤ 1 MB")
        file_context = sanitize_text(content.decode("utf-8", errors="replace"))

    group_id = str(uuid.uuid4())
    initial_status = "gathering_context" if website_url else "generating"

    group_data = {
        "group_id": group_id,
        "topic": topic,
        "status": initial_status,
        "num_chats": num_chats,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "website_url": website_url,
        "context_gathering_error": None,
    }
    storage.save_group(group_id, group_data)

    if website_url:
        background_tasks.add_task(
            _run_gather_and_generate_group,
            group_id,
            topic,
            file_context,
            website_url,
            num_chats,
        )
    else:
        storage.save_context(group_id, file_context)
        background_tasks.add_task(_run_generate_group, group_id, topic, file_context, num_chats)

    return GroupCreateResponse(group_id=group_id, status=initial_status, num_chats=num_chats)


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
        website_url=group_data.get("website_url"),
        context_gathering_error=group_data.get("context_gathering_error"),
    )
