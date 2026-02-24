"""Secure step: input sanitization and path validation."""

import re
from pathlib import Path

from config import CONTEXT_DIR


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
