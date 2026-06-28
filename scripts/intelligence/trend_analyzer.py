"""
Trend analysis across historical monthly snapshots.

Compares current month vs previous month(s) to detect rising/falling
keywords, traffic changes, and emerging opportunities.
"""

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class Trend:
    entity: str  # URL or keyword
    entity_type: str  # page, keyword
    metric: str  # clicks, impressions, sessions, position
    current_value: float
    previous_value: float
    change_absolute: float
    change_percent: float
    direction: str  # rising, falling, stable, new, lost
    evidence: str

    def to_dict(self) -> dict:
        return asdict(self)


class TrendAnalyzer:
    def __init__(self, data_dir: Path):
        self._data_dir = data_dir

    def analyze(
        self,
        current_year: int,
        current_month: int,
    ) -> list[Trend]:
        """Compare current month data against previous month."""
        prev_year, prev_month = self._prev_month(current_year, current_month)
        trends = []

        # Load current and previous combined data
        current = self._load_combined(current_year, current_month)
        previous = self._load_combined(prev_year, prev_month)

        if current is not None and previous is not None:
            trends.extend(self._compare_pages(current, previous))

        # Load current and previous search queries
        cur_queries = self._load_queries(current_year, current_month)
        prev_queries = self._load_queries(prev_year, prev_month)

        if cur_queries is not None and prev_queries is not None:
            trends.extend(self._compare_keywords(cur_queries, prev_queries))
        elif cur_queries is not None:
            logger.info("No previous month query data — marking all keywords as new")
            trends.extend(self._mark_all_new(cur_queries))

        logger.info("Trend analysis: %d trends detected", len(trends))
        return trends

    def _compare_pages(self, current: pd.DataFrame, previous: pd.DataFrame) -> list[Trend]:
        trends = []
        merged = pd.merge(
            current, previous,
            on="url", how="outer", suffixes=("_cur", "_prev")
        )

        for _, r in merged.iterrows():
            url = r["url"]
            for metric in ["clicks", "impressions", "sessions"]:
                cur = r.get(f"{metric}_cur", 0) or 0
                prev = r.get(f"{metric}_prev", 0) or 0
                if cur == 0 and prev == 0:
                    continue

                change = cur - prev
                pct = (change / prev * 100) if prev > 0 else (100.0 if cur > 0 else 0.0)

                if abs(pct) < 10 and abs(change) < 3:
                    direction = "stable"
                elif prev == 0 and cur > 0:
                    direction = "new"
                elif cur == 0 and prev > 0:
                    direction = "lost"
                elif change > 0:
                    direction = "rising"
                else:
                    direction = "falling"

                if direction in ("stable",):
                    continue

                trends.append(Trend(
                    entity=url,
                    entity_type="page",
                    metric=metric,
                    current_value=float(cur),
                    previous_value=float(prev),
                    change_absolute=float(change),
                    change_percent=round(pct, 1),
                    direction=direction,
                    evidence=f"{metric}: {prev:.0f} → {cur:.0f} ({change:+.0f}, {pct:+.1f}%)",
                ))
        return trends

    def _compare_keywords(self, current: pd.DataFrame, previous: pd.DataFrame) -> list[Trend]:
        trends = []
        cur_agg = current.groupby("query", as_index=False).agg(
            {"clicks": "sum", "impressions": "sum", "position": "mean"}
        )
        prev_agg = previous.groupby("query", as_index=False).agg(
            {"clicks": "sum", "impressions": "sum", "position": "mean"}
        )

        merged = pd.merge(cur_agg, prev_agg, on="query", how="outer", suffixes=("_cur", "_prev"))

        for _, r in merged.iterrows():
            query = r["query"]
            cur_imp = r.get("impressions_cur", 0) or 0
            prev_imp = r.get("impressions_prev", 0) or 0
            cur_pos = r.get("position_cur", 0) or 0
            prev_pos = r.get("position_prev", 0) or 0

            if cur_imp < 2 and prev_imp < 2:
                continue

            if prev_imp == 0 and cur_imp > 0:
                trends.append(Trend(
                    entity=query, entity_type="keyword", metric="impressions",
                    current_value=cur_imp, previous_value=0,
                    change_absolute=cur_imp, change_percent=100.0,
                    direction="new",
                    evidence=f"New keyword: {int(cur_imp)} impressions, position {cur_pos:.1f}",
                ))
            elif cur_imp == 0 and prev_imp > 0:
                trends.append(Trend(
                    entity=query, entity_type="keyword", metric="impressions",
                    current_value=0, previous_value=prev_imp,
                    change_absolute=-prev_imp, change_percent=-100.0,
                    direction="lost",
                    evidence=f"Lost keyword: had {int(prev_imp)} impressions last month",
                ))
            elif cur_pos > 0 and prev_pos > 0:
                pos_change = prev_pos - cur_pos  # positive = improved
                if abs(pos_change) >= 3:
                    direction = "rising" if pos_change > 0 else "falling"
                    trends.append(Trend(
                        entity=query, entity_type="keyword", metric="position",
                        current_value=cur_pos, previous_value=prev_pos,
                        change_absolute=-pos_change, change_percent=round(pos_change / prev_pos * 100, 1),
                        direction=direction,
                        evidence=f"Position: {prev_pos:.1f} → {cur_pos:.1f} ({pos_change:+.1f} positions)",
                    ))
        return trends

    def _mark_all_new(self, queries: pd.DataFrame) -> list[Trend]:
        agg = queries.groupby("query", as_index=False).agg(
            {"impressions": "sum", "position": "mean"}
        )
        trends = []
        for _, r in agg[agg["impressions"] >= 2].iterrows():
            trends.append(Trend(
                entity=r["query"], entity_type="keyword", metric="impressions",
                current_value=r["impressions"], previous_value=0,
                change_absolute=r["impressions"], change_percent=100.0,
                direction="new",
                evidence=f"First snapshot: {int(r['impressions'])} impressions at position {r['position']:.1f}",
            ))
        return trends

    def _load_combined(self, year: int, month: int) -> pd.DataFrame | None:
        path = self._data_dir / "history" / str(year) / f"{month:02d}" / "combined_pages.csv"
        if not path.exists():
            path = self._data_dir / "processed" / "combined_pages.csv"
        if path.exists():
            return pd.read_csv(path, encoding="utf-8")
        return None

    def _load_queries(self, year: int, month: int) -> pd.DataFrame | None:
        path = self._data_dir / "search_console" / str(year) / f"{month:02d}" / "queries.csv"
        if path.exists():
            return pd.read_csv(path, encoding="utf-8")
        return None

    @staticmethod
    def _prev_month(year: int, month: int) -> tuple[int, int]:
        if month == 1:
            return year - 1, 12
        return year, month - 1
