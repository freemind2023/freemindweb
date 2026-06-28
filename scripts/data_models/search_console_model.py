"""
Data models for Google Search Console snapshots.

Defines the schema for search query performance, per-page search data,
and the overall snapshot container. Handles validation and serialization.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class SearchQueryRow:
    query: str
    page: str
    clicks: int = 0
    impressions: int = 0
    ctr: float = 0.0
    position: float = 0.0
    country: str = ""
    device: str = ""

    def validate(self) -> list[str]:
        errors = []
        if not self.query:
            errors.append("query is empty")
        if not self.page:
            errors.append("page is empty")
        if self.clicks < 0:
            errors.append(f"clicks is negative: {self.clicks}")
        if self.impressions < 0:
            errors.append(f"impressions is negative: {self.impressions}")
        if not 0.0 <= self.ctr <= 1.0:
            errors.append(f"ctr out of range [0,1]: {self.ctr}")
        if self.position < 0:
            errors.append(f"position is negative: {self.position}")
        return errors

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SearchPageRow:
    """Aggregated search metrics per page URL."""
    page: str
    clicks: int = 0
    impressions: int = 0
    ctr: float = 0.0
    avg_position: float = 0.0
    query_count: int = 0

    def validate(self) -> list[str]:
        errors = []
        if not self.page:
            errors.append("page is empty")
        if self.clicks < 0:
            errors.append(f"clicks is negative: {self.clicks}")
        if self.impressions < 0:
            errors.append(f"impressions is negative: {self.impressions}")
        return errors

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SearchConsoleSnapshot:
    site_url: str
    start_date: str
    end_date: str
    fetched_at: str = ""
    queries: list[SearchQueryRow] = field(default_factory=list)
    pages: list[SearchPageRow] = field(default_factory=list)
    total_clicks: int = 0
    total_impressions: int = 0
    row_count: int = 0

    def __post_init__(self):
        if not self.fetched_at:
            self.fetched_at = datetime.now().isoformat()

    def validate(self) -> list[str]:
        errors = []
        if not self.site_url:
            errors.append("site_url is empty")
        if not self.start_date:
            errors.append("start_date is empty")
        if not self.end_date:
            errors.append("end_date is empty")
        for i, q in enumerate(self.queries):
            for err in q.validate():
                errors.append(f"queries[{i}]: {err}")
        for i, p in enumerate(self.pages):
            for err in p.validate():
                errors.append(f"pages[{i}]: {err}")
        return errors

    def to_metadata(self) -> dict:
        return {
            "source": "google_search_console",
            "site_url": self.site_url,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "fetched_at": self.fetched_at,
            "total_clicks": self.total_clicks,
            "total_impressions": self.total_impressions,
            "query_count": len(self.queries),
            "page_count": len(self.pages),
            "row_count": self.row_count,
            "validation_errors": self.validate(),
        }
