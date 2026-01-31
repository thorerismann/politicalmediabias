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


def _extract_json_payload(output: str) -> dict[str, Any] | None:
    if not output:
        return None

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        pass

    start = output.find("{")
    end = output.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        return json.loads(output[start : end + 1])
    except json.JSONDecodeError:
        return None


def _write_run_log(log_path: str, prompt: str, output: str, parsed: dict[str, Any] | None) -> None:
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write("=== Prompt ===\n")
        log_file.write(prompt)
        log_file.write("\n\n=== Raw Output ===\n")
        log_file.write(output)
        log_file.write("\n\n=== Parsed JSON ===\n")
        if parsed is None:
            log_file.write("None\n")
        else:
            log_file.write(json.dumps(parsed, indent=2))
            log_file.write("\n")


def analyze_with_mistral(raw_input: str, max_words: int = DEFAULT_MAX_WORDS) -> dict:
    prompt = prepare_bias_prompt(raw_input, max_words=max_words)
    log_path = os.getenv("BIAS_LOG_PATH", "mistral_run.log")

    try:
        result = subprocess.run(
            ["ollama", "run", "mistral"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=240
        )
        output = result.stdout.strip()
        parsed = _extract_json_payload(output)
        _write_run_log(log_path, prompt, output, parsed)
        if parsed is not None:
            return parsed
        return {"bias": "unknown", "raw_output": output}

    except subprocess.TimeoutExpired:
        return {"bias": "timeout"}
    except Exception as e:
        return {"bias": f"error: {e}"}
