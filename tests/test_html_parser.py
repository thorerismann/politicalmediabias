"""Tests for HTML parsing helpers."""

from app.html_parser import extract_main_text, extract_text_from_input

def test_extract_main_text_from_html():
    """Ensure main text extraction pulls content from HTML bodies."""
    html = "<html><body><h1>Title</h1><p>This is a test.</p></body></html>"
    result = extract_main_text(html)
    assert "Title" in result
    assert "This is a test." in result


def test_extract_text_from_url(monkeypatch):
    """Ensure URL input returns extracted text and URL metadata."""
    html = "<html><body><p>Article text.</p></body></html>"

    class DummyResponse:
        def __enter__(self):
            """Return the dummy response instance."""
            return self

        def __exit__(self, exc_type, exc, tb):
            """No-op context manager cleanup."""
            return False

        def read(self):
            """Return encoded HTML content."""
            return html.encode("utf-8")

    def fake_urlopen(_request, timeout=10):
        """Return a dummy response for urlopen calls."""
        return DummyResponse()

    monkeypatch.setattr("app.html_parser.request.urlopen", fake_urlopen)

    text, metadata = extract_text_from_input("https://example.com/article")
    assert "Article text." in text
    assert metadata["source"] == "url"
