"""Tests for bias detector helpers."""

from app.bias_detector import prepare_bias_input, prepare_bias_prompt, truncate_words


def test_truncate_words_limits_to_200():
    """Truncation should respect the max word count."""
    text = "word " * 300
    truncated = truncate_words(text, max_words=200)
    assert len(truncated.split()) == 200


def test_prepare_bias_prompt_with_html():
    """Prompt generation should include extracted HTML text."""
    html = "<html><body><h1>Headline</h1><p>Some article text.</p></body></html>"
    prompt = prepare_bias_prompt(html, max_words=200)
    assert '"bias"' in prompt
    assert "Headline" in prompt
    assert "Some article text." in prompt


def test_prepare_bias_input_tracks_words_cut():
    """Metadata should track words removed during truncation."""
    text = "word " * 10
    prompt, metadata = prepare_bias_input(text, max_words=5)
    assert '"bias"' in prompt
    assert metadata["words_cut"] == 5
