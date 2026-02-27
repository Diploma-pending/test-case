"""Analysis pipeline: analyze generated chats for quality, intent, and mistakes."""

import json
import logging
import sys
import time

from langchain_core.prompts import ChatPromptTemplate

from chat_analysis.analysis.models import AnalysisDataset, AnalysisValidationResult, ChatAnalysis
from chat_analysis.analysis.prompts import ANALYZE_SYSTEM_TEMPLATE, ANALYZE_VALIDATE_TEMPLATE
from chat_analysis.core.config import ANALYSIS_RESULTS_PATH, GENERATED_CHATS_PATH, OUTPUT_DIR, get_llm
from chat_analysis.core.security import sanitize_text
from chat_analysis.generation.models import GeneratedDataset

logger = logging.getLogger(__name__)


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
    domain = chat.get("scenario", {}).get("domain", "unknown")
    case_type = chat.get("scenario", {}).get("case_type", "unknown")

    logger.info("[%s] Analyzing (%s/%s)", chat_id, domain, case_type)
    t_start = time.perf_counter()

    # Step 1: Analyze
    analyze_prompt = ChatPromptTemplate.from_messages([
        ("system", ANALYZE_SYSTEM_TEMPLATE),
        ("human", "Analyze the chat above and return the analysis result."),
    ])

    analyze_chain = analyze_prompt | llm.with_structured_output(ChatAnalysis)

    analysis = analyze_chain.invoke({
        "chat_id": chat_id,
        "chat_messages": chat_messages,
        "domain": domain,
        "case_type": case_type,
    })

    # Force correct chat_id
    analysis.chat_id = chat_id

    logger.debug(
        "[%s] Initial analysis — intent=%s satisfaction=%s quality=%d mistakes=%d",
        chat_id, analysis.intent, analysis.satisfaction.value,
        analysis.quality_score, len(analysis.agent_mistakes),
    )

    # Step 2: Validate and correct
    validate_prompt = ChatPromptTemplate.from_messages([
        ("system", ANALYZE_VALIDATE_TEMPLATE),
        ("human", "Validate and correct the analysis above if needed."),
    ])

    validate_chain = validate_prompt | llm.with_structured_output(AnalysisValidationResult)

    validation = validate_chain.invoke({
        "chat_id": chat_id,
        "chat_messages": chat_messages,
        "analysis_json": analysis.model_dump_json(indent=2),
        "domain": domain,
        "case_type": case_type,
    })

    corrected = validation.corrected_analysis
    corrected.chat_id = chat_id

    elapsed = time.perf_counter() - t_start

    if not validation.is_correct:
        logger.info("[%s] Corrections applied: %s", chat_id, validation.corrections)

    logger.info(
        "[%s] Done — intent=%s satisfaction=%s quality=%d/10 mistakes=%d (%.1fs)",
        chat_id, corrected.intent, corrected.satisfaction.value,
        corrected.quality_score, len(corrected.agent_mistakes), elapsed,
    )

    return corrected


def main() -> None:
    from chat_analysis.core.logging import setup_logging
    setup_logging()

    logger.info("=== Support Chat Analyzer ===")

    if not GENERATED_CHATS_PATH.exists():
        logger.error("%s not found — run generate.py first", GENERATED_CHATS_PATH)
        sys.exit(1)

    with open(GENERATED_CHATS_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    dataset = GeneratedDataset.model_validate(raw_data)
    logger.info("Loaded %d chats from %s", len(dataset.chats), GENERATED_CHATS_PATH)

    llm = get_llm()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    analyses = []
    for i, chat in enumerate(dataset.chats):
        chat_dict = chat.model_dump()
        analysis = analyze_single_chat(chat_dict, llm)
        analyses.append(analysis)

    analysis_dataset = AnalysisDataset(analyses=analyses)

    with open(ANALYSIS_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(analysis_dataset.model_dump(), f, indent=2, ensure_ascii=False)

    logger.info("Saved %d analyses to %s", len(analyses), ANALYSIS_RESULTS_PATH)

    satisfaction_counts: dict[str, int] = {}
    total_mistakes = 0
    for a in analyses:
        level = a.satisfaction.value
        satisfaction_counts[level] = satisfaction_counts.get(level, 0) + 1
        total_mistakes += len(a.agent_mistakes)

    avg_quality = sum(a.quality_score for a in analyses) / len(analyses) if analyses else 0
    logger.info("Satisfaction distribution: %s", satisfaction_counts)
    logger.info("Average quality score: %.1f/10", avg_quality)
    logger.info("Total agent mistakes found: %d", total_mistakes)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
