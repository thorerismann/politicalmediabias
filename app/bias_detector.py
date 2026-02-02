"""Helpers for building prompts and running bias analysis with local models."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import streamlit as st
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


def _render_custom_prompt(prompt_template: str, truncated_text: str) -> str:
    """Render a custom prompt template.

    Args:
        prompt_template: The user-provided prompt template.
        truncated_text: The truncated article text.

    Returns:
        A prompt string ready to send to the model.
    """
    if "{text}" in prompt_template:
        return prompt_template.format(text=truncated_text)
    return f"{prompt_template.rstrip()}\n\nText:\n\"\"\"\n{truncated_text}\n\"\"\""


def prepare_bias_input(
    raw_input: str,
    max_words: int = DEFAULT_MAX_WORDS,
    prompt_template: str | None = None,
) -> tuple[str, dict]:
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

    if prompt_template:
        prompt = _render_custom_prompt(prompt_template, truncated_text)
    else:
        prompt = (
            "You are a media bias analyst. Score the political bias of the text on a "
            "scale from -1 (left) to 1 (right), with 0 as neutral. Respond ONLY with "
            'a JSON object using keys "bias", "confidence", and "reasoning". The '
            "reasoning should be 1-3 sentences.\n\n"
            f'Text:\n"""\n{truncated_text}\n"""'
        )
    return prompt, metadata


def prepare_bias_prompt(
    raw_input: str,
    max_words: int = DEFAULT_MAX_WORDS,
    prompt_template: str | None = None,
) -> str:
    """Generate only the prompt for bias analysis.

    Args:
        raw_input: The raw text, HTML, or URL provided by the user.
        max_words: Maximum number of words to include in the prompt.

    Returns:
        The prompt string sent to the model.
    """
    prompt, _ = prepare_bias_input(
        raw_input,
        max_words=max_words,
        prompt_template=prompt_template,
    )
    return prompt


def parse_bias_score(bias_value: Any) -> float | None:
    """Parse a bias value into a numeric score between -1 and 1.

    Args:
        bias_value: Bias value returned by the model (string or numeric).

    Returns:
        The normalized bias score or ``None`` if parsing fails.
    """
    if bias_value is None:
        return None
    if isinstance(bias_value, (int, float)):
        return max(-1.0, min(1.0, float(bias_value)))
    if isinstance(bias_value, str):
        normalized = bias_value.strip().lower()
        if normalized in {"left", "liberal"}:
            return -1.0
        if normalized in {"right", "conservative"}:
            return 1.0
        if normalized in {"neutral", "center", "centre", "middle"}:
            return 0.0
        try:
            numeric = float(normalized)
        except ValueError:
            return None
        return max(-1.0, min(1.0, numeric))
    return None


def normalize_bias_response(result: dict[str, Any]) -> dict[str, Any]:
    """Normalize a model response to ensure consistent bias fields.

    Args:
        result: Parsed model response from the analysis call.

    Returns:
        A dictionary with normalized ``bias`` and ``reasoning`` fields.
    """
    normalized = dict(result)
    st.write(normalized)
    bias_score = parse_bias_score(normalized.get("bias"))
    if bias_score is not None:
        normalized["bias"] = bias_score
    rationale = normalized.get("reasoning") or normalized.get("rationale")
    if rationale is not None:
        normalized["reasoning"] = rationale
    return normalized


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


def analyze_with_model(
    raw_input: str,
    model_name: str,
    max_words: int = DEFAULT_MAX_WORDS,
    prepared_prompt: str | None = None,
) -> dict[str, Any]:
    """Run bias analysis using a local Ollama model.

    Args:
        raw_input: The raw text, HTML, or URL provided by the user.
        model_name: The Ollama model name to run.
        max_words: Maximum number of words to include in the prompt.
        prepared_prompt: Optional pre-built prompt to reuse.

    Returns:
        The model response dictionary with bias classification details.
    """
    prompt = prepared_prompt or prepare_bias_prompt(raw_input, max_words=max_words)
    log_path = os.getenv("BIAS_LOG_PATH", f"{model_name}_run.log")

    try:
        result = subprocess.run(
            ["ollama", "run", model_name],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=240
        )
        output = result.stdout.strip()
        parsed = _extract_json_payload(output)
        _write_run_log(log_path, prompt, output, parsed)
        if parsed is not None:
            parsed_with_raw = dict(parsed)
            parsed_with_raw.setdefault("raw_output", output)
            return parsed_with_raw
        return {"bias": "unknown", "raw_output": output}

    except subprocess.TimeoutExpired:
        return {"bias": "timeout"}
    except Exception as e:
        return {"bias": f"error: {e}"}


def analyze_with_mistral(
    raw_input: str,
    max_words: int = DEFAULT_MAX_WORDS,
    prepared_prompt: str | None = None,
) -> dict:
    """Run bias analysis using the local Mistral model via Ollama."""
    return analyze_with_model(
        raw_input,
        model_name="mistral",
        max_words=max_words,
        prepared_prompt=prepared_prompt,
    )


def analyze_with_tinyllama(
    raw_input: str,
    max_words: int = DEFAULT_MAX_WORDS,
    prepared_prompt: str | None = None,
) -> dict:
    """Run bias analysis using the TinyLlama model via Ollama."""
    return analyze_with_model(
        raw_input,
        model_name="tinyllama",
        max_words=max_words,
        prepared_prompt=prepared_prompt,
    )
