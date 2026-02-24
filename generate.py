"""Script 1: Generate synthetic support chat dataset using LLM."""

import json
import sys

from langchain_core.prompts import ChatPromptTemplate

from config import GENERATED_CHATS_PATH, MAX_RETRIES, OUTPUT_DIR, get_llm
from models import (
    CaseType,
    ChatDomain,
    ChatScenario,
    ChatValidationResult,
    GeneratedChat,
    GeneratedDataset,
)
from prompts import GENERATE_SYSTEM_TEMPLATE, VALIDATE_SYSTEM_TEMPLATE, build_special_requirements
from security import load_context_safely


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
) -> GeneratedChat:
    """Generate a single chat using a two-step LLM chain: generate → validate.

    Retries up to MAX_RETRIES times if validation fails.
    """
    domain_context = load_context_safely(scenario.domain.value)
    special_requirements = build_special_requirements(scenario)

    # Step 1: Generate
    generate_prompt = ChatPromptTemplate.from_messages([
        ("system", GENERATE_SYSTEM_TEMPLATE),
        ("human", "Generate the support chat conversation for this scenario."),
    ])

    generate_chain = generate_prompt | llm.with_structured_output(GeneratedChat)

    generate_params = {
        "domain": scenario.domain.value,
        "case_type": scenario.case_type.value,
        "chat_id": chat_id,
        "domain_context": domain_context if domain_context else "No additional context available.",
        "special_requirements": special_requirements,
    }

    # Step 2: Validate prompt
    validate_prompt = ChatPromptTemplate.from_messages([
        ("system", VALIDATE_SYSTEM_TEMPLATE),
        ("human", "Validate the chat above and return the validation result."),
    ])

    validate_chain = validate_prompt | llm.with_structured_output(ChatValidationResult)

    for attempt in range(MAX_RETRIES):
        print(f"  Attempt {attempt + 1}/{MAX_RETRIES}...")

        chat = generate_chain.invoke(generate_params)

        # Force correct metadata
        chat.chat_id = chat_id
        chat.scenario = scenario

        # Validate
        chat_json = chat.model_dump_json(indent=2)
        validation = validate_chain.invoke({
            "domain": scenario.domain.value,
            "case_type": scenario.case_type.value,
            "has_hidden_dissatisfaction": str(scenario.has_hidden_dissatisfaction),
            "has_tonal_errors": str(scenario.has_tonal_errors),
            "has_logical_errors": str(scenario.has_logical_errors),
            "special_requirements": special_requirements,
            "chat_json": chat_json,
        })

        if validation.is_valid:
            print(f"  Validated OK.")
            return chat
        else:
            print(f"  Validation failed: {validation.issues}")
            if validation.suggestions:
                print(f"  Suggestions: {validation.suggestions}")

    # Return last attempt even if not fully validated
    print(f"  WARNING: Using last attempt after {MAX_RETRIES} retries.")
    return chat


def main():
    print("=== Support Chat Generator ===\n")

    llm = get_llm()
    scenarios = build_scenario_matrix()
    print(f"Generated {len(scenarios)} scenarios.\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    chats = []
    for i, scenario in enumerate(scenarios):
        chat_id = f"chat_{i + 1:03d}"
        print(f"[{i + 1}/{len(scenarios)}] Generating {chat_id}: "
              f"{scenario.domain.value} / {scenario.case_type.value}"
              f"{' [hidden_dissatisfaction]' if scenario.has_hidden_dissatisfaction else ''}"
              f"{' [tonal_errors]' if scenario.has_tonal_errors else ''}"
              f"{' [logical_errors]' if scenario.has_logical_errors else ''}")

        chat = generate_single_chat(scenario, chat_id, llm)
        chats.append(chat)
        print()

    dataset = GeneratedDataset(chats=chats)

    with open(GENERATED_CHATS_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset.model_dump(), f, indent=2, ensure_ascii=False)

    print(f"Done! Saved {len(chats)} chats to {GENERATED_CHATS_PATH}")

    # Print summary
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
    print(f"\nScenario distribution: {flags_summary}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
