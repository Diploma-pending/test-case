"""Configuration: LLM factory, paths, generation parameters, env loading."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Paths ---

# Project root is 3 levels up from src/chat_analysis/core/
BASE_DIR = Path(__file__).parents[3]
_PACKAGE_DIR = Path(__file__).parents[1]
CONTEXT_DIR = _PACKAGE_DIR / "data" / "context"
DOMAINS_DIR = _PACKAGE_DIR / "data" / "domains"
OUTPUT_DIR = BASE_DIR / "output"

GENERATED_CHATS_PATH = OUTPUT_DIR / "generated_chats.json"
ANALYSIS_RESULTS_PATH = OUTPUT_DIR / "analysis_results.json"
GROUPS_DIR = OUTPUT_DIR / "groups"

# --- Generation parameters ---

NUM_CHATS_PER_DOMAIN = 4  # 4 case types × 5 domains = 20 chats
MAX_RETRIES = 3  # Max retries if validation fails

# --- LLM configuration ---

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # "openai", "anthropic", or "google"
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = 0


def get_llm():
    """Create and return an LLM instance based on environment configuration."""
    if LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            model_kwargs={"seed": 42},
        )
    elif LLM_PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
        )
    elif LLM_PROVIDER == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
        )
    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}. "
            "Use 'openai', 'anthropic', or 'google'."
        )
