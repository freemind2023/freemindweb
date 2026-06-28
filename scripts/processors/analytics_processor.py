"""
Process raw GA4 API responses into structured snapshots.

Converts raw GA4 RunReportResponse data into AnalyticsSnapshot objects
with landing page and traffic source breakdowns. Saves raw JSON,
processed CSVs, and metadata to the year/month warehouse structure.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from scripts.data_models.analytics_model import (
    AnalyticsSnapshot,
    LandingPageRow,
    TrafficSourceRow,
)

logger = logging.getLogger(__name__)


class AnalyticsProcessor:
    def __init__(self, data_dir: Path):
        self._data_dir = data_dir

    def _month_dir(self, year: int, month: int) -> Path:
        d = self._data_dir / "analytics" / str(year) / f"{month:02d}"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _guard_overwrite(self, path: Path) -> Path:
        """If file already exists, append a counter to avoid overwriting."""
        if not path.exists():
            return path
        stem, suffix = path.stem, path.suffix
        counter = 1
        while True:
            candidate = path.parent / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                logger.warning(
                    "File %s exists — saving as %s to avoid overwrite",
                    path.name,
                    candidate.name,
                )
                return candidate
            counter += 1

    def process_response(
        self,
        raw_rows: list[dict],
        property_id: str,
        start_date: str,
        end_date: str,
        dim_headers: list[str],
        met_headers: list[str],
    ) -> AnalyticsSnapshot:
        """Convert raw API row dicts into an AnalyticsSnapshot."""
        landing_pages: dict[str, LandingPageRow] = {}
        traffic_sources: dict[str, TrafficSourceRow] = {}

        for row in raw_rows:
            page_path = row.get("pagePath", "")
            source = row.get("sessionSource", "(not set)")
            medium = row.get("sessionMedium", "(not set)")

            sessions = int(float(row.get("sessions", 0)))
            total_users = int(float(row.get("totalUsers", 0)))
            new_users = int(float(row.get("newUsers", 0)))
            bounce_rate = float(row.get("bounceRate", 0))
            avg_duration = float(row.get("averageSessionDuration", 0))
            page_views = int(float(row.get("screenPageViews", 0)))
            conversions = int(float(row.get("conversions", 0)))

            # Aggregate by page path
            if page_path:
                if page_path not in landing_pages:
                    landing_pages[page_path] = LandingPageRow(page_path=page_path)
                lp = landing_pages[page_path]
                lp.sessions += sessions
                lp.total_users += total_users
                lp.new_users += new_users
                lp.screen_page_views += page_views
                lp.conversions += conversions
                # Weighted average for rates
                if lp.sessions > 0:
                    weight = sessions / lp.sessions
                    lp.bounce_rate = lp.bounce_rate * (1 - weight) + bounce_rate * weight
                    lp.avg_session_duration = (
                        lp.avg_session_duration * (1 - weight) + avg_duration * weight
                    )

            # Aggregate by source/medium
            src_key = f"{source}|{medium}"
            if src_key not in traffic_sources:
                traffic_sources[src_key] = TrafficSourceRow(
                    source=source, medium=medium
                )
            ts = traffic_sources[src_key]
            ts.sessions += sessions
            ts.total_users += total_users
            ts.new_users += new_users
            ts.conversions += conversions
            if ts.sessions > 0:
                weight = sessions / ts.sessions
                ts.bounce_rate = ts.bounce_rate * (1 - weight) + bounce_rate * weight

        # Compute engagement_rate for landing pages
        for lp in landing_pages.values():
            lp.engagement_rate = round(1.0 - lp.bounce_rate, 4) if lp.sessions > 0 else 0.0

        snapshot = AnalyticsSnapshot(
            property_id=property_id,
            start_date=start_date,
            end_date=end_date,
            landing_pages=list(landing_pages.values()),
            traffic_sources=list(traffic_sources.values()),
            total_sessions=sum(lp.sessions for lp in landing_pages.values()),
            total_users=sum(lp.total_users for lp in landing_pages.values()),
            row_count=len(raw_rows),
        )

        errors = snapshot.validate()
        if errors:
            logger.warning("Validation issues in analytics snapshot: %s", errors)

        return snapshot

    def save_snapshot(
        self,
        snapshot: AnalyticsSnapshot,
        raw_response: list[dict],
        year: int | None = None,
        month: int | None = None,
    ) -> dict[str, Path]:
        """Persist raw JSON, processed CSVs, and metadata to the warehouse."""
        now = datetime.now()
        year = year or now.year
        month = month or now.month
        out_dir = self._month_dir(year, month)

        # 1. Raw JSON
        raw_path = self._guard_overwrite(out_dir / "analytics.json")
        raw_path.write_text(
            json.dumps(raw_response, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Saved raw analytics JSON → %s", raw_path)

        # 2. Landing pages CSV
        lp_path = self._guard_overwrite(out_dir / "landing_pages.csv")
        lp_df = pd.DataFrame([lp.to_dict() for lp in snapshot.landing_pages])
        lp_df.to_csv(lp_path, index=False, encoding="utf-8")
        logger.info("Saved %d landing pages → %s", len(lp_df), lp_path)

        # 3. Traffic sources CSV
        ts_path = self._guard_overwrite(out_dir / "traffic_sources.csv")
        ts_df = pd.DataFrame([ts.to_dict() for ts in snapshot.traffic_sources])
        ts_df.to_csv(ts_path, index=False, encoding="utf-8")
        logger.info("Saved %d traffic sources → %s", len(ts_df), ts_path)

        # 4. Metadata JSON
        meta_path = self._guard_overwrite(out_dir / "metadata.json")
        meta_path.write_text(
            json.dumps(snapshot.to_metadata(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Saved analytics metadata → %s", meta_path)

        return {
            "raw": raw_path,
            "landing_pages": lp_path,
            "traffic_sources": ts_path,
            "metadata": meta_path,
        }
