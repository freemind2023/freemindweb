"""
Maps URLs to files and enriches pages with SEO intelligence data.

Joins crawler output with combined_pages.csv and query data to produce
a complete per-page profile with file path, URL, rankings, traffic,
CTR, technical score, issues, and suggested fixes.
"""

import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from .crawler import PageData

logger = logging.getLogger(__name__)


@dataclass
class PageProfile:
    """Complete profile merging website structure + SEO intelligence."""
    url: str
    relative_url: str
    file_path: str
    # From crawler
    title: str = ""
    title_length: int = 0
    meta_description: str = ""
    meta_description_length: int = 0
    canonical: str = ""
    h1_count: int = 0
    h1_text: str = ""
    word_count: int = 0
    schema_types: list[str] = field(default_factory=list)
    has_faq: bool = False
    has_breadcrumb: bool = False
    og_title: str = ""
    internal_link_count: int = 0
    external_link_count: int = 0
    image_count: int = 0
    images_missing_alt: int = 0
    # From SEO intelligence
    primary_keyword: str = ""
    secondary_keywords: list[str] = field(default_factory=list)
    clicks: int = 0
    impressions: int = 0
    ctr: float = 0.0
    avg_position: float = 0.0
    sessions: int = 0
    total_users: int = 0
    bounce_rate: float = 0.0
    conversions: int = 0
    landing_page_status: str = "unknown"
    # Computed
    technical_score: float = 0.0
    priority_score: float = 0.0
    issues: list[str] = field(default_factory=list)
    suggested_fixes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class PageMapper:
    def __init__(self, domain: str = "https://www.freemindconsult.com"):
        self._domain = domain.rstrip("/")
        self._profiles: list[PageProfile] = []

    @staticmethod
    def normalize_url(url: str) -> str:
        if url.startswith("http"):
            return urlparse(url).path.rstrip("/") or "/"
        return url.rstrip("/") or "/"

    def build_profiles(
        self,
        pages: list[PageData],
        combined_df: pd.DataFrame | None = None,
        queries_df: pd.DataFrame | None = None,
    ) -> list[PageProfile]:
        """Merge crawler pages with SEO data into PageProfiles."""
        self._profiles = []

        combined_lookup = {}
        if combined_df is not None and not combined_df.empty:
            for _, row in combined_df.iterrows():
                key = self.normalize_url(str(row.get("url", "")))
                combined_lookup[key] = row

        query_lookup = {}
        if queries_df is not None and not queries_df.empty:
            for _, row in queries_df.iterrows():
                page_key = self.normalize_url(str(row.get("page", "")))
                query_lookup.setdefault(page_key, []).append(row)

        for page in pages:
            norm_url = self.normalize_url(page.relative_url)
            profile = PageProfile(
                url=page.url,
                relative_url=page.relative_url,
                file_path=page.file_path,
                title=page.title,
                title_length=page.title_length,
                meta_description=page.meta_description,
                meta_description_length=page.meta_description_length,
                canonical=page.canonical,
                h1_count=len(page.h1),
                h1_text=page.h1[0] if page.h1 else "",
                word_count=page.word_count,
                schema_types=page.schema_types,
                has_faq=page.has_faq,
                has_breadcrumb=page.has_breadcrumb,
                og_title=page.og_title,
                internal_link_count=len(page.internal_links),
                external_link_count=len(page.external_links),
                image_count=len(page.images),
                images_missing_alt=sum(1 for img in page.images if not img.get("has_alt")),
            )

            # Enrich with SEO data
            seo = combined_lookup.get(norm_url)
            if seo is not None:
                profile.clicks = int(seo.get("clicks", 0) or 0)
                profile.impressions = int(seo.get("impressions", 0) or 0)
                profile.ctr = float(seo.get("ctr", 0) or 0)
                profile.avg_position = float(seo.get("avg_position", 0) or 0)
                profile.sessions = int(seo.get("sessions", 0) or 0)
                profile.total_users = int(seo.get("total_users", 0) or 0)
                profile.bounce_rate = float(seo.get("bounce_rate", 0) or 0)
                profile.conversions = int(seo.get("conversions", 0) or 0)
                profile.landing_page_status = str(seo.get("landing_page_status", "unknown"))

            # Map top queries as keywords
            page_queries = query_lookup.get(norm_url, [])
            if page_queries:
                sorted_q = sorted(page_queries, key=lambda r: int(r.get("impressions", 0)), reverse=True)
                profile.primary_keyword = str(sorted_q[0].get("query", ""))
                profile.secondary_keywords = [str(r.get("query", "")) for r in sorted_q[1:6]]

            # Compute technical score and issues
            self._score_page(profile)
            self._profiles.append(profile)

        logger.info("Built %d page profiles", len(self._profiles))
        return self._profiles

    def get_profiles(self) -> list[PageProfile]:
        return self._profiles

    def get_profile_by_url(self, url: str) -> PageProfile | None:
        norm = self.normalize_url(url)
        for p in self._profiles:
            if self.normalize_url(p.relative_url) == norm:
                return p
        return None

    def _score_page(self, p: PageProfile):
        score = 100.0
        issues = []
        fixes = []

        if not p.title:
            score -= 20
            issues.append("missing_title")
            fixes.append("Add <title> with primary keyword under 60 chars")
        elif p.title_length > 60:
            score -= 10
            issues.append("title_too_long")
            fixes.append(f"Shorten title from {p.title_length} to under 60 chars")

        if not p.meta_description:
            score -= 15
            issues.append("missing_meta_description")
            fixes.append("Add meta description under 155 chars with CTA")
        elif p.meta_description_length > 155:
            score -= 5
            issues.append("meta_description_too_long")
            fixes.append(f"Shorten meta description from {p.meta_description_length} to under 155 chars")

        if p.h1_count == 0:
            score -= 15
            issues.append("missing_h1")
            fixes.append("Add single H1 with primary keyword")
        elif p.h1_count > 1:
            score -= 5
            issues.append("multiple_h1")
            fixes.append(f"Reduce from {p.h1_count} H1 tags to 1")

        if not p.canonical:
            score -= 10
            issues.append("missing_canonical")
            fixes.append("Add self-referencing canonical tag")

        if not p.schema_types:
            score -= 10
            issues.append("missing_schema")
            fixes.append("Add JSON-LD schema (Service/Article/FAQPage)")

        if p.images_missing_alt > 0:
            score -= min(10, p.images_missing_alt * 2)
            issues.append("missing_alt_text")
            fixes.append(f"Add alt text to {p.images_missing_alt} images")

        if p.word_count < 300:
            score -= 10
            issues.append("thin_content")
            fixes.append(f"Expand content from {p.word_count} to 800+ words")

        if p.internal_link_count < 3:
            score -= 5
            issues.append("few_internal_links")
            fixes.append(f"Add internal links (currently {p.internal_link_count})")

        if not p.og_title:
            score -= 5
            issues.append("missing_og_tags")
            fixes.append("Add Open Graph meta tags")

        p.technical_score = max(0, score)
        p.issues = issues
        p.suggested_fixes = fixes

        # Priority score from SEO data
        p.priority_score = (
            p.impressions * 0.3
            + p.sessions * 0.3
            + (100 - p.technical_score) * 0.2
            + len(issues) * 5
        )
