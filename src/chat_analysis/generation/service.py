"""Generation pipeline: build scenario matrix, generate and validate chats.

Uses a 4-step architecture:
1. Structure context — extract structured product reference from raw context (once per source)
2. Generate brief — create a rich scenario brief from structured context + flags
3. Write conversation — write the conversation using structured context + brief
4. Validate conversation — validate against all inputs
"""

import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_core.prompts import ChatPromptTemplate

from chat_analysis.core.config import GENERATED_CHATS_PATH, MAX_RETRIES, OUTPUT_DIR, get_llm
from chat_analysis.core.security import load_context_safely
from chat_analysis.generation.models import (
    CaseType,
    ChatScenario,
    ChatValidationResult,
    GeneratedChat,
    GeneratedDataset,
    ScenarioBrief,
    StructuredContext,
)
from chat_analysis.generation.prompts import (
    GENERATE_BRIEF_SYSTEM_TEMPLATE,
    STRUCTURE_CONTEXT_SYSTEM_TEMPLATE,
    VALIDATE_CHAT_SYSTEM_TEMPLATE,
    WRITE_CHAT_SYSTEM_TEMPLATE,
)
from chat_analysis.models import ChatDomain, MessageRole

logger = logging.getLogger(__name__)


def build_scenario_matrix() -> list[ChatScenario]:
    """Build a deterministic matrix of 20 scenarios (5 domains × 4 case types).

    Uses modular arithmetic to assign flags (hidden dissatisfaction, tonal errors,
    logical errors) in a deterministic, evenly distributed pattern.
    """
    domains = list(ChatDomain)
    case_types = list(CaseType)
    scenarios = []

    for i, domain in enumerate(domains):
        for j, case_type in enumerate(case_types):
            idx = i * len(case_types) + j
            # Deterministic flag assignment using modular arithmetic
            # ~25% have hidden dissatisfaction, ~25% have tonal errors, ~25% have logical errors
            has_hidden_dissatisfaction = idx % 4 == 1
            has_tonal_errors = idx % 4 == 2
            has_logical_errors = idx % 4 == 3

            scenarios.append(
                ChatScenario(
                    domain=domain,
                    case_type=case_type,
                    has_hidden_dissatisfaction=has_hidden_dissatisfaction,
                    has_tonal_errors=has_tonal_errors,
                    has_logical_errors=has_logical_errors,
                )
            )

    return scenarios


def structure_product_context(raw_context: str, llm) -> StructuredContext:
    """Step 1: Extract structured product reference from raw context.

    This step runs once per context source (not per chat), extracting
    structured sections including the valid_entities vocabulary list.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", STRUCTURE_CONTEXT_SYSTEM_TEMPLATE),
        ("human", "Extract and organize the product information into structured sections."),
    ])
    chain = prompt | llm.with_structured_output(StructuredContext)

    logger.info("Structuring product context (%d chars)...", len(raw_context))
    t_start = time.perf_counter()

    result = chain.invoke({"raw_context": raw_context})

    elapsed = time.perf_counter() - t_start
    logger.info(
        "Context structured: product=%r, %d entities (%.1fs)",
        result.product_name, len(result.valid_entities), elapsed,
    )
    return result


def _generate_brief(
    structured_context: StructuredContext,
    scenario: ChatScenario,
    chat_id: str,
    domain_label: str,
    llm,
) -> ScenarioBrief:
    """Step 2: Generate a rich scenario brief from structured context + flags."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", GENERATE_BRIEF_SYSTEM_TEMPLATE),
        ("human", "Create a detailed scenario brief for this chat simulation."),
    ])
    chain = prompt | llm.with_structured_output(ScenarioBrief)

    result = chain.invoke({
        "structured_context": structured_context.to_prompt_text(),
        "domain": domain_label,
        "case_type": scenario.case_type.value,
        "chat_id": chat_id,
        "has_hidden_dissatisfaction": str(scenario.has_hidden_dissatisfaction),
        "has_tonal_errors": str(scenario.has_tonal_errors),
        "has_logical_errors": str(scenario.has_logical_errors),
    })

    logger.debug(
        "[%s] Brief: persona=%s, outcome=%s, errors=%d",
        chat_id, result.customer_persona, result.target_outcome,
        len(result.agent_error_plan),
    )
    return result


