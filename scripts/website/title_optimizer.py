"""
Optimize title tags using keyword data and SEO best practices.
"""

import logging

from .page_mapper import PageProfile
from .metadata_manager import MetadataManager

logger = logging.getLogger(__name__)

MAX_TITLE_LENGTH = 60
BRAND_SUFFIX = " | Free Mind"


class TitleOptimizer:
    @staticmethod
    def suggest_title(profile: PageProfile) -> str | None:
        """Suggest an optimized title or return None if current is fine."""
        current = profile.title
        keyword = profile.primary_keyword

        if not current:
            if keyword:
                return f"{keyword.title()}{BRAND_SUFFIX}"
            return None

        if len(current) <= MAX_TITLE_LENGTH and keyword and keyword.lower() in current.lower():
            return None  # Already good

        if len(current) > MAX_TITLE_LENGTH:
            return TitleOptimizer._shorten(current, keyword)

        if keyword and keyword.lower() not in current.lower():
            return TitleOptimizer._inject_keyword(current, keyword)

        return None

    @staticmethod
    def _shorten(title: str, keyword: str) -> str:
        # Remove brand suffix if present and too long
        for suffix in [" — Free Mind Consultancy India", " | Free Mind Consultancy",
                       " — Free Mind Consultancy", " | Free Mind"]:
            if title.endswith(suffix):
                core = title[: -len(suffix)]
                candidate = core.strip() + BRAND_SUFFIX
                if len(candidate) <= MAX_TITLE_LENGTH:
                    return candidate

        # Truncate intelligently at word boundary
        target = MAX_TITLE_LENGTH - len(BRAND_SUFFIX)
        words = title.split()
        shortened = ""
        for w in words:
            test = f"{shortened} {w}".strip() if shortened else w
            if len(test) <= target:
                shortened = test
            else:
                break
        return shortened + BRAND_SUFFIX if shortened else title[:target] + BRAND_SUFFIX

    @staticmethod
    def _inject_keyword(title: str, keyword: str) -> str:
        # Put keyword at front if possible
        candidate = f"{keyword.title()} — {title}"
        if len(candidate) <= MAX_TITLE_LENGTH:
            return candidate
        # Replace brand suffix approach
        candidate = f"{keyword.title()}{BRAND_SUFFIX}"
        if len(candidate) <= MAX_TITLE_LENGTH:
            return candidate
        return None

    @staticmethod
    def apply_title(html: str, new_title: str) -> str:
        return MetadataManager.update_all_metadata(html, title=new_title)
