"""Generation pipeline: build scenario matrix, generate and validate chats."""

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
)
from chat_analysis.generation.prompts import (
    GENERATE_SYSTEM_TEMPLATE,
    VALIDATE_SYSTEM_TEMPLATE,
    build_special_requirements,
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


def generate_single_chat(
    scenario: ChatScenario,
    chat_id: str,
    llm,
    context_override: str | None = None,
    topic_override: str | None = None,
) -> GeneratedChat:
    """Generate a single chat using a two-step LLM chain: generate → validate.

    Retries up to MAX_RETRIES times if validation fails.

    Args:
        context_override: If provided, used instead of loading context from disk.
        topic_override: If provided, used as the domain label in prompts instead of
            scenario.domain.value.
    """
    domain_context = context_override if context_override is not None else load_context_safely(scenario.domain.value)
    special_requirements = build_special_requirements(scenario)
    domain_label = topic_override if topic_override is not None else scenario.domain.value

    # Step 1: Generate
    generate_prompt = ChatPromptTemplate.from_messages([
        ("system", GENERATE_SYSTEM_TEMPLATE),
        ("human", "Generate the support chat conversation for this scenario."),
    ])

    generate_chain = generate_prompt | llm.with_structured_output(GeneratedChat)

    generate_params = {
        "domain": domain_label,
        "case_type": scenario.case_type.value,
        "chat_id": chat_id,
        "domain_context": domain_context if domain_context else "No additional context available.",
        "special_requirements": special_requirements,
    }

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

    # Step 2: Validate (LLM-based quality check)
    validate_prompt = ChatPromptTemplate.from_messages([
        ("system", VALIDATE_SYSTEM_TEMPLATE),
        ("human", "Validate the chat above and return your assessment."),
    ])
    validate_chain = validate_prompt | llm.with_structured_output(ChatValidationResult)

    for attempt in range(MAX_RETRIES):
        logger.debug("[%s] Attempt %d/%d", chat_id, attempt + 1, MAX_RETRIES)

        chat = generate_chain.invoke(generate_params)

        # Force correct metadata
        chat.chat_id = chat_id
        chat.scenario = scenario

        # Lightweight structural validation (no extra LLM call)
        issues = _validate_structure(chat)
        if issues:
            logger.warning("[%s] Structural issues (attempt %d): %s", chat_id, attempt + 1, issues)
            continue

        # LLM-based validation for topic adherence, case type, and flags
        validation = validate_chain.invoke({
            "domain": domain_label,
            "case_type": scenario.case_type.value,
            "has_hidden_dissatisfaction": str(scenario.has_hidden_dissatisfaction),
            "has_tonal_errors": str(scenario.has_tonal_errors),
            "has_logical_errors": str(scenario.has_logical_errors),
            "special_requirements": special_requirements,
            "chat_json": chat.model_dump_json(indent=2),
        })

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

    elapsed = time.perf_counter() - t_start
    logger.warning(
        "[%s] Using last attempt after %d retries (%.1fs)", chat_id, MAX_RETRIES, elapsed
    )
    return chat


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

    logger.info("=== Support Chat Generator ===")

    llm = get_llm()
    scenarios = build_scenario_matrix()
    logger.info("Built %d scenarios", len(scenarios))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    workers = min(5, len(scenarios))  # max 5 concurrent Gemini requests
    futures: dict = {}
    chats_by_index: dict[int, GeneratedChat] = {}

    t_total = time.perf_counter()
    logger.info("Submitting %d chats to thread pool (workers=%d)", len(scenarios), workers)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for i, scenario in enumerate(scenarios):
            chat_id = f"chat_{i + 1:03d}"
            future = executor.submit(generate_single_chat, scenario, chat_id, llm)
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
