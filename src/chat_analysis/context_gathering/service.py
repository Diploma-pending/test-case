"""Context gathering service: fetch website HTML, extract text, generate structured context via LLM."""

import socket
from ipaddress import ip_address
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from chat_analysis.context_gathering.models import GatheredContext
from chat_analysis.context_gathering.prompts import GATHER_CONTEXT_SYSTEM_TEMPLATE
from chat_analysis.core.security import sanitize_text

_MAX_DOWNLOAD_BYTES = 2 * 1024 * 1024  # 2 MB
_MAX_TEXT_CHARS = 12_000
_REQUEST_TIMEOUT = 15.0


class ContextGatheringError(Exception):
    """Raised when context gathering fails at any stage."""


def validate_url(url: str) -> str:
    """Validate URL scheme and block SSRF by resolving hostname to a public IP.

    Returns the original URL if valid.
    Raises ContextGatheringError for invalid scheme or private/loopback addresses.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ContextGatheringError(f"Invalid URL scheme '{parsed.scheme}': only http and https are allowed")

    hostname = parsed.hostname
    if not hostname:
        raise ContextGatheringError("URL has no hostname")

    try:
        results = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise ContextGatheringError(f"Cannot resolve hostname '{hostname}': {exc}") from exc

    for result in results:
        addr = result[4][0]
        try:
            ip = ip_address(addr)
        except ValueError:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ContextGatheringError(
                f"Blocked: hostname '{hostname}' resolves to a private/loopback address ({addr})"
            )

    return url


def fetch_html(url: str) -> str:
    """Fetch HTML from a URL with a 15s timeout and 2 MB download cap.

    Raises ContextGatheringError on timeout or HTTP errors.
    """
    try:
        with httpx.Client(timeout=_REQUEST_TIMEOUT, follow_redirects=True) as client:
            with client.stream("GET", url) as response:
                response.raise_for_status()
                chunks: list[bytes] = []
                total = 0
                for chunk in response.iter_bytes(chunk_size=8192):
                    total += len(chunk)
                    if total > _MAX_DOWNLOAD_BYTES:
                        chunks.append(chunk[: _MAX_DOWNLOAD_BYTES - (total - len(chunk))])
                        break
                    chunks.append(chunk)
                return b"".join(chunks).decode("utf-8", errors="replace")
    except httpx.TimeoutException as exc:
        raise ContextGatheringError(f"Request timed out fetching '{url}'") from exc
    except httpx.HTTPStatusError as exc:
        raise ContextGatheringError(
            f"HTTP {exc.response.status_code} fetching '{url}'"
        ) from exc
    except httpx.RequestError as exc:
        raise ContextGatheringError(f"Network error fetching '{url}': {exc}") from exc


def extract_text(html: str) -> str:
    """Extract visible text from HTML using BeautifulSoup.

    Removes script/style/nav/footer/header/aside tags.
    Caps output at 12,000 characters.
    Raises ContextGatheringError if no text is extracted.
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    if not text:
        raise ContextGatheringError("No text could be extracted from the page")

    return text[:_MAX_TEXT_CHARS]


def gather_context(url: str, llm) -> GatheredContext:
    """Full pipeline: validate URL → fetch HTML → extract text → sanitize → LLM chain.

    Args:
        url: The website URL to gather context from.
        llm: A LangChain LLM instance (from get_llm()).

    Returns:
        GatheredContext with the structured markdown context document.

    Raises:
        ContextGatheringError: If any step fails.
    """
    validated_url = validate_url(url)
    html = fetch_html(validated_url)
    raw_text = extract_text(html)
    sanitized_text = sanitize_text(raw_text)

    prompt = ChatPromptTemplate.from_messages([
        ("system", GATHER_CONTEXT_SYSTEM_TEMPLATE),
    ])
    chain = prompt | llm | StrOutputParser()

    context_document: str = chain.invoke({"website_text": sanitized_text})

    return GatheredContext(
        url=validated_url,
        raw_text=sanitized_text,
        context_document=context_document,
        char_count=len(context_document),
    )
