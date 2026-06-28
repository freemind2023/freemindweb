"""
Unified data model merging GA4 and Search Console data per page.

This is the primary schema for the combined_pages.csv output that feeds
the AI analysis engine.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


COMBINED_COLUMNS = [
    "url",
    "clicks",
    "impressions",
    "ctr",
    "avg_position",
    "sessions",
    "total_users",
    "new_users",
    "bounce_rate",
    "avg_session_duration",
    "screen_page_views",
    "engagement_rate",
    "conversions",
    "landing_page_status",
    "last_updated",
]


@dataclass
class CombinedPageRow:
    url: str
    clicks: int = 0
    impressions: int = 0
    ctr: float = 0.0
    avg_position: float = 0.0
    sessions: int = 0
    total_users: int = 0
    new_users: int = 0
    bounce_rate: float = 0.0
    avg_session_duration: float = 0.0
    screen_page_views: int = 0
    engagement_rate: float = 0.0
    conversions: int = 0
    landing_page_status: str = "unknown"
    last_updated: str = ""

    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()
        self._classify_status()

    def _classify_status(self):
        if self.sessions > 0 and self.impressions > 0:
            self.landing_page_status = "active"
        elif self.impressions > 0 and self.sessions == 0:
            self.landing_page_status = "indexed_no_traffic"
        elif self.sessions > 0 and self.impressions == 0:
            self.landing_page_status = "direct_only"
        else:
            self.landing_page_status = "inactive"

    def validate(self) -> list[str]:
        errors = []
        if not self.url:
            errors.append("url is empty")
        if self.clicks < 0:
            errors.append(f"clicks is negative: {self.clicks}")
        if self.impressions < 0:
            errors.append(f"impressions is negative: {self.impressions}")
        if self.sessions < 0:
            errors.append(f"sessions is negative: {self.sessions}")
        if not 0.0 <= self.ctr <= 1.0:
            errors.append(f"ctr out of range [0,1]: {self.ctr}")
        if not 0.0 <= self.bounce_rate <= 1.0:
            errors.append(f"bounce_rate out of range [0,1]: {self.bounce_rate}")
        return errors

    def to_dict(self) -> dict:
        return asdict(self)

    def missing_fields(self) -> list[str]:
        """Return field names that have zero/empty values suggesting missing data."""
        missing = []
        if self.clicks == 0 and self.impressions == 0:
            missing.append("search_data")
        if self.sessions == 0 and self.total_users == 0:
            missing.append("analytics_data")
        return missing


@dataclass
class CombinedSnapshot:
    start_date: str
    end_date: str
    created_at: str = ""
    pages: list[CombinedPageRow] = field(default_factory=list)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def validate(self) -> list[str]:
        errors = []
        if not self.start_date:
            errors.append("start_date is empty")
        if not self.end_date:
            errors.append("end_date is empty")
        if not self.pages:
            errors.append("no pages in snapshot")
        for i, p in enumerate(self.pages):
            for err in p.validate():
                errors.append(f"pages[{i}]: {err}")
        return errors

    def missing_data_report(self) -> dict:
        """Summarize which pages are missing GA4 or GSC data."""
        missing_search = []
        missing_analytics = []
        for p in self.pages:
            gaps = p.missing_fields()
            if "search_data" in gaps:
                missing_search.append(p.url)
            if "analytics_data" in gaps:
                missing_analytics.append(p.url)
        return {
            "total_pages": len(self.pages),
            "pages_missing_search_data": len(missing_search),
            "pages_missing_analytics_data": len(missing_analytics),
            "missing_search_urls": missing_search,
            "missing_analytics_urls": missing_analytics,
        }

    def to_metadata(self) -> dict:
        errors = self.validate()
        missing = self.missing_data_report()
        active = sum(1 for p in self.pages if p.landing_page_status == "active")
        return {
            "source": "combined",
            "start_date": self.start_date,
            "end_date": self.end_date,
            "created_at": self.created_at,
            "total_pages": len(self.pages),
            "active_pages": active,
            "total_sessions": sum(p.sessions for p in self.pages),
            "total_clicks": sum(p.clicks for p in self.pages),
            "total_impressions": sum(p.impressions for p in self.pages),
            "missing_data": missing,
            "validation_errors": errors,
        }
