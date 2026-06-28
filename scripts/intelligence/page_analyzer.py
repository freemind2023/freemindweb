"""
Page-level SEO analysis combining GA4 analytics, GSC search data,
and on-page HTML inspection.

Detects pages losing/gaining traffic, poor engagement, missing
content elements, orphan pages, and duplicate intent.
"""

import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class PageIssue:
    url: str
    issue_type: str
    severity: str  # critical, high, medium, low
    detail: str
    evidence: str
    recommendation: str
    estimated_time: str = "15 min"
    seo_impact: str = "medium"
    business_impact: str = "medium"

    def to_dict(self) -> dict:
        return asdict(self)


class PageAnalyzer:
    def __init__(self, data_dir: Path, website_root: str, settings: dict):
        self._data_dir = data_dir
        self._website_root = Path(website_root)
        self._settings = settings
        self._min_word_count = settings.get("analysis", {}).get("min_content_word_count", 800)

    def analyze_combined(self, combined_df: pd.DataFrame) -> list[PageIssue]:
        """Analyze combined_pages.csv for performance issues."""
        issues = []
        if combined_df.empty:
            return issues

        issues.extend(self._detect_losing_clicks(combined_df))
        issues.extend(self._detect_no_conversions(combined_df))
        issues.extend(self._detect_poor_engagement(combined_df))
        issues.extend(self._detect_orphan_pages(combined_df))

        logger.info("Page analysis found %d issues", len(issues))
        return issues

    def analyze_html(self) -> list[PageIssue]:
        """Scan website HTML files for technical SEO issues."""
        issues = []
        if not self._website_root.exists():
            logger.warning("Website root not found: %s", self._website_root)
            return issues

        html_files = list(self._website_root.rglob("*.html"))
        logger.info("Scanning %d HTML files for technical issues", len(html_files))

        titles_seen = {}
        for html_path in html_files:
            rel_path = "/" + str(html_path.relative_to(self._website_root)).replace("\\", "/")
            try:
                content = html_path.read_text(encoding="utf-8", errors="ignore")
                soup = BeautifulSoup(content, "html.parser")
            except Exception as e:
                logger.warning("Failed to parse %s: %s", rel_path, e)
                continue

            issues.extend(self._check_title(soup, rel_path, titles_seen))
            issues.extend(self._check_meta_description(soup, rel_path))
            issues.extend(self._check_h1(soup, rel_path))
            issues.extend(self._check_canonical(soup, rel_path))
            issues.extend(self._check_alt_text(soup, rel_path))
            issues.extend(self._check_schema(soup, rel_path))
            issues.extend(self._check_content_length(soup, rel_path))

        logger.info("HTML scan found %d technical issues across %d files", len(issues), len(html_files))
        return issues

    # --- Performance issues from combined data ---

    def _detect_losing_clicks(self, df: pd.DataFrame) -> list[PageIssue]:
        issues = []
        low_click_pages = df[(df["impressions"] > 50) & (df["clicks"] == 0)]
        for _, r in low_click_pages.iterrows():
            issues.append(PageIssue(
                url=r["url"],
                issue_type="zero_clicks_high_impressions",
                severity="high",
                detail=f"{int(r['impressions'])} impressions but 0 clicks",
                evidence=f"GSC: {int(r['impressions'])} impressions, 0 clicks, avg position {r['avg_position']:.1f}",
                recommendation="Rewrite title tag and meta description to improve CTR",
                seo_impact="high",
                business_impact="high",
                estimated_time="20 min",
            ))
        return issues

    def _detect_no_conversions(self, df: pd.DataFrame) -> list[PageIssue]:
        issues = []
        no_conv = df[(df["sessions"] > 5) & (df["conversions"] == 0)]
        for _, r in no_conv.iterrows():
            issues.append(PageIssue(
                url=r["url"],
                issue_type="no_conversions",
                severity="medium",
                detail=f"{int(r['sessions'])} sessions but 0 conversions",
                evidence=f"GA4: {int(r['sessions'])} sessions, {int(r['total_users'])} users, 0 conversions",
                recommendation="Add clear CTA, contact form, or lead capture element",
                seo_impact="low",
                business_impact="high",
                estimated_time="30 min",
            ))
        return issues

    def _detect_poor_engagement(self, df: pd.DataFrame) -> list[PageIssue]:
        issues = []
        poor = df[(df["sessions"] > 3) & (df["bounce_rate"] > 0.7)]
        for _, r in poor.iterrows():
            issues.append(PageIssue(
                url=r["url"],
                issue_type="poor_engagement",
                severity="medium",
                detail=f"Bounce rate {r['bounce_rate']:.0%}, avg duration {r['avg_session_duration']:.0f}s",
                evidence=f"GA4: {r['bounce_rate']:.0%} bounce rate across {int(r['sessions'])} sessions",
                recommendation="Improve content quality, add internal links, improve page speed",
                seo_impact="medium",
                business_impact="medium",
                estimated_time="45 min",
            ))
        return issues

    def _detect_orphan_pages(self, df: pd.DataFrame) -> list[PageIssue]:
        issues = []
        orphan = df[df["landing_page_status"] == "inactive"]
        for _, r in orphan.iterrows():
            issues.append(PageIssue(
                url=r["url"],
                issue_type="orphan_page",
                severity="low",
                detail="No sessions and no search impressions",
                evidence="GA4: 0 sessions. GSC: 0 impressions.",
                recommendation="Add internal links pointing to this page or consider removing",
                seo_impact="low",
                business_impact="low",
                estimated_time="10 min",
            ))
        return issues

    # --- HTML technical checks ---

    def _check_title(self, soup, url: str, titles_seen: dict) -> list[PageIssue]:
        issues = []
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        if not title:
            issues.append(PageIssue(url=url, issue_type="missing_title", severity="critical",
                detail="Page has no <title> tag", evidence="HTML scan: no <title> element found",
                recommendation="Add a unique, keyword-rich title under 60 characters",
                seo_impact="critical", business_impact="high", estimated_time="5 min"))
        elif len(title) > 60:
            issues.append(PageIssue(url=url, issue_type="long_title", severity="medium",
                detail=f"Title is {len(title)} chars (max 60): '{title[:65]}...'",
                evidence=f"HTML scan: title length {len(title)}",
                recommendation="Shorten title to under 60 characters",
                seo_impact="medium", business_impact="low", estimated_time="5 min"))

        if title:
            if title in titles_seen:
                issues.append(PageIssue(url=url, issue_type="duplicate_title", severity="high",
                    detail=f"Same title as {titles_seen[title]}",
                    evidence=f"Duplicate: '{title[:60]}'",
                    recommendation="Write a unique title for this page",
                    seo_impact="high", business_impact="medium", estimated_time="5 min"))
            titles_seen[title] = url
        return issues

    def _check_meta_description(self, soup, url: str) -> list[PageIssue]:
        issues = []
        meta = soup.find("meta", attrs={"name": "description"})
        desc = meta.get("content", "").strip() if meta else ""

        if not desc:
            issues.append(PageIssue(url=url, issue_type="missing_meta_description", severity="high",
                detail="No meta description found",
                evidence="HTML scan: no <meta name='description'> tag",
                recommendation="Add a compelling meta description under 155 characters with a CTA",
                seo_impact="high", business_impact="medium", estimated_time="10 min"))
        elif len(desc) > 155:
            issues.append(PageIssue(url=url, issue_type="long_meta_description", severity="low",
                detail=f"Meta description is {len(desc)} chars (max 155)",
                evidence=f"HTML scan: description length {len(desc)}",
                recommendation="Shorten meta description to under 155 characters",
                seo_impact="low", business_impact="low", estimated_time="5 min"))
        return issues

    def _check_h1(self, soup, url: str) -> list[PageIssue]:
        issues = []
        h1s = soup.find_all("h1")
        if not h1s:
            issues.append(PageIssue(url=url, issue_type="missing_h1", severity="high",
                detail="No H1 heading found", evidence="HTML scan: 0 <h1> elements",
                recommendation="Add a single H1 heading containing the primary keyword",
                seo_impact="high", business_impact="medium", estimated_time="5 min"))
        elif len(h1s) > 1:
            issues.append(PageIssue(url=url, issue_type="multiple_h1", severity="medium",
                detail=f"Found {len(h1s)} H1 tags — should be 1",
                evidence=f"HTML scan: {len(h1s)} <h1> elements",
                recommendation="Keep a single H1 per page",
                seo_impact="medium", business_impact="low", estimated_time="10 min"))
        return issues

    def _check_canonical(self, soup, url: str) -> list[PageIssue]:
        issues = []
        canonical = soup.find("link", attrs={"rel": "canonical"})
        if not canonical:
            issues.append(PageIssue(url=url, issue_type="missing_canonical", severity="high",
                detail="No canonical tag found", evidence="HTML scan: no <link rel='canonical'>",
                recommendation="Add a self-referencing canonical tag",
                seo_impact="high", business_impact="medium", estimated_time="5 min"))
        return issues

    def _check_alt_text(self, soup, url: str) -> list[PageIssue]:
        issues = []
        imgs = soup.find_all("img")
        missing_alt = [img for img in imgs if not img.get("alt", "").strip()]
        if missing_alt:
            issues.append(PageIssue(url=url, issue_type="missing_alt_text", severity="medium",
                detail=f"{len(missing_alt)} of {len(imgs)} images missing alt text",
                evidence=f"HTML scan: {len(missing_alt)} <img> tags without alt attribute",
                recommendation="Add descriptive alt text with keywords to all images",
                seo_impact="medium", business_impact="low", estimated_time="10 min"))
        return issues

    def _check_schema(self, soup, url: str) -> list[PageIssue]:
        issues = []
        scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
        if not scripts:
            issues.append(PageIssue(url=url, issue_type="missing_schema", severity="medium",
                detail="No JSON-LD structured data found",
                evidence="HTML scan: 0 <script type='application/ld+json'> elements",
                recommendation="Add appropriate schema markup (Service, Article, LocalBusiness, FAQ)",
                seo_impact="medium", business_impact="medium", estimated_time="20 min"))
        return issues

    def _check_content_length(self, soup, url: str) -> list[PageIssue]:
        issues = []
        body = soup.find("body")
        if body:
            text = body.get_text(separator=" ", strip=True)
            word_count = len(text.split())
            if word_count < self._min_word_count and not any(
                skip in url for skip in ["/privacy", "/terms", "/disclaimer"]
            ):
                issues.append(PageIssue(url=url, issue_type="thin_content", severity="medium",
                    detail=f"Only {word_count} words (minimum {self._min_word_count})",
                    evidence=f"HTML scan: {word_count} words in body content",
                    recommendation=f"Expand content to at least {self._min_word_count} words",
                    seo_impact="medium", business_impact="medium", estimated_time="60 min"))
        return issues
