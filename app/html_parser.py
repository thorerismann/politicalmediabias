"""Utilities for extracting text from HTML or URL inputs."""

import logging
from urllib import parse, request

from bs4 import BeautifulSoup

LOGGER = logging.getLogger(__name__)
MIN_RTS_BODY_WORDS = 30


def _is_probable_url(text: str) -> bool:
    """Check whether a string looks like an HTTP(S) URL.

    Args:
        text: Input string to evaluate.

    Returns:
        ``True`` if the string has an HTTP(S) scheme and netloc.
    """
    parsed = parse.urlparse(text)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _fetch_url_content(url: str, timeout: int = 10) -> str:
    """Fetch HTML content from a URL.

    Args:
        url: URL to request.
        timeout: Timeout in seconds for the request.

    Returns:
        The decoded HTML response body.
    """
    LOGGER.info("Fetching URL content for extraction: %s", url)
    req = request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; BiasAnalyzer/1.0)"},
    )
    with request.urlopen(req, timeout=timeout) as response:  # noqa: S310
        return response.read().decode("utf-8", errors="replace")


def extract_main_text(html_content: str) -> str:
    """Extract visible text from an HTML document.

    Args:
        html_content: HTML markup to parse.

    Returns:
        The extracted text with whitespace normalized.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    if soup.body:
        LOGGER.debug("Extracted text from HTML body.")
        return soup.body.get_text(separator=" ", strip=True)
    LOGGER.debug("Extracted text from full HTML document.")
    return soup.get_text(separator=" ", strip=True)


def extract_text_from_input(raw_input: str) -> tuple[str, dict]:
    """Normalize input into plain text and metadata.

    Args:
        raw_input: The raw text, HTML, or URL provided by the user.

    Returns:
        A tuple containing the extracted text and metadata describing the source.
    """
    cleaned_input = raw_input.strip()
    metadata = {
        "source": "text",
        "extracted": False,
        "url": None,
    }

    if not cleaned_input:
        return "", metadata

    if _is_probable_url(cleaned_input):
        html_content = _fetch_url_content(cleaned_input)
        extracted_text = extract_main_text(html_content)
        metadata.update(
            {
                "source": "url",
                "extracted": True,
                "url": cleaned_input,
            }
        )
        LOGGER.info("Extracted main text from URL input.")
        return extracted_text, metadata

    if "<" in cleaned_input and ">" in cleaned_input:
        LOGGER.info("Detected HTML input; extracting main text.")
        metadata.update({"source": "html", "extracted": True})
        return extract_main_text(cleaned_input), metadata

    LOGGER.info("Detected plain text input; trimming whitespace.")
    return cleaned_input, metadata


def _extract_rts_text(element: BeautifulSoup | None) -> str | None:
    """Extract and normalize text from a BeautifulSoup element."""
    if not element:
        return None
    text = element.get_text(separator=" ", strip=True)
    return text or None


def extract_rts_article(html_content: str) -> dict:
    """Extract RTS article fields from HTML content.

    Args:
        html_content: HTML markup to parse.

    Returns:
        A dictionary with keys: title, body, source, credits, date.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    body_text = _extract_rts_text(soup.select_one(".article-part.article-body"))
    if not body_text or len(body_text.split()) < MIN_RTS_BODY_WORDS:
        LOGGER.warning("RTS article body missing or too short.")
        return {
            "title": None,
            "body": None,
            "source": None,
            "credits": None,
            "date": None,
        }

    title_text = _extract_rts_text(
        soup.select_one("h1.article-part.article-title")
    )
    source_text = _extract_rts_text(soup.select_one(".sources"))
    credits_text = _extract_rts_text(soup.select_one(".credit"))
    date_meta = soup.find("meta", attrs={"name": "dcterms.created"})
    date_value = date_meta.get("content") if date_meta else None

    return {
        "title": title_text,
        "body": body_text,
        "source": source_text,
        "credits": credits_text,
        "date": date_value,
    }


def extract_rts_article_from_input(raw_input: str) -> dict:
    """Extract RTS article fields from a URL or HTML string.

    Args:
        raw_input: A URL or raw HTML string.

    Returns:
        A dictionary with keys: title, body, source, credits, date.
    """
    cleaned_input = raw_input.strip()
    if not cleaned_input:
        return {
            "title": None,
            "body": None,
            "source": None,
            "credits": None,
            "date": None,
        }

    if _is_probable_url(cleaned_input):
        html_content = _fetch_url_content(cleaned_input)
        return extract_rts_article(html_content)

    if "<" in cleaned_input and ">" in cleaned_input:
        return extract_rts_article(cleaned_input)

    LOGGER.warning("RTS article extraction requires HTML or URL input.")
    return {
        "title": None,
        "body": None,
        "source": None,
        "credits": None,
        "date": None,
    }
