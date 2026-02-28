"""Analysis pipeline: analyze generated chats for quality, intent, and mistakes."""

import json
import logging
import re
import sys
import time
from typing import TypeVar

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from chat_analysis.analysis.models import AnalysisDataset, AnalysisValidationResult, ChatAnalysis
from chat_analysis.analysis.prompts import ANALYZE_SYSTEM_TEMPLATE, ANALYZE_VALIDATE_TEMPLATE
from chat_analysis.core.config import (
    ANALYSIS_RESULTS_PATH,
    GENERATED_CHATS_PATH,
    OUTPUT_DIR,
    get_llm,
)
from chat_analysis.core.security import sanitize_text
from chat_analysis.generation.models import GeneratedDataset

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _extract_llm(chain) -> object:
    """Walk an LCEL chain to find the underlying LLM instance."""
    for step in chain.steps if hasattr(chain, "steps") else [chain]:
        # RunnableBinding wraps the LLM — e.g. llm.bind_tools(...)
        if hasattr(step, "bound"):
            return step.bound
        # Direct LLM (ChatOpenAI, ChatAnthropic, etc.)
        if hasattr(step, "invoke") and hasattr(step, "model_name"):
            return step
    raise RuntimeError("Could not find LLM in chain")


def _invoke_structured(chain, variables: dict, model_class: type[T], chat_id: str) -> T | None:
    """Invoke a chain with structured output, falling back to raw JSON parsing on failure."""
    result = chain.invoke(variables)
    if result is not None:
        return result

    # Structured output failed — try invoking the LLM directly and parsing raw response
    logger.warning("[%s] Structured output returned None, trying raw JSON fallback", chat_id)
    prompt = chain.first  # the prompt template
    llm = _extract_llm(chain)
    messages = prompt.invoke(variables)
    raw_response = llm.invoke(messages)
    content = raw_response.content if hasattr(raw_response, "content") else str(raw_response)

    # Extract JSON from the response (may be wrapped in markdown code blocks)
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
    json_str = json_match.group(1).strip() if json_match else content.strip()

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        logger.error("[%s] Raw JSON fallback: invalid JSON: %s. Content: %s", chat_id, exc, content[:500])
        return None

    # Inject chat_id if missing (raw LLM won't include it) and strip extra fields
    if isinstance(data, dict):
        data.setdefault("chat_id", chat_id)

    try:
        return model_class.model_validate(data)
    except Exception as exc:
        logger.error("[%s] Raw JSON fallback: validation failed: %s", chat_id, exc)
        return None


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

    logger.info("[%s] Analyzing", chat_id)
    t_start = time.perf_counter()

    # Step 1: Analyze
    analyze_prompt = ChatPromptTemplate.from_messages([
        ("system", ANALYZE_SYSTEM_TEMPLATE),
        ("human", "Analyze the chat above and return the analysis result."),
    ])

    analyze_chain = analyze_prompt | llm.with_structured_output(ChatAnalysis)

    invoke_vars = {"chat_id": chat_id, "chat_messages": chat_messages}
    analysis = _invoke_structured(analyze_chain, invoke_vars, ChatAnalysis, chat_id)

    if analysis is None:
        raise RuntimeError(f"[{chat_id}] Analysis failed — LLM could not produce structured output")

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

    validate_vars = {
        "chat_id": chat_id,
        "chat_messages": chat_messages,
        "analysis_json": analysis.model_dump_json(indent=2),
    }
    validation = _invoke_structured(validate_chain, validate_vars, AnalysisValidationResult, chat_id)

    if validation is None:
        logger.warning("[%s] Validation returned None, using initial analysis", chat_id)
        elapsed = time.perf_counter() - t_start
        logger.info(
            "[%s] Done — intent=%s satisfaction=%s quality=%d/10 mistakes=%d (%.1fs)",
            chat_id, analysis.intent, analysis.satisfaction.value,
            analysis.quality_score, len(analysis.agent_mistakes), elapsed,
        )
        return analysis

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
