"""
Read and validate robots.txt.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_ROBOTS = """User-agent: *
Allow: /

Sitemap: https://www.freemindconsult.com/sitemap.xml
"""


class RobotsManager:
    def __init__(self, website_root: str):
        self._root = Path(website_root)
        self._path = self._root / "robots.txt"

    def exists(self) -> bool:
        return self._path.exists()

    def read(self) -> str:
        if self._path.exists():
            return self._path.read_text(encoding="utf-8")
        return ""

    def validate(self) -> list[str]:
        issues = []
        if not self.exists():
            issues.append("robots.txt is missing")
            return issues
        content = self.read()
        if "Sitemap:" not in content:
            issues.append("robots.txt missing Sitemap directive")
        if "User-agent:" not in content:
            issues.append("robots.txt missing User-agent directive")
        if "Disallow: /" in content and "Allow:" not in content:
            issues.append("robots.txt blocks all crawling")
        return issues

    def create_default(self) -> str:
        self._path.write_text(DEFAULT_ROBOTS, encoding="utf-8")
        logger.info("Created default robots.txt")
        return DEFAULT_ROBOTS
