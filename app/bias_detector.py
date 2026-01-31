from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib import request

from app.html_parser import extract_main_text

LOGGER = logging.getLogger(__name__)
DEFAULT_MAX_WORDS = 200
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"


def _looks_like_html(text: str) -> bool:
    return "<" in text and ">" in text


def truncate_words(text: str, max_words: int = DEFAULT_MAX_WORDS) -> str:
    words = text.split()
    return " ".join(words[:max_words])


def prepare_bias_prompt(raw_input: str, max_words: int = DEFAULT_MAX_WORDS) -> str:
    LOGGER.debug("Preparing bias prompt with max_words=%s", max_words)
    if _looks_like_html(raw_input):
        LOGGER.info("Detected HTML input; extracting main text.")
        cleaned_text = extract_main_text(raw_input)
    else:
        LOGGER.info("Detected plain text input; trimming whitespace.")
        cleaned_text = raw_input.strip()

    truncated_text = truncate_words(cleaned_text, max_words=max_words)
    LOGGER.debug("Prepared prompt with %s words.", len(truncated_text.split()))

    return (
        "You are a media bias analyst. Classify the political bias of the text as "
        "left, right, or neutral. Respond ONLY with a JSON object using keys "
        '"bias", "confidence", and "rationale". The rationale should be 1-3 sentences.\n\n'
        f'Text:\n"""\n{truncated_text}\n"""'
    )


def analyze_with_mistral(raw_input: str, max_words: int = DEFAULT_MAX_WORDS) -> dict[str, Any]:
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("Missing MISTRAL_API_KEY environment variable.")

    prompt = prepare_bias_prompt(raw_input, max_words=max_words)
    payload = {
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }

    LOGGER.info("Sending prompt to Mistral API.")
    req = request.Request(
        MISTRAL_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with request.urlopen(req, timeout=30) as response:
        response_body = response.read().decode("utf-8")

    response_payload = json.loads(response_body)
    message = response_payload["choices"][0]["message"]["content"]
    LOGGER.info("Received response from Mistral API.")
    return json.loads(message)
