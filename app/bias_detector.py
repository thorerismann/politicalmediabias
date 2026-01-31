from __future__ import annotations

from app.html_parser import extract_main_text


def _looks_like_html(text: str) -> bool:
    return "<" in text and ">" in text


def truncate_words(text: str, max_words: int = 250) -> str:
    words = text.split()
    return " ".join(words[:max_words])


def prepare_bias_prompt(raw_input: str, max_words: int = 250) -> str:
    if _looks_like_html(raw_input):
        cleaned_text = extract_main_text(raw_input)
    else:
        cleaned_text = raw_input.strip()

    truncated_text = truncate_words(cleaned_text, max_words=max_words)

    return (
        "You are a media bias analyst. Classify the political bias of the text as "
        "left, right, or neutral. Respond ONLY with a JSON object using keys "
        '"bias", "confidence", and "rationale". The rationale should be 1-3 sentences.\n\n'
        f'Text:\n"""\n{truncated_text}\n"""'
    )
