"""
Read and write page metadata — title, meta description,
Open Graph, Twitter Card tags.
"""

import logging
import re
from pathlib import Path

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class MetadataManager:
    @staticmethod
    def read_metadata(html_path: Path) -> dict:
        soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
        title_tag = soup.find("title")
        meta_desc = soup.find("meta", attrs={"name": "description"})
        return {
            "title": title_tag.get_text(strip=True) if title_tag else "",
            "meta_description": meta_desc.get("content", "") if meta_desc else "",
            "og_title": (soup.find("meta", property="og:title") or {}).get("content", ""),
            "og_description": (soup.find("meta", property="og:description") or {}).get("content", ""),
            "og_url": (soup.find("meta", property="og:url") or {}).get("content", ""),
            "og_image": (soup.find("meta", property="og:image") or {}).get("content", ""),
            "twitter_title": (soup.find("meta", attrs={"name": "twitter:title"}) or {}).get("content", ""),
            "twitter_description": (soup.find("meta", attrs={"name": "twitter:description"}) or {}).get("content", ""),
        }

    @staticmethod
    def update_title(html: str, new_title: str) -> str:
        return re.sub(r"<title>.*?</title>", f"<title>{new_title}</title>", html, count=1, flags=re.DOTALL)

    @staticmethod
    def update_meta_description(html: str, new_desc: str) -> str:
        if re.search(r'<meta\s+name="description"', html):
            return re.sub(
                r'(<meta\s+name="description"\s+content=")[^"]*(")',
                rf'\g<1>{new_desc}\2', html, count=1,
            )
        return html.replace("</title>", f'</title>\n  <meta name="description" content="{new_desc}">')

    @staticmethod
    def update_og_title(html: str, new_title: str) -> str:
        if re.search(r'<meta\s+property="og:title"', html):
            return re.sub(
                r'(<meta\s+property="og:title"\s+content=")[^"]*(")',
                rf'\g<1>{new_title}\2', html, count=1,
            )
        return html

    @staticmethod
    def update_og_description(html: str, new_desc: str) -> str:
        if re.search(r'<meta\s+property="og:description"', html):
            return re.sub(
                r'(<meta\s+property="og:description"\s+content=")[^"]*(")',
                rf'\g<1>{new_desc}\2', html, count=1,
            )
        return html

    @staticmethod
    def update_twitter_title(html: str, new_title: str) -> str:
        if re.search(r'<meta\s+name="twitter:title"', html):
            return re.sub(
                r'(<meta\s+name="twitter:title"\s+content=")[^"]*(")',
                rf'\g<1>{new_title}\2', html, count=1,
            )
        return html

    @staticmethod
    def update_twitter_description(html: str, new_desc: str) -> str:
        if re.search(r'<meta\s+name="twitter:description"', html):
            return re.sub(
                r'(<meta\s+name="twitter:description"\s+content=")[^"]*(")',
                rf'\g<1>{new_desc}\2', html, count=1,
            )
        return html

    @classmethod
    def update_all_metadata(cls, html: str, title: str = "", description: str = "") -> str:
        if title:
            html = cls.update_title(html, title)
            html = cls.update_og_title(html, title)
            html = cls.update_twitter_title(html, title)
        if description:
            html = cls.update_meta_description(html, description)
            html = cls.update_og_description(html, description)
            html = cls.update_twitter_description(html, description)
        return html
