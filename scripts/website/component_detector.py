"""
Detect reusable components across website pages — shared headers,
footers, navigation, CTAs, tracking scripts.
"""

import logging
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path

from bs4 import BeautifulSoup

from .crawler import PageData

logger = logging.getLogger(__name__)


@dataclass
class Component:
    name: str
    html_tag: str
    found_in: list[str] = field(default_factory=list)
    count: int = 0
    is_consistent: bool = True
    variants: int = 1

    def to_dict(self) -> dict:
        return asdict(self)


class ComponentDetector:
    def detect(self, pages: list[PageData]) -> list[Component]:
        components = []
        components.append(self._detect_nav(pages))
        components.append(self._detect_footer(pages))
        components.append(self._detect_tracking(pages, "ga4", "G-EWH4E2G82R"))
        components.append(self._detect_tracking(pages, "meta_pixel", "2618965074964872"))
        components.append(self._detect_cta(pages))
        logger.info("Detected %d component types", len(components))
        return components

    def _detect_nav(self, pages: list[PageData]) -> Component:
        nav_hashes = Counter()
        found_in = []
        for p in pages:
            soup = BeautifulSoup(Path(p.file_path).read_text(encoding="utf-8", errors="ignore"), "html.parser")
            nav = soup.find("nav")
            if nav:
                found_in.append(p.relative_url)
                links = tuple(a.get("href", "") for a in nav.find_all("a", href=True))
                nav_hashes[links] += 1
        return Component(
            name="navigation", html_tag="nav",
            found_in=found_in, count=len(found_in),
            is_consistent=len(nav_hashes) <= 2, variants=len(nav_hashes),
        )

    def _detect_footer(self, pages: list[PageData]) -> Component:
        found_in = []
        variants = Counter()
        for p in pages:
            soup = BeautifulSoup(Path(p.file_path).read_text(encoding="utf-8", errors="ignore"), "html.parser")
            footer = soup.find("footer")
            if footer:
                found_in.append(p.relative_url)
                text = footer.get_text(strip=True)[:100]
                variants[text] += 1
        return Component(
            name="footer", html_tag="footer",
            found_in=found_in, count=len(found_in),
            is_consistent=len(variants) <= 2, variants=len(variants),
        )

    def _detect_tracking(self, pages: list[PageData], name: str, marker: str) -> Component:
        found_in = [p.relative_url for p in pages if marker in Path(p.file_path).read_text(encoding="utf-8", errors="ignore")]
        return Component(
            name=name, html_tag="script",
            found_in=found_in, count=len(found_in),
            is_consistent=len(found_in) == len(pages), variants=1,
        )

    def _detect_cta(self, pages: list[PageData]) -> Component:
        found_in = []
        for p in pages:
            soup = BeautifulSoup(Path(p.file_path).read_text(encoding="utf-8", errors="ignore"), "html.parser")
            ctas = soup.find_all("a", class_=lambda c: c and "btn" in c)
            if ctas:
                found_in.append(p.relative_url)
        return Component(
            name="cta_buttons", html_tag="a.btn",
            found_in=found_in, count=len(found_in),
            is_consistent=True, variants=1,
        )
