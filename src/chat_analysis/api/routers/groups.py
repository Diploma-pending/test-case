"""Group endpoints: create, trigger analysis, list chats."""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Union
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

logger = logging.getLogger(__name__)

from chat_analysis.analysis.service import analyze_single_chat
from chat_analysis.api import storage
from chat_analysis.api.models import (
    BusinessContext,
    BusinessContextItem,
    ChatSummary,
    GroupAnalyzeResponse,
    GroupChatsResponse,
    GroupCreateResponse,
    GroupSummary,
)
from chat_analysis.context_gathering.service import (
    ContextGatheringError,
    gather_context,
    resolve_context,
)
from chat_analysis.core.config import get_llm
from chat_analysis.core.security import load_domain_context, sanitize_text
from chat_analysis.generation.models import CaseType, ChatScenario
from chat_analysis.generation.service import generate_single_chat, structure_product_context
from chat_analysis.models import ChatDomain

router = APIRouter(prefix="/groups", tags=["groups"])

MAX_CONTEXT_SIZE = 1 * 1024 * 1024  # 1 MB


def build_group_scenarios(num_chats: int) -> list[ChatScenario]:
    """Build a list of scenarios for a custom group by cycling through domains and case types.

    Uses the same modular arithmetic for flags as build_scenario_matrix().
    """
    domains = list(ChatDomain)
    case_types = list(CaseType)
    scenarios = []
    for i in range(num_chats):
        scenarios.append(
            ChatScenario(
                domain=domains[i % len(domains)],
                case_type=case_types[i % len(case_types)],
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

    logger.info("[group=%s] Starting generation: topic=%r num_chats=%d", group_id, topic, num_chats)
    t_total = time.perf_counter()

    # Step 1: Structure context once for the entire group
    structured_ctx = None
    if context_str and context_str.strip():
        logger.info("[group=%s] Structuring product context...", group_id)
        structured_ctx = structure_product_context(context_str, llm)

    # Pre-create all chat records so the FE can see them immediately
    for i, scenario in enumerate(scenarios):
        chat_id = f"chat_{i + 1:03d}"
        storage.save_chat(group_id, chat_id, {
            "chat_id": chat_id,
            "status": "pending",
            "messages": None,
            "analysis": None,
        })

    succeeded = 0
    failed = 0
    try:
        for i, scenario in enumerate(scenarios):
            chat_id = f"chat_{i + 1:03d}"
            storage.update_chat_status(group_id, chat_id, "generating")
            try:
                chat = generate_single_chat(
                    scenario,
                    chat_id,
                    llm,
                    structured_context=structured_ctx,
                    context_override=context_str,
                    topic_override=topic,
                )
                storage.save_chat(group_id, chat_id, {
                    "chat_id": chat_id,
                    "status": "generated",
                    "messages": [m.model_dump() for m in chat.messages],
                    "analysis": None,
                })
                succeeded += 1
            except Exception as exc:
                logger.error("[group=%s] [%s] Generation failed: %s", group_id, chat_id, exc, exc_info=True)
                storage.update_chat_status(group_id, chat_id, "failed")
                failed += 1

        elapsed = time.perf_counter() - t_total
        logger.info(
            "[group=%s] Generation complete — succeeded=%d failed=%d (%.1fs)",
            group_id, succeeded, failed, elapsed,
        )
        group_data = storage.load_group(group_id)
        group_data["status"] = "generated"
        storage.save_group(group_id, group_data)

    except Exception:
        group_data = storage.load_group(group_id)
        group_data["status"] = "generation_failed"
        storage.save_group(group_id, group_data)
        raise


def _resolve_and_generate_sync(
    group_id: str,
    topic: str,
    num_chats: int,
) -> None:
    """Resolve context from domain file or LLM knowledge, then generate chats."""
    llm = get_llm()

    logger.info("[group=%s] Resolving context for topic=%r", group_id, topic)
    try:
        context_str, context_source = resolve_context(topic, llm)
        logger.info(
            "[group=%s] Context resolved via %s (%d chars)",
            group_id, context_source, len(context_str),
        )
    except Exception as exc:
        logger.error("[group=%s] Context resolution failed: %s", group_id, exc)
        group_data = storage.load_group(group_id)
        group_data["status"] = "context_gathering_failed"
        group_data["context_gathering_error"] = str(exc)
        storage.save_group(group_id, group_data)
        return

    storage.save_context(group_id, context_str)

    group_data = storage.load_group(group_id)
    group_data["status"] = "generating"
    group_data["context_source"] = context_source
    storage.save_group(group_id, group_data)

    _generate_group_sync(group_id, topic, context_str, num_chats)


def _gather_and_generate_sync(
    group_id: str,
    topic: str,
    file_context: str,
    website_url: str,
    num_chats: int,
) -> None:
    """Gather context from website, merge with file context, then generate chats."""
    llm = get_llm()

    logger.info("[group=%s] Gathering context from %s", group_id, website_url)
    try:
        gathered = gather_context(website_url, llm)
        website_context = gathered.context_document
        logger.info(
            "[group=%s] Context gathered from %s (%d chars)",
            group_id, website_url, gathered.char_count,
        )
    except ContextGatheringError as exc:
        logger.error("[group=%s] Context gathering failed: %s", group_id, exc)
        group_data = storage.load_group(group_id)
        group_data["status"] = "context_gathering_failed"
        group_data["context_gathering_error"] = str(exc)
        storage.save_group(group_id, group_data)
        return

    merged = _combine_contexts(file_context, website_context, website_url)
    logger.info("[group=%s] Merged context: %d chars total", group_id, len(merged))
    storage.save_context(group_id, merged)

    group_data = storage.load_group(group_id)
    group_data["status"] = "generating"
    storage.save_group(group_id, group_data)

    _generate_group_sync(group_id, topic, merged, num_chats)


def _analyze_group_sync(group_id: str) -> None:
    """Synchronous analysis task — run via asyncio.to_thread."""
    llm = get_llm()
    chats = storage.load_all_chats(group_id)

    logger.info("[group=%s] Starting analysis of %d chats", group_id, len(chats))
    t_total = time.perf_counter()
    succeeded = 0
    failed = 0

    try:
        for chat_data in chats:
            chat_id = chat_data["chat_id"]

            if not chat_data.get("messages"):
                logger.warning("[group=%s] [%s] Skipping — no messages", group_id, chat_id)
                storage.update_chat_status(group_id, chat_id, "failed")
                failed += 1
                continue

            storage.update_chat_status(group_id, chat_id, "analyzing")
            try:
                analysis = analyze_single_chat(chat_data, llm)
                chat_data["status"] = "analyzed"
                chat_data["analysis"] = analysis.model_dump()
                storage.save_chat(group_id, chat_id, chat_data)
                succeeded += 1
            except Exception as exc:
                logger.error("[group=%s] [%s] Analysis failed: %s", group_id, chat_id, exc, exc_info=True)
                storage.update_chat_status(group_id, chat_id, "failed")
                failed += 1

        elapsed = time.perf_counter() - t_total
        logger.info(
            "[group=%s] Analysis complete — succeeded=%d failed=%d (%.1fs)",
            group_id, succeeded, failed, elapsed,
        )
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


async def _run_resolve_and_generate_group(
    group_id: str,
    topic: str,
    num_chats: int,
) -> None:
    await asyncio.to_thread(_resolve_and_generate_sync, group_id, topic, num_chats)


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


def _business_context_label(value: str) -> str:
    """Human-readable label for a business context value (e.g. maxbeauty -> MaxBeauty)."""
    return value.replace("_", " ").title()


@router.get("/businesses", response_model=list[BusinessContextItem])
async def list_businesses() -> list[BusinessContextItem]:
    """Return available preset business contexts from data/domains/ for UI dropdown (excludes CUSTOM)."""
    return [
        BusinessContextItem(id=bc.value, label=_business_context_label(bc.value))
        for bc in BusinessContext
        if bc != BusinessContext.CUSTOM
    ]


@router.get("", response_model=list[GroupSummary])
async def list_groups() -> list[GroupSummary]:
    """Return all groups sorted by creation time (newest first)."""
    return [GroupSummary(**g) for g in storage.list_groups()]


@router.post("", status_code=202, response_model=GroupCreateResponse)
async def create_group(
    background_tasks: BackgroundTasks,
    business: Optional[BusinessContext] = Form(
        None,
        description="Preset Scalara business context from data/domains/, or CUSTOM for your own context (file/URL).",
    ),
    context_file: Union[UploadFile, str, None] = File(None),
    website_url: Optional[str] = Form(None),
    num_chats: int = Form(default=8),
) -> GroupCreateResponse:
    """Create a new chat group and generate chats in the background.

    Set business to a preset (e.g. brighterly, dressly) to use that context from data/domains/.
    Set business to CUSTOM or omit to use your own context: context_file (.md) or website_url.
    """
    # Swagger UI sends an empty string when no file is selected; treat it as None
    if isinstance(context_file, str):
        context_file = None

    # Derive a display name from available inputs
    if business is not None and business != BusinessContext.CUSTOM:
        topic = _business_context_label(business.value)
    elif website_url is not None:
        topic = urlparse(website_url).hostname or "Custom Group"
    elif isinstance(context_file, UploadFile) and context_file.filename:
        topic = context_file.filename.removesuffix(".md")
    else:
        topic = "Custom Group"

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

    # Preset business: load context from data/domains/<value>.md only
    use_preset = business is not None and business != BusinessContext.CUSTOM
    if use_preset:
        context_str = load_domain_context(business.value)
        if context_str is None:
            raise HTTPException(
                status_code=422,
                detail=f'Context file for business "{business.value}" not found.',
            )
        initial_status = "generating"
        group_data = {
            "group_id": group_id,
            "topic": topic,
            "status": initial_status,
            "num_chats": num_chats,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "website_url": None,
            "context_gathering_error": None,
            "context_source": "domain_file",
            "business": business.value,
        }
        storage.save_group(group_id, group_data)
        storage.save_context(group_id, context_str)
        background_tasks.add_task(_run_generate_group, group_id, topic, context_str, num_chats)
        return GroupCreateResponse(group_id=group_id, status=initial_status, num_chats=num_chats)

    # CUSTOM or None: existing behaviour (file, URL, or resolve from topic)
    has_file = context_file is not None
    has_url = website_url is not None
    if has_url:
        initial_status = "gathering_context"
    elif not has_file:
        initial_status = "gathering_context"  # will resolve from domain file or LLM
    else:
        initial_status = "generating"

    logger.info(
        "[group=%s] Created — topic=%r num_chats=%d website_url=%s has_file=%s",
        group_id, topic, num_chats, website_url, has_file,
    )

    group_data = {
        "group_id": group_id,
        "topic": topic,
        "status": initial_status,
        "num_chats": num_chats,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "website_url": website_url,
        "context_gathering_error": None,
        "context_source": None,
        "business": BusinessContext.CUSTOM.value if business == BusinessContext.CUSTOM else None,
    }
    storage.save_group(group_id, group_data)

    if has_url:
        background_tasks.add_task(
            _run_gather_and_generate_group,
            group_id,
            topic,
            file_context,
            website_url,
            num_chats,
        )
    elif has_file:
        storage.save_context(group_id, file_context)
        background_tasks.add_task(_run_generate_group, group_id, topic, file_context, num_chats)
    else:
        background_tasks.add_task(
            _run_resolve_and_generate_group,
            group_id,
            topic,
            num_chats,
        )

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
        business=group_data.get("business"),
    )
