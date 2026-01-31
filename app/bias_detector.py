from __future__ import annotations

import subprocess
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


def analyze_with_mistral(raw_input: str, max_words: int = 800) -> dict:
    prompt = f"""
Classify the political bias of the following text as 'left', 'right', or 'neutral'. 
Only return a JSON object with a single field: "bias".

Text (max {max_words} words):
{raw_input[:max_words * 6]}  # crude character-based trim
"""

    try:
        result = subprocess.run(
            ["ollama", "run", "mistral"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=240
        )
        output = result.stdout.strip()

        # Try parsing a JSON object from the output
        import json
        for line in output.splitlines():
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue

        return {"bias": "unknown", "raw_output": output}

    except subprocess.TimeoutExpired:
        return {"bias": "timeout"}
    except Exception as e:
        return {"bias": f"error: {e}"}
