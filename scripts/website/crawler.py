"""
Website crawler — builds a complete inventory of every page, its
metadata, structure, links, and SEO elements by parsing HTML files.
"""

import json
import logging
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SITE_DOMAIN = "https://www.freemindconsult.com"


@dataclass
class PageData:
    file_path: str
    url: str
    relative_url: str
    title: str = ""
    title_length: int = 0
    meta_description: str = ""
    meta_description_length: int = 0
    canonical: str = ""
    h1: list[str] = field(default_factory=list)
    h2: list[str] = field(default_factory=list)
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""
    og_url: str = ""
    twitter_title: str = ""
    twitter_description: str = ""
    twitter_card: str = ""
    schemas: list[dict] = field(default_factory=list)
    schema_types: list[str] = field(default_factory=list)
    internal_links: list[str] = field(default_factory=list)
    external_links: list[str] = field(default_factory=list)
    images: list[dict] = field(default_factory=list)
    word_count: int = 0
    has_faq: bool = False
    has_breadcrumb: bool = False
    hreflang: list[str] = field(default_factory=list)
    robots: str = ""
    lang: str = ""
    css_files: list[str] = field(default_factory=list)
    js_files: list[str] = field(default_factory=list)
    has_ga4: bool = False
    has_meta_pixel: bool = False
    raw_html_size: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


class WebsiteCrawler:
    def __init__(self, website_root: str, domain: str = SITE_DOMAIN):
        self._root = Path(website_root)
        self._domain = domain.rstrip("/")
        self._pages: list[PageData] = []

    def crawl(self) -> list[PageData]:
        """Crawl all HTML files and extract SEO data."""
        if not self._root.exists():
            logger.error("Website root not found: %s", self._root)
            return []

        html_files = sorted(self._root.rglob("*.html"))
        logger.info("Crawling %d HTML files from %s", len(html_files), self._root)

        self._pages = []
        for html_path in html_files:
            page = self._parse_page(html_path)
            if page:
                self._pages.append(page)

        logger.info("Crawled %d pages successfully", len(self._pages))
        return self._pages

    def get_pages(self) -> list[PageData]:
        return self._pages

    def get_page_by_url(self, url: str) -> PageData | None:
        url_clean = url.rstrip("/")
        for p in self._pages:
            if p.relative_url.rstrip("/") == url_clean or p.url == url_clean:
                return p
        return None

    def save_inventory(self, output_path: Path):
        """Save crawl results as JSON."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = [p.to_dict() for p in self._pages]
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Saved page inventory: %s (%d pages)", output_path, len(data))

    def _parse_page(self, html_path: Path) -> PageData | None:
        rel = html_path.relative_to(self._root)
        relative_url = "/" + str(rel).replace("\\", "/")
        if relative_url == "/index.html":
            relative_url = "/"
        url = self._domain + relative_url

        try:
            raw = html_path.read_text(encoding="utf-8", errors="ignore")
            soup = BeautifulSoup(raw, "html.parser")
        except Exception as e:
            logger.warning("Failed to parse %s: %s", relative_url, e)
            return None

        page = PageData(
            file_path=str(html_path),
            url=url,
            relative_url=relative_url,
            raw_html_size=len(raw),
        )

        # Title
        title_tag = soup.find("title")
        if title_tag:
            page.title = title_tag.get_text(strip=True)
            page.title_length = len(page.title)

        # Meta description
        meta = soup.find("meta", attrs={"name": "description"})
        if meta:
            page.meta_description = meta.get("content", "").strip()
            page.meta_description_length = len(page.meta_description)

        # Canonical
        canon = soup.find("link", attrs={"rel": "canonical"})
        if canon:
            page.canonical = canon.get("href", "")

        # Headings
        page.h1 = [h.get_text(strip=True) for h in soup.find_all("h1")]
        page.h2 = [h.get_text(strip=True) for h in soup.find_all("h2")]

        # Open Graph
        for prop, attr in [("og:title", "og_title"), ("og:description", "og_description"),
                           ("og:image", "og_image"), ("og:url", "og_url")]:
            tag = soup.find("meta", attrs={"property": prop})
            if tag:
                setattr(page, attr, tag.get("content", ""))

        # Twitter
        for name_attr, attr in [("twitter:title", "twitter_title"), ("twitter:description", "twitter_description"),
                                ("twitter:card", "twitter_card")]:
            tag = soup.find("meta", attrs={"name": name_attr})
            if tag:
                setattr(page, attr, tag.get("content", ""))

        # Schema
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                schema = json.loads(script.string)
                page.schemas.append(schema)
                schema_type = schema.get("@type", "Unknown")
                page.schema_types.append(schema_type)
                if schema_type == "FAQPage":
                    page.has_faq = True
                if schema_type == "BreadcrumbList":
                    page.has_breadcrumb = True
            except (json.JSONDecodeError, TypeError):
                pass

        # Links
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith(("http://", "https://")):
                if self._domain in href or "freemindconsult.com" in href:
                    page.internal_links.append(href)
                else:
                    page.external_links.append(href)
            elif href.startswith(("/", ".")) and not href.startswith("#"):
                page.internal_links.append(href)

        # Images
        for img in soup.find_all("img"):
            page.images.append({
                "src": img.get("src", ""),
                "alt": img.get("alt", ""),
                "width": img.get("width", ""),
                "height": img.get("height", ""),
                "has_alt": bool(img.get("alt", "").strip()),
            })

        # Word count
        body = soup.find("body")
        if body:
            page.word_count = len(body.get_text(separator=" ", strip=True).split())

        # Hreflang
        for link in soup.find_all("link", attrs={"rel": "alternate", "hreflang": True}):
            page.hreflang.append(link.get("hreflang", ""))

        # Robots
        robots = soup.find("meta", attrs={"name": "robots"})
        if robots:
            page.robots = robots.get("content", "")

        # Language
        html_tag = soup.find("html")
        if html_tag:
            page.lang = html_tag.get("lang", "")

        # Tracking
        page.has_ga4 = "G-EWH4E2G82R" in raw
        page.has_meta_pixel = "2618965074964872" in raw

        return page
