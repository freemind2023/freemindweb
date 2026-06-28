"""
Manage image alt text, dimensions, and file references.
Does NOT process image files — only modifies HTML references.
"""

import logging
import re

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ImageOptimizer:
    @staticmethod
    def fix_missing_alt(html: str, default_prefix: str = "Free Mind Consultancy") -> str:
        soup = BeautifulSoup(html, "html.parser")
        fixed = 0
        for img in soup.find_all("img"):
            if not img.get("alt", "").strip():
                src = img.get("src", "")
                name = src.split("/")[-1].rsplit(".", 1)[0].replace("-", " ").replace("_", " ")
                img["alt"] = f"{default_prefix} — {name}" if name else default_prefix
                fixed += 1
        if fixed:
            logger.info("Fixed alt text on %d images", fixed)
        return str(soup)

    @staticmethod
    def add_dimensions(html: str, width: str, height: str) -> str:
        """Add width/height to images missing them (prevents CLS)."""
        soup = BeautifulSoup(html, "html.parser")
        for img in soup.find_all("img"):
            if not img.get("width") and not img.get("height"):
                img["width"] = width
                img["height"] = height
                img["loading"] = "lazy"
        return str(soup)

    @staticmethod
    def audit_images(html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for img in soup.find_all("img"):
            results.append({
                "src": img.get("src", ""),
                "alt": img.get("alt", ""),
                "has_alt": bool(img.get("alt", "").strip()),
                "has_dimensions": bool(img.get("width") or img.get("height")),
                "has_lazy": img.get("loading") == "lazy",
            })
        return results
