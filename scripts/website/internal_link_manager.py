"""
Analyze and modify internal links across the website.
"""

import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .crawler import PageData

logger = logging.getLogger(__name__)


@dataclass
class LinkEdge:
    source: str
    target: str
    anchor_text: str
    is_nav: bool = False


@dataclass
class LinkReport:
    total_links: int = 0
    orphan_pages: list[str] = field(default_factory=list)
    weak_pages: list[str] = field(default_factory=list)
    hub_pages: list[str] = field(default_factory=list)
    max_depth: int = 0
    edges: list[LinkEdge] = field(default_factory=list)


class InternalLinkManager:
    def __init__(self, pages: list[PageData]):
        self._pages = pages
        self._all_urls = {p.relative_url for p in pages}

    def analyze(self) -> LinkReport:
        edges = []
        incoming: dict[str, int] = {p.relative_url: 0 for p in self._pages}

        for page in self._pages:
            soup = BeautifulSoup(
                Path(page.file_path).read_text(encoding="utf-8", errors="ignore"),
                "html.parser",
            )
            nav = soup.find("nav")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                target = self._resolve_link(href, page.relative_url)
                if target and target in self._all_urls and target != page.relative_url:
                    is_nav = nav is not None and a in nav.descendants
                    edges.append(LinkEdge(
                        source=page.relative_url,
                        target=target,
                        anchor_text=a.get_text(strip=True)[:80],
                        is_nav=is_nav,
                    ))
                    incoming[target] = incoming.get(target, 0) + 1

        content_edges = [e for e in edges if not e.is_nav]
        content_incoming: dict[str, int] = {p.relative_url: 0 for p in self._pages}
        for e in content_edges:
            content_incoming[e.target] = content_incoming.get(e.target, 0) + 1

        orphans = [url for url, count in content_incoming.items() if count == 0]
        weak = [url for url, count in content_incoming.items() if 0 < count <= 1]
        hubs = sorted(content_incoming.items(), key=lambda x: x[1], reverse=True)[:5]

        report = LinkReport(
            total_links=len(edges),
            orphan_pages=orphans,
            weak_pages=weak,
            hub_pages=[h[0] for h in hubs],
            edges=edges,
        )
        logger.info(
            "Link analysis: %d links, %d orphans, %d weak pages",
            report.total_links, len(report.orphan_pages), len(report.weak_pages),
        )
        return report

    def add_link(self, html: str, anchor_text: str, href: str, after_tag: str = "p") -> str:
        """Insert an internal link after the first occurrence of a given tag."""
        soup = BeautifulSoup(html, "html.parser")
        target = soup.find(after_tag)
        if target:
            link_html = f' <a href="{href}">{anchor_text}</a>'
            target.append(BeautifulSoup(link_html, "html.parser"))
        return str(soup)

    def _resolve_link(self, href: str, source_url: str) -> str | None:
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            return None
        if href.startswith("http"):
            parsed = urlparse(href)
            if "freemindconsult.com" in parsed.netloc:
                return parsed.path.rstrip("/") or "/"
            return None
        if href.startswith("/"):
            return href.rstrip("/") or "/"
        # Relative path
        from pathlib import PurePosixPath
        base = PurePosixPath(source_url).parent
        resolved = str(base / href).replace("\\", "/")
        return resolved.rstrip("/") or "/"
