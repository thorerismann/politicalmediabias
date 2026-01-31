"""Helpers for building prompts and running bias analysis with Mistral."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from typing import Any

from app.html_parser import extract_text_from_input

LOGGER = logging.getLogger(__name__)
DEFAULT_MAX_WORDS = 200
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

def truncate_words(text: str, max_words: int = DEFAULT_MAX_WORDS) -> str:
    """Truncate text to a maximum number of words.

    Args:
        text: Source text to truncate.
        max_words: Maximum number of words to keep.

    Returns:
        The truncated text preserving word order.
    """
    words = text.split()
    return " ".join(words[:max_words])

def prepare_bias_input(raw_input: str, max_words: int = DEFAULT_MAX_WORDS) -> tuple[str, dict]:
    """Prepare the Mistral prompt and metadata for bias analysis.

    Args:
        raw_input: The raw text, HTML, or URL provided by the user.
        max_words: Maximum number of words to include in the prompt.

    Returns:
        A tuple of the formatted prompt and metadata about extraction and truncation.
    """
    LOGGER.debug("Preparing bias prompt with max_words=%s", max_words)
    cleaned_text, metadata = extract_text_from_input(raw_input)
    original_word_count = len(cleaned_text.split())
    truncated_text = truncate_words(cleaned_text, max_words=max_words)
    truncated_word_count = len(truncated_text.split())
    words_cut = max(0, original_word_count - truncated_word_count)
    metadata.update(
        {
            "original_word_count": original_word_count,
            "truncated_word_count": truncated_word_count,
            "words_cut": words_cut,
        }
    )
    LOGGER.info("Prepared prompt with %s words (%s cut).", truncated_word_count, words_cut)

    prompt = (
        "You are a media bias analyst. Classify the political bias of the text as "
        "left, right, or neutral. Respond ONLY with a JSON object using keys "
        '"bias", "confidence", and "rationale". The rationale should be 1-3 sentences.\n\n'
        f'Text:\n"""\n{truncated_text}\n"""'
    )
    return prompt, metadata


def prepare_bias_prompt(raw_input: str, max_words: int = DEFAULT_MAX_WORDS) -> str:
    """Generate only the prompt for bias analysis.

    Args:
        raw_input: The raw text, HTML, or URL provided by the user.
        max_words: Maximum number of words to include in the prompt.

    Returns:
        The prompt string sent to the model.
    """
    prompt, _ = prepare_bias_input(raw_input, max_words=max_words)
    return prompt


def _extract_json_payload(output: str) -> dict[str, Any] | None:
    """Extract a JSON object from model output.

    Args:
        output: The raw model output string.

    Returns:
        The parsed JSON payload when possible, otherwise ``None``.
    """
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
    """Write the prompt, raw output, and parsed JSON to disk.

    Args:
        log_path: Path to the log file to write.
        prompt: The prompt sent to the model.
        output: The raw output from the model.
        parsed: Parsed JSON payload, if available.
    """
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


def analyze_with_mistral(
    raw_input: str,
    max_words: int = DEFAULT_MAX_WORDS,
    prepared_prompt: str | None = None,
) -> dict:
    """Run bias analysis using the local Mistral model via Ollama.

    Args:
        raw_input: The raw text, HTML, or URL provided by the user.
        max_words: Maximum number of words to include in the prompt.
        prepared_prompt: Optional pre-built prompt to reuse.

    Returns:
        The model response dictionary with bias classification details.
    """
    prompt = prepared_prompt or prepare_bias_prompt(raw_input, max_words=max_words)
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
