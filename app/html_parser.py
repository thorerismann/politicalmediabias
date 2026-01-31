# app/html_parser.py

from bs4 import BeautifulSoup

def extract_main_text(html_content: str) -> str:
    soup = BeautifulSoup(html_content, 'html.parser')
    if soup.body:
        return soup.body.get_text(separator=' ', strip=True)
    return soup.get_text(separator=' ', strip=True)
