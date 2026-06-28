"""
Generate and validate XML sitemaps from the crawled page inventory.
"""

import logging
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from .crawler import PageData

logger = logging.getLogger(__name__)

DOMAIN = "https://www.freemindconsult.com"
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


class SitemapManager:
    def __init__(self, website_root: str):
        self._root = Path(website_root)
        self._path = self._root / "sitemap.xml"

    def exists(self) -> bool:
        return self._path.exists()

    def generate(self, pages: list[PageData]) -> str:
        """Generate a sitemap.xml from crawled pages."""
        today = datetime.now().strftime("%Y-%m-%d")
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append(f'<urlset xmlns="{NS}">')

        for page in sorted(pages, key=lambda p: p.relative_url):
            url = page.url
            priority = "1.0" if page.relative_url == "/" else "0.8" if "/blog/" not in page.relative_url else "0.6"
            changefreq = "weekly" if "/blog/" in page.relative_url else "monthly"
            lines.append("  <url>")
            lines.append(f"    <loc>{url}</loc>")
            lines.append(f"    <lastmod>{today}</lastmod>")
            lines.append(f"    <changefreq>{changefreq}</changefreq>")
            lines.append(f"    <priority>{priority}</priority>")
            lines.append("  </url>")

        lines.append("</urlset>")
        xml = "\n".join(lines)
        logger.info("Generated sitemap with %d URLs", len(pages))
        return xml

    def validate(self, pages: list[PageData]) -> list[str]:
        """Check existing sitemap against crawled pages."""
        issues = []
        if not self.exists():
            issues.append("sitemap.xml not found")
            return issues

        try:
            tree = ET.parse(self._path)
            root = tree.getroot()
            ns = {"sm": NS}
            sitemap_urls = set()
            for url_elem in root.findall("sm:url/sm:loc", ns):
                sitemap_urls.add(url_elem.text)

            page_urls = {p.url for p in pages}
            missing = page_urls - sitemap_urls
            extra = sitemap_urls - page_urls

            for url in missing:
                issues.append(f"Page not in sitemap: {url}")
            for url in extra:
                issues.append(f"Sitemap URL has no matching page: {url}")
        except ET.ParseError as e:
            issues.append(f"Sitemap XML parse error: {e}")

        return issues

    def save(self, xml_content: str):
        self._path.write_text(xml_content, encoding="utf-8")
        logger.info("Saved sitemap.xml (%d bytes)", len(xml_content))
