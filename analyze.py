"""Script 2: Analyze generated support chats for quality, intent, satisfaction, and mistakes."""

import json
import sys

from langchain_core.prompts import ChatPromptTemplate

from config import ANALYSIS_RESULTS_PATH, GENERATED_CHATS_PATH, OUTPUT_DIR, get_llm
from models import (
    AnalysisDataset,
    AnalysisValidationResult,
    ChatAnalysis,
    GeneratedDataset,
)
from prompts import ANALYZE_SYSTEM_TEMPLATE, ANALYZE_VALIDATE_TEMPLATE
from security import sanitize_text


def format_chat_messages(messages: list[dict]) -> str:
    """Format chat messages into a readable string for the prompt."""
    lines = []
    for i, msg in enumerate(messages):
        role = msg["role"].upper()
        text = sanitize_text(msg["text"])
        lines.append(f"[{i}] {role}: {text}")
    return "\n".join(lines)


def analyze_single_chat(chat: dict, llm) -> ChatAnalysis:
    """Analyze a single chat using a two-step LLM chain: analyze → validate/correct.

    Step 1: Initial analysis
    Step 2: Meta-validation that corrects any issues in the initial analysis
    """
    chat_id = chat["chat_id"]
    chat_messages = format_chat_messages(chat["messages"])

    # Step 1: Analyze
    analyze_prompt = ChatPromptTemplate.from_messages([
        ("system", ANALYZE_SYSTEM_TEMPLATE),
    ])

    analyze_chain = analyze_prompt | llm.with_structured_output(ChatAnalysis)

    analysis = analyze_chain.invoke({
        "chat_id": chat_id,
        "chat_messages": chat_messages,
    })

    # Force correct chat_id
    analysis.chat_id = chat_id

    # Step 2: Validate and correct
    validate_prompt = ChatPromptTemplate.from_messages([
        ("system", ANALYZE_VALIDATE_TEMPLATE),
    ])

    validate_chain = validate_prompt | llm.with_structured_output(AnalysisValidationResult)

    validation = validate_chain.invoke({
        "chat_id": chat_id,
        "chat_messages": chat_messages,
        "analysis_json": analysis.model_dump_json(indent=2),
    })

    corrected = validation.corrected_analysis
    corrected.chat_id = chat_id

    if not validation.is_correct:
        print(f"  Corrections applied: {validation.corrections}")

    return corrected


def main():
    print("=== Support Chat Analyzer ===\n")

    if not GENERATED_CHATS_PATH.exists():
        print(f"Error: {GENERATED_CHATS_PATH} not found.")
        print("Run generate.py first to create the chat dataset.")
        sys.exit(1)

    with open(GENERATED_CHATS_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    dataset = GeneratedDataset.model_validate(raw_data)
    print(f"Loaded {len(dataset.chats)} chats from {GENERATED_CHATS_PATH}\n")

    llm = get_llm()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    analyses = []
    for i, chat in enumerate(dataset.chats):
        chat_dict = chat.model_dump()
        chat_id = chat_dict["chat_id"]
        scenario = chat_dict["scenario"]

        print(f"[{i + 1}/{len(dataset.chats)}] Analyzing {chat_id}: "
              f"{scenario['domain']} / {scenario['case_type']}")

        analysis = analyze_single_chat(chat_dict, llm)
        analyses.append(analysis)

        print(f"  Intent: {analysis.intent}")
        print(f"  Satisfaction: {analysis.satisfaction.value}")
        print(f"  Quality: {analysis.quality_score}/10")
        print(f"  Mistakes: {len(analysis.agent_mistakes)}")
        print()

    analysis_dataset = AnalysisDataset(analyses=analyses)

    with open(ANALYSIS_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(analysis_dataset.model_dump(), f, indent=2, ensure_ascii=False)

    print(f"Done! Saved {len(analyses)} analyses to {ANALYSIS_RESULTS_PATH}")

    # Print summary
    satisfaction_counts = {}
    total_mistakes = 0
    for a in analyses:
        level = a.satisfaction.value
        satisfaction_counts[level] = satisfaction_counts.get(level, 0) + 1
        total_mistakes += len(a.agent_mistakes)

    avg_quality = sum(a.quality_score for a in analyses) / len(analyses) if analyses else 0
    print(f"\nSatisfaction distribution: {satisfaction_counts}")
    print(f"Average quality score: {avg_quality:.1f}/10")
    print(f"Total agent mistakes found: {total_mistakes}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
