from app.bias_detector import prepare_bias_prompt, truncate_words


def test_truncate_words_limits_to_250():
    text = "word " * 300
    truncated = truncate_words(text, max_words=250)
    assert len(truncated.split()) == 250


def test_prepare_bias_prompt_with_html():
    html = "<html><body><h1>Headline</h1><p>Some article text.</p></body></html>"
    prompt = prepare_bias_prompt(html, max_words=250)
    assert '"bias"' in prompt
    assert "Headline" in prompt
    assert "Some article text." in prompt
