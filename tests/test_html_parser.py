# tests/test_html_parser.py

from app.html_parser import extract_main_text

def test_extract_main_text_from_html():
    html = "<html><body><h1>Title</h1><p>This is a test.</p></body></html>"
    result = extract_main_text(html)
    assert "Title" in result
    assert "This is a test." in result
