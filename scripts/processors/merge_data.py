"""
Merge GA4 and Search Console processed data into combined_pages.csv.

Joins landing page analytics with search page performance by normalizing
URLs, producing the unified CombinedSnapshot that feeds the AI engine.
Detects missing data on both sides and logs gaps.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import math

import pandas as pd

from scripts.data_models.combined_model import CombinedPageRow, CombinedSnapshot, COMBINED_COLUMNS


def _safe_int(val, default: int = 0) -> int:
    try:
        f = float(val)
        return default if math.isnan(f) else int(f)
    except (TypeError, ValueError):
        return default


def _safe_float(val, default: float = 0.0) -> float:
    try:
        f = float(val)
        return default if math.isnan(f) else f
    except (TypeError, ValueError):
        return default

logger = logging.getLogger(__name__)


class DataMerger:
    def __init__(self, data_dir: Path):
        self._data_dir = data_dir

    def _guard_overwrite(self, path: Path) -> Path:
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

    @staticmethod
    def normalize_url(url: str) -> str:
        """Reduce a URL or path to its canonical path for matching."""
        if url.startswith("http"):
            parsed = urlparse(url)
            path = parsed.path
        else:
            path = url
        path = path.rstrip("/") or "/"
        return path.lower()

    def merge(
        self,
        analytics_landing_pages: pd.DataFrame,
        search_console_pages: pd.DataFrame,
        start_date: str,
        end_date: str,
    ) -> CombinedSnapshot:
        """Merge GA4 landing pages with GSC page data by normalized URL."""
        # Normalize keys
        ga4 = analytics_landing_pages.copy()
        gsc = search_console_pages.copy()

        ga4["_merge_key"] = ga4["page_path"].apply(self.normalize_url)
        gsc["_merge_key"] = gsc["page"].apply(self.normalize_url)

        # Full outer join to keep pages from both sources
        merged = pd.merge(
            ga4, gsc,
            on="_merge_key",
            how="outer",
            suffixes=("_ga4", "_gsc"),
        )

        pages = []
        for _, row in merged.iterrows():
            url = row.get("_merge_key", "")

            pages.append(CombinedPageRow(
                url=url,
                clicks=_safe_int(row.get("clicks")),
                impressions=_safe_int(row.get("impressions")),
                ctr=_safe_float(row.get("ctr")),
                avg_position=_safe_float(row.get("avg_position")),
                sessions=_safe_int(row.get("sessions")),
                total_users=_safe_int(row.get("total_users")),
                new_users=_safe_int(row.get("new_users")),
                bounce_rate=_safe_float(row.get("bounce_rate")),
                avg_session_duration=_safe_float(row.get("avg_session_duration")),
                screen_page_views=_safe_int(row.get("screen_page_views")),
                engagement_rate=_safe_float(row.get("engagement_rate")),
                conversions=_safe_int(row.get("conversions")),
            ))

        snapshot = CombinedSnapshot(
            start_date=start_date,
            end_date=end_date,
            pages=pages,
        )

        # Log missing data
        missing = snapshot.missing_data_report()
        logger.info(
            "Merged %d pages — %d missing search data, %d missing analytics data",
            missing["total_pages"],
            missing["pages_missing_search_data"],
            missing["pages_missing_analytics_data"],
        )

        errors = snapshot.validate()
        if errors:
            logger.warning("Validation issues in combined snapshot: %s", errors)

        return snapshot

    def load_latest_analytics(self, year: int, month: int) -> pd.DataFrame | None:
        """Load the most recent landing_pages.csv for a given month."""
        month_dir = self._data_dir / "analytics" / str(year) / f"{month:02d}"
        return self._load_latest_csv(month_dir, "landing_pages")

    def load_latest_search_console(self, year: int, month: int) -> pd.DataFrame | None:
        """Load the most recent search_pages.csv for a given month."""
        month_dir = self._data_dir / "search_console" / str(year) / f"{month:02d}"
        return self._load_latest_csv(month_dir, "search_pages")

    def _load_latest_csv(self, month_dir: Path, stem: str) -> pd.DataFrame | None:
        if not month_dir.exists():
            logger.warning("Directory not found: %s", month_dir)
            return None
        candidates = sorted(month_dir.glob(f"{stem}*.csv"), key=lambda p: p.stat().st_mtime)
        if not candidates:
            logger.warning("No %s*.csv files in %s", stem, month_dir)
            return None
        latest = candidates[-1]
        logger.info("Loading %s", latest)
        return pd.read_csv(latest, encoding="utf-8")

    def save_combined(
        self,
        snapshot: CombinedSnapshot,
        year: int | None = None,
        month: int | None = None,
    ) -> dict[str, Path]:
        """Save combined_pages.csv and metadata to processed/ and history/."""
        now = datetime.now()
        year = year or now.year
        month = month or now.month

        # processed/ — always holds the latest
        processed_dir = self._data_dir / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)

        combined_df = pd.DataFrame(
            [p.to_dict() for p in snapshot.pages],
            columns=COMBINED_COLUMNS,
        )

        # Primary output
        processed_path = processed_dir / "combined_pages.csv"
        combined_df.to_csv(processed_path, index=False, encoding="utf-8")
        logger.info("Saved %d combined pages → %s", len(combined_df), processed_path)

        # Metadata
        meta_path = processed_dir / "combined_metadata.json"
        meta_path.write_text(
            json.dumps(snapshot.to_metadata(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # history/ — archived copy, never overwritten
        history_dir = self._data_dir / "history" / str(year) / f"{month:02d}"
        history_dir.mkdir(parents=True, exist_ok=True)

        hist_csv = self._guard_overwrite(history_dir / "combined_pages.csv")
        combined_df.to_csv(hist_csv, index=False, encoding="utf-8")

        hist_meta = self._guard_overwrite(history_dir / "combined_metadata.json")
        hist_meta.write_text(
            json.dumps(snapshot.to_metadata(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Archived combined snapshot → %s", history_dir)

        return {
            "combined_csv": processed_path,
            "metadata": meta_path,
            "history_csv": hist_csv,
            "history_metadata": hist_meta,
        }
