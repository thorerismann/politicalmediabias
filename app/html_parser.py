# app/html_parser.py

import logging
from urllib import parse, request

from bs4 import BeautifulSoup

LOGGER = logging.getLogger(__name__)


def _is_probable_url(text: str) -> bool:
    parsed = parse.urlparse(text)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _fetch_url_content(url: str, timeout: int = 10) -> str:
    LOGGER.info("Fetching URL content for extraction: %s", url)
    req = request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; BiasAnalyzer/1.0)"},
    )
    with request.urlopen(req, timeout=timeout) as response:  # noqa: S310
        return response.read().decode("utf-8", errors="replace")


def extract_main_text(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    if soup.body:
        LOGGER.debug("Extracted text from HTML body.")
        return soup.body.get_text(separator=" ", strip=True)
    LOGGER.debug("Extracted text from full HTML document.")
    return soup.get_text(separator=" ", strip=True)


def extract_text_from_input(raw_input: str) -> tuple[str, dict]:
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
