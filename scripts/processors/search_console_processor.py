"""
Process raw Search Console API responses into structured snapshots.

Converts raw GSC query rows into SearchConsoleSnapshot objects with
per-query and per-page aggregations. Saves raw JSON, processed CSVs,
and metadata to the year/month warehouse structure.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from scripts.data_models.search_console_model import (
    SearchConsoleSnapshot,
    SearchQueryRow,
    SearchPageRow,
)

logger = logging.getLogger(__name__)


class SearchConsoleProcessor:
    def __init__(self, data_dir: Path):
        self._data_dir = data_dir

    def _month_dir(self, year: int, month: int) -> Path:
        d = self._data_dir / "search_console" / str(year) / f"{month:02d}"
        d.mkdir(parents=True, exist_ok=True)
        return d

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

    def process_response(
        self,
        raw_rows: list[dict],
        site_url: str,
        start_date: str,
        end_date: str,
        dimensions: list[str],
    ) -> SearchConsoleSnapshot:
        """Convert raw GSC response rows into a SearchConsoleSnapshot."""
        queries: list[SearchQueryRow] = []
        page_agg: dict[str, dict] = {}

        for row in raw_rows:
            keys = row.get("keys", [])
            dim_map = {d: keys[i] if i < len(keys) else "" for i, d in enumerate(dimensions)}

            query = dim_map.get("query", "")
            page = dim_map.get("page", "")
            country = dim_map.get("country", "")
            device = dim_map.get("device", "")
            clicks = int(row.get("clicks", 0))
            impressions = int(row.get("impressions", 0))
            ctr = float(row.get("ctr", 0.0))
            position = float(row.get("position", 0.0))

            queries.append(SearchQueryRow(
                query=query,
                page=page,
                clicks=clicks,
                impressions=impressions,
                ctr=ctr,
                position=position,
                country=country,
                device=device,
            ))

            # Aggregate per page
            if page:
                if page not in page_agg:
                    page_agg[page] = {
                        "clicks": 0,
                        "impressions": 0,
                        "position_sum": 0.0,
                        "query_count": 0,
                    }
                pa = page_agg[page]
                pa["clicks"] += clicks
                pa["impressions"] += impressions
                pa["position_sum"] += position * impressions  # weighted by impressions
                pa["query_count"] += 1

        pages = []
        for page_url, agg in page_agg.items():
            avg_pos = (
                agg["position_sum"] / agg["impressions"]
                if agg["impressions"] > 0
                else 0.0
            )
            page_ctr = (
                agg["clicks"] / agg["impressions"]
                if agg["impressions"] > 0
                else 0.0
            )
            pages.append(SearchPageRow(
                page=page_url,
                clicks=agg["clicks"],
                impressions=agg["impressions"],
                ctr=round(page_ctr, 6),
                avg_position=round(avg_pos, 2),
                query_count=agg["query_count"],
            ))

        snapshot = SearchConsoleSnapshot(
            site_url=site_url,
            start_date=start_date,
            end_date=end_date,
            queries=queries,
            pages=pages,
            total_clicks=sum(q.clicks for q in queries),
            total_impressions=sum(q.impressions for q in queries),
            row_count=len(raw_rows),
        )

        errors = snapshot.validate()
        if errors:
            logger.warning("Validation issues in search console snapshot: %s", errors)

        return snapshot

    def save_snapshot(
        self,
        snapshot: SearchConsoleSnapshot,
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
        raw_path = self._guard_overwrite(out_dir / "search_console.json")
        raw_path.write_text(
            json.dumps(raw_response, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Saved raw search console JSON → %s", raw_path)

        # 2. Queries CSV (full query-level data)
        q_path = self._guard_overwrite(out_dir / "queries.csv")
        q_df = pd.DataFrame([q.to_dict() for q in snapshot.queries])
        q_df.to_csv(q_path, index=False, encoding="utf-8")
        logger.info("Saved %d query rows → %s", len(q_df), q_path)

        # 3. Pages CSV (aggregated per page)
        p_path = self._guard_overwrite(out_dir / "search_pages.csv")
        p_df = pd.DataFrame([p.to_dict() for p in snapshot.pages])
        p_df.to_csv(p_path, index=False, encoding="utf-8")
        logger.info("Saved %d page rows → %s", len(p_df), p_path)

        # 4. Metadata JSON
        meta_path = self._guard_overwrite(out_dir / "metadata.json")
        meta_path.write_text(
            json.dumps(snapshot.to_metadata(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Saved search console metadata → %s", meta_path)

        return {
            "raw": raw_path,
            "queries": q_path,
            "pages": p_path,
            "metadata": meta_path,
        }
