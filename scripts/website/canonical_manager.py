"""
Manage canonical tags across all pages.
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

DOMAIN = "https://www.freemindconsult.com"


class CanonicalManager:
    @staticmethod
    def read_canonical(html: str) -> str:
        match = re.search(r'<link\s+rel="canonical"\s+href="([^"]*)"', html)
        return match.group(1) if match else ""

    @staticmethod
    def set_canonical(html: str, url: str) -> str:
        if re.search(r'<link\s+rel="canonical"', html):
            return re.sub(r'(<link\s+rel="canonical"\s+href=")[^"]*(")', rf'\g<1>{url}\2', html, count=1)
        return html.replace("</title>", f'</title>\n  <link rel="canonical" href="{url}">')

    @staticmethod
    def build_canonical_url(relative_url: str) -> str:
        if relative_url == "/":
            return DOMAIN + "/"
        return DOMAIN + relative_url

    @staticmethod
    def validate_canonical(html: str, expected_url: str) -> list[str]:
        issues = []
        current = CanonicalManager.read_canonical(html)
        if not current:
            issues.append("missing_canonical")
        elif current != expected_url:
            issues.append(f"canonical_mismatch: '{current}' should be '{expected_url}'")
        return issues