def _write_conversation(
    structured_context: StructuredContext,
    brief: ScenarioBrief,
    scenario: ChatScenario,
    chat_id: str,
    domain_label: str,
    llm,
) -> GeneratedChat:
    """Step 3: Write the conversation using structured context + brief."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", WRITE_CHAT_SYSTEM_TEMPLATE),
        ("human", "Write the support chat conversation following the brief exactly."),
    ])
    chain = prompt | llm.with_structured_output(GeneratedChat)

    result = chain.invoke({
        "structured_context": structured_context.to_prompt_text(),
        "brief": brief.to_prompt_text(),
        "domain": domain_label,
        "case_type": scenario.case_type.value,
        "chat_id": chat_id,
    })

    # Force correct chat_id
    result.chat_id = chat_id
    return result


def _validate_conversation(
    structured_context: StructuredContext,
    brief: ScenarioBrief,
    chat: GeneratedChat,
    scenario: ChatScenario,
    domain_label: str,
    llm,
) -> ChatValidationResult | None:
    """Step 4: Validate the conversation against all inputs."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", VALIDATE_CHAT_SYSTEM_TEMPLATE),
        ("human", "Validate the chat and return your assessment."),
    ])
    chain = prompt | llm.with_structured_output(ChatValidationResult)

    return chain.invoke({
        "structured_context": structured_context.to_prompt_text(),
        "brief": brief.to_prompt_text(),
        "domain": domain_label,
        "case_type": scenario.case_type.value,
        "has_hidden_dissatisfaction": str(scenario.has_hidden_dissatisfaction),
        "has_tonal_errors": str(scenario.has_tonal_errors),
        "has_logical_errors": str(scenario.has_logical_errors),
        "chat_json": chat.model_dump_json(indent=2),
    })


def generate_single_chat(
    scenario: ChatScenario,
    chat_id: str,
    llm,
    structured_context: StructuredContext | None = None,
    context_override: str | None = None,
    topic_override: str | None = None,
) -> GeneratedChat:
    """Generate a single chat using the 4-step pipeline.

    Steps: structure context → generate brief → write conversation → validate.
    Uses a two-tier retry: inner loop retries steps 3+4, outer loop regenerates
    the brief once if all inner retries fail.

    Args:
        structured_context: Pre-structured context (preferred, avoids redundant LLM call).
        context_override: Raw context string, structured on-the-fly if structured_context
            is not provided.
        topic_override: If provided, used as the domain label in prompts instead of
            scenario.domain.value.
    """
    domain_label = topic_override if topic_override is not None else scenario.domain.value

    # Step 1: Ensure we have structured context
    if structured_context is None:
        raw_context = (
            context_override
            if context_override is not None
            else load_context_safely(scenario.domain.value)
        )
        if raw_context:
            structured_context = structure_product_context(raw_context, llm)
        else:
            # Minimal fallback when no context is available
            structured_context = StructuredContext(
                product_name=domain_label,
                business_summary="General support service",
                plans_and_pricing="Not specified in documentation",
                billing_and_payments="Not specified in documentation",
                refund_policy="Not specified in documentation",
                account_and_security="Not specified in documentation",
                technical_platform="Not specified in documentation",
                known_issues_and_edge_cases="Not specified in documentation",
                escalation_rules="Not specified in documentation",
                tone_guidelines="Professional and empathetic",
                valid_entities=[domain_label],
            )

    flags = [
        f for f, v in [
            ("hidden_dissatisfaction", scenario.has_hidden_dissatisfaction),
            ("tonal_errors", scenario.has_tonal_errors),
            ("logical_errors", scenario.has_logical_errors),
        ] if v
    ]
    flag_str = f" [{', '.join(flags)}]" if flags else ""
    logger.info("[%s] Generating %s/%s%s", chat_id, domain_label, scenario.case_type.value, flag_str)

    t_start = time.perf_counter()
    chat = None
    max_brief_attempts = 2  # Outer loop: regenerate brief once if all inner retries fail

    for brief_attempt in range(max_brief_attempts):
        # Step 2: Generate brief
        brief = _generate_brief(structured_context, scenario, chat_id, domain_label, llm)

        if brief_attempt > 0:
            logger.info("[%s] Regenerated brief (attempt %d)", chat_id, brief_attempt + 1)

        # Inner loop: retry steps 3+4 up to MAX_RETRIES
        for attempt in range(MAX_RETRIES):
            logger.debug("[%s] Write attempt %d/%d (brief %d)", chat_id, attempt + 1, MAX_RETRIES, brief_attempt + 1)

            # Step 3: Write conversation
            chat = _write_conversation(
                structured_context, brief, scenario, chat_id, domain_label, llm,
            )

            # Lightweight structural pre-check
            issues = _validate_structure(chat)
            if issues:
                logger.warning("[%s] Structural issues (attempt %d): %s", chat_id, attempt + 1, issues)
                continue

            # Step 4: LLM-based validation
            validation = _validate_conversation(
                structured_context, brief, chat, scenario, domain_label, llm,
            )

            if validation is None:
                logger.warning(
                    "[%s] Validation returned None (attempt %d), accepting (structural check passed)",
                    chat_id, attempt + 1,
                )
                elapsed = time.perf_counter() - t_start
                logger.info(
                    "[%s] Done — %d messages in %.1fs",
                    chat_id, len(chat.messages), elapsed,
                )
                return chat

            if validation.is_valid:
                elapsed = time.perf_counter() - t_start
                logger.info(
                    "[%s] Done — %d messages in %.1fs",
                    chat_id, len(chat.messages), elapsed,
                )
                return chat
            else:
                logger.warning(
                    "[%s] Validation failed (attempt %d): %s",
                    chat_id, attempt + 1, validation.issues,
                )

        # All inner retries failed — outer loop will regenerate brief (if attempts remain)
        if brief_attempt < max_brief_attempts - 1:
            logger.warning("[%s] All %d write attempts failed, regenerating brief...", chat_id, MAX_RETRIES)

    elapsed = time.perf_counter() - t_start
    logger.warning(
        "[%s] Using last attempt after retries (%.1fs)", chat_id, elapsed,
    )
    return chat  # type: ignore[return-value]


