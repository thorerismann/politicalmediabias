"""Batch processing utilities for serial bias analysis."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.bias_detector import (
    analyze_with_model,
    normalize_bias_response,
    prepare_bias_input,
)


def _write_result_json(output_path: Path, payload: dict[str, Any]) -> None:
    """Write a JSON payload to disk.

    Args:
        output_path: File path for the JSON output.
        payload: Parsed JSON payload to write.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def analyze_text_folder(
    folder_path: str,
    model_name: str,
    max_words: int,
    prompt_template: str | None = None,
) -> dict[str, Any]:
    """Analyze each text file in a folder and save JSON results.

    Args:
        folder_path: Path to the folder containing `.txt` files.
        model_name: The Ollama model name to run.
        max_words: Maximum number of words to include in each prompt.
        prompt_template: Optional prompt template to override the default.

    Returns:
        A summary dictionary with the processed file count and results directory.

    Raises:
        ValueError: If the folder is missing or contains no `.txt` files.
    """
    target_dir = Path(folder_path).expanduser().resolve()
    if not target_dir.exists() or not target_dir.is_dir():
        raise ValueError(f"Folder not found: {target_dir}")

    text_files = sorted(target_dir.glob("*.txt"))
    if not text_files:
        raise ValueError(f"No .txt files found in {target_dir}")

    results_dir = target_dir / "results"
    processed = 0

    for text_file in text_files:
        raw_text = text_file.read_text(encoding="utf-8")
        prompt, _ = prepare_bias_input(
            raw_text,
            max_words=max_words,
            prompt_template=prompt_template,
        )
        result = analyze_with_model(
            raw_text,
            model_name=model_name,
            max_words=max_words,
            prepared_prompt=prompt,
        )
        normalized = normalize_bias_response(result)
        output_payload = {
            "text": raw_text,
            "bias": normalized.get("bias"),
            "confidence": normalized.get("confidence"),
            "reasoning": normalized.get("reasoning"),
            "reasoining": normalized.get("reasoning"),
            "raw_output": normalized.get("raw_output"),
        }
        output_path = results_dir / f"{text_file.stem}.json"
        _write_result_json(output_path, output_payload)
        processed += 1

    return {
        "processed_files": processed,
        "results_directory": str(results_dir),
    }
