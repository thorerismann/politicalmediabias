# app/html_parser.py

import logging

from bs4 import BeautifulSoup

LOGGER = logging.getLogger(__name__)

def extract_main_text(html_content: str) -> str:
    soup = BeautifulSoup(html_content, 'html.parser')
    if soup.body:
        LOGGER.debug("Extracted text from HTML body.")
        return soup.body.get_text(separator=' ', strip=True)
    LOGGER.debug("Extracted text from full HTML document.")
    return soup.get_text(separator=' ', strip=True)
