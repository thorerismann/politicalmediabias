# tests/test_html_parser.py

from app.html_parser import extract_main_text, extract_text_from_input

def test_extract_main_text_from_html():
    html = "<html><body><h1>Title</h1><p>This is a test.</p></body></html>"
    result = extract_main_text(html)
    assert "Title" in result
    assert "This is a test." in result


def test_extract_text_from_url(monkeypatch):
    html = "<html><body><p>Article text.</p></body></html>"

    class DummyResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return html.encode("utf-8")

    def fake_urlopen(_request, timeout=10):
        return DummyResponse()

    monkeypatch.setattr("app.html_parser.request.urlopen", fake_urlopen)

    text, metadata = extract_text_from_input("https://example.com/article")
    assert "Article text." in text
    assert metadata["source"] == "url"
