"""Secure step: input sanitization and path validation."""

import re
from pathlib import Path

from chat_analysis.core.config import CONTEXT_DIR, DOMAINS_DIR


# Patterns commonly used in prompt injection attempts
_INJECTION_PATTERNS = [
    r"ignore\s+(previous|above|all)\s+(instructions|prompts)",
    r"you\s+are\s+now\s+",
    r"new\s+instructions?\s*:",
    r"system\s*:\s*",
    r"<\s*system\s*>",
    r"\[INST\]",
    r"\[/INST\]",
    r"<<\s*SYS\s*>>",
    r"human\s*:\s*\n",
    r"assistant\s*:\s*\n",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


def sanitize_text(text: str) -> str:
    """Strip potential prompt injection patterns from text.

    Removes known injection patterns while preserving the rest of the content.
    """
    sanitized = text
    for pattern in _COMPILED_PATTERNS:
        sanitized = pattern.sub("[FILTERED]", sanitized)
    return sanitized.strip()


def validate_context_file(filename: str) -> Path:
    """Validate that a context filename is safe and within the context directory.

    Prevents path traversal attacks by resolving the path and checking
    it stays within CONTEXT_DIR.

    Raises:
        ValueError: If the filename contains path traversal or points outside CONTEXT_DIR.
    """
    if ".." in filename or filename.startswith("/"):
        raise ValueError(f"Invalid context filename: {filename}")

    filepath = (CONTEXT_DIR / filename).resolve()

    if not filepath.is_relative_to(CONTEXT_DIR.resolve()):
        raise ValueError(f"Path traversal detected: {filename}")

    if not filepath.suffix == ".md":
        raise ValueError(f"Only .md context files are allowed, got: {filename}")

    return filepath


def normalize_domain_name(topic: str) -> str:
    """Normalize a topic string into a safe filename stem.

    Lowercases, strips whitespace, replaces non-alphanumeric chars with '_',
    and strips trailing underscores.
    E.g. "Brighterly" → "brighterly", "Max Beauty" → "max_beauty".
    """
    name = topic.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def load_domain_context(topic: str) -> str | None:
    """Try to load a pre-built domain context file from domains/ for the given topic.

    First tries an exact normalized match, then a compact match (stripping underscores)
    against all .md files in DOMAINS_DIR.

    Returns the sanitized file content, or None if no match is found.
    """
    normalized = normalize_domain_name(topic)
    if not normalized:
        return None

    # Exact match
    filepath = (DOMAINS_DIR / f"{normalized}.md").resolve()
    if filepath.is_relative_to(DOMAINS_DIR.resolve()) and filepath.exists():
        content = filepath.read_text(encoding="utf-8")
        return sanitize_text(content)

    # Compact match: strip underscores and compare
    compact = normalized.replace("_", "")
    if DOMAINS_DIR.is_dir():
        for candidate in DOMAINS_DIR.glob("*.md"):
            candidate_compact = candidate.stem.replace("_", "")
            if candidate_compact == compact:
                resolved = candidate.resolve()
                if resolved.is_relative_to(DOMAINS_DIR.resolve()):
                    content = resolved.read_text(encoding="utf-8")
                    return sanitize_text(content)

    return None


def load_context_safely(domain: str) -> str:
    """Load and sanitize a domain-specific context file.

    Args:
        domain: The domain name (e.g., 'payment_issues'), used as the filename stem.

    Returns:
        Sanitized content of the context file, or empty string if not found.
    """
    filename = f"{domain}.md"
    try:
        filepath = validate_context_file(filename)
    except ValueError:
        return ""

    if not filepath.exists():
        return ""

    content = filepath.read_text(encoding="utf-8")
    return sanitize_text(content)
