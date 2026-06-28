"""
Data models for Google Analytics 4 snapshots.

Defines the schema for raw API responses, landing page aggregations,
and traffic source breakdowns. Handles validation and serialization.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class LandingPageRow:
    page_path: str
    sessions: int = 0
    total_users: int = 0
    new_users: int = 0
    bounce_rate: float = 0.0
    avg_session_duration: float = 0.0
    screen_page_views: int = 0
    conversions: int = 0
    engagement_rate: float = 0.0

    def validate(self) -> list[str]:
        errors = []
        if not self.page_path:
            errors.append("page_path is empty")
        if self.sessions < 0:
            errors.append(f"sessions is negative: {self.sessions}")
        if self.total_users < 0:
            errors.append(f"total_users is negative: {self.total_users}")
        if not 0.0 <= self.bounce_rate <= 1.0:
            errors.append(f"bounce_rate out of range [0,1]: {self.bounce_rate}")
        return errors

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TrafficSourceRow:
    source: str
    medium: str
    sessions: int = 0
    total_users: int = 0
    new_users: int = 0
    bounce_rate: float = 0.0
    conversions: int = 0

    def validate(self) -> list[str]:
        errors = []
        if not self.source:
            errors.append("source is empty")
        if self.sessions < 0:
            errors.append(f"sessions is negative: {self.sessions}")
        return errors

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AnalyticsSnapshot:
    property_id: str
    start_date: str
    end_date: str
    fetched_at: str = ""
    landing_pages: list[LandingPageRow] = field(default_factory=list)
    traffic_sources: list[TrafficSourceRow] = field(default_factory=list)
    total_sessions: int = 0
    total_users: int = 0
    row_count: int = 0

    def __post_init__(self):
        if not self.fetched_at:
            self.fetched_at = datetime.now().isoformat()

    def validate(self) -> list[str]:
        errors = []
        if not self.property_id:
            errors.append("property_id is empty")
        if not self.start_date:
            errors.append("start_date is empty")
        if not self.end_date:
            errors.append("end_date is empty")
        for i, lp in enumerate(self.landing_pages):
            for err in lp.validate():
                errors.append(f"landing_pages[{i}]: {err}")
        for i, ts in enumerate(self.traffic_sources):
            for err in ts.validate():
                errors.append(f"traffic_sources[{i}]: {err}")
        return errors

    def to_metadata(self) -> dict:
        return {
            "source": "google_analytics_4",
            "property_id": self.property_id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "fetched_at": self.fetched_at,
            "total_sessions": self.total_sessions,
            "total_users": self.total_users,
            "landing_page_count": len(self.landing_pages),
            "traffic_source_count": len(self.traffic_sources),
            "row_count": self.row_count,
            "validation_errors": self.validate(),
        }