def _validate_structure(chat: GeneratedChat) -> list[str]:
    """Fast structural check without an LLM call."""
    issues = []
    msgs = chat.messages
    if not msgs:
        return ["No messages generated"]
    if msgs[0].role != MessageRole.CUSTOMER:
        issues.append("First message must be from customer")
    for i in range(1, len(msgs)):
        if msgs[i].role == msgs[i - 1].role:
            issues.append(f"Messages {i} and {i+1} have the same role (not alternating)")
            break
    if len(msgs) < 4:
        issues.append(f"Too few messages: {len(msgs)} (minimum 4)")
    return issues


def main() -> None:
    from chat_analysis.core.logging import setup_logging
    setup_logging()

    logger.info("=== Support Chat Generator (4-step pipeline) ===")

    llm = get_llm()
    scenarios = build_scenario_matrix()
    logger.info("Built %d scenarios", len(scenarios))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Structure context once per domain (5 LLM calls)
    logger.info("Structuring context for %d domains...", len(ChatDomain))
    structured_contexts: dict[str, StructuredContext] = {}
    for domain in ChatDomain:
        raw_context = load_context_safely(domain.value)
        if raw_context:
            structured_contexts[domain.value] = structure_product_context(raw_context, llm)
        else:
            logger.warning("No context found for domain %s", domain.value)

    workers = min(5, len(scenarios))  # max 5 concurrent requests
    futures: dict = {}
    chats_by_index: dict[int, GeneratedChat] = {}

    t_total = time.perf_counter()
    logger.info("Submitting %d chats to thread pool (workers=%d)", len(scenarios), workers)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for i, scenario in enumerate(scenarios):
            chat_id = f"chat_{i + 1:03d}"
            ctx = structured_contexts.get(scenario.domain.value)
            future = executor.submit(
                generate_single_chat, scenario, chat_id, llm,
                structured_context=ctx,
            )
            futures[future] = (i, chat_id)

        for future in as_completed(futures):
            i, chat_id = futures[future]
            try:
                chat = future.result()
                chats_by_index[i] = chat
            except Exception as exc:
                logger.error("[%s] Generation failed: %s", chat_id, exc, exc_info=True)
                raise

    chats = [chats_by_index[i] for i in range(len(scenarios))]

    dataset = GeneratedDataset(chats=chats)

    with open(GENERATED_CHATS_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset.model_dump(), f, indent=2, ensure_ascii=False)

    elapsed = time.perf_counter() - t_total
    logger.info("Saved %d chats to %s (total %.1fs)", len(chats), GENERATED_CHATS_PATH, elapsed)

    flags_summary = {
        "hidden_dissatisfaction": sum(1 for s in scenarios if s.has_hidden_dissatisfaction),
        "tonal_errors": sum(1 for s in scenarios if s.has_tonal_errors),
        "logical_errors": sum(1 for s in scenarios if s.has_logical_errors),
        "clean": sum(
            1 for s in scenarios
            if not s.has_hidden_dissatisfaction
            and not s.has_tonal_errors
            and not s.has_logical_errors
        ),
    }
    logger.info("Scenario distribution: %s", flags_summary)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
