"""
Optimize body content — headings, keyword placement, word count.
"""

import logging
import re
from pathlib import Path

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ContentOptimizer:
    @staticmethod
    def fix_h1(html: str, desired_h1: str) -> str:
        """Ensure exactly one H1 with the desired text."""
        soup = BeautifulSoup(html, "html.parser")
        h1s = soup.find_all("h1")
        if not h1s:
            body = soup.find("body")
            if body:
                main = body.find("main") or body
                first_child = main.find(["section", "div", "header"])
                tag = soup.new_tag("h1")
                tag.string = desired_h1
                if first_child:
                    first_child.insert(0, tag)
                else:
                    main.insert(0, tag)
            return str(soup)
        # Update first H1, remove extras
        h1s[0].string = desired_h1
        for extra in h1s[1:]:
            extra.name = "h2"
        return str(soup)

    @staticmethod
    def get_word_count(html: str) -> int:
        soup = BeautifulSoup(html, "html.parser")
        body = soup.find("body")
        if body:
            return len(body.get_text(separator=" ", strip=True).split())
        return 0

    @staticmethod
    def check_keyword_in_first_100_words(html: str, keyword: str) -> bool:
        soup = BeautifulSoup(html, "html.parser")
        body = soup.find("body")
        if not body:
            return False
        words = body.get_text(separator=" ", strip=True).split()[:100]
        return keyword.lower() in " ".join(words).lower()

    @staticmethod
    def add_last_updated_date(html: str, date: str) -> str:
        """Add a visible 'Last Updated' line after the H1."""
        if f"Last updated" in html or f"Last Updated" in html:
            return html
        soup = BeautifulSoup(html, "html.parser")
        h1 = soup.find("h1")
        if h1:
            date_tag = soup.new_tag("p", style="font-size:14px;color:var(--color-text-muted);margin-top:8px;")
            date_tag.string = f"Last updated: {date}"
            h1.insert_after(date_tag)
        return str(soup)
