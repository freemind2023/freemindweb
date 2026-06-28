"""
CTR optimization analysis.

Finds pages with high impressions but low CTR relative to their
position, and generates specific recommendations for title/meta
improvements, rich results, and FAQ opportunities.
"""

import logging
from dataclasses import dataclass, asdict
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class CTROpportunity:
    url: str
    current_ctr: float
    expected_ctr: float
    ctr_gap: float
    impressions: int
    clicks: int
    position: float
    top_queries: list
    recommendation_type: str  # title_rewrite, meta_rewrite, rich_result, faq
    recommendation: str
    estimated_click_gain: int
    priority_score: float
    evidence: str

    def to_dict(self) -> dict:
        return asdict(self)


# Average CTR by position (industry benchmarks)
POSITION_CTR = {
    1: 0.28, 2: 0.15, 3: 0.11, 4: 0.08, 5: 0.065,
    6: 0.05, 7: 0.04, 8: 0.03, 9: 0.025, 10: 0.02,
}


class CTRAnalyzer:
    def __init__(self, data_dir: Path, settings: dict):
        self._data_dir = data_dir
        self._settings = settings

    def analyze(
        self,
        combined_df: pd.DataFrame,
        queries_df: pd.DataFrame,
    ) -> list[CTROpportunity]:
        """Find pages with CTR below expected for their position."""
        opportunities = []
        if combined_df.empty:
            return opportunities

        # Only analyze pages with search visibility
        visible = combined_df[
            (combined_df["impressions"] >= 10) & (combined_df["avg_position"] > 0)
        ].copy()

        for _, row in visible.iterrows():
            pos = row["avg_position"]
            pos_int = max(1, min(10, round(pos)))
            expected = POSITION_CTR.get(pos_int, 0.01)
            actual = row["ctr"]

            if actual >= expected * 0.7:
                continue  # CTR is reasonable

            gap = expected - actual
            est_clicks = int(row["impressions"] * gap)

            # Get top queries for this page
            page_queries = []
            if not queries_df.empty:
                url_variants = [row["url"]]
                page_q = queries_df[queries_df["page"].str.contains(row["url"].rstrip("/"), na=False)]
                page_q_agg = (
                    page_q.groupby("query", as_index=False)
                    .agg({"impressions": "sum", "clicks": "sum", "position": "mean"})
                    .sort_values("impressions", ascending=False)
                    .head(5)
                )
                page_queries = page_q_agg["query"].tolist()

            # Determine recommendation type
            if actual == 0 and pos <= 10:
                rec_type = "title_rewrite"
                rec = (
                    f"Page ranks at position {pos:.1f} with {int(row['impressions'])} impressions "
                    f"but 0 clicks. Title and meta description are likely unappealing. "
                    f"Rewrite with action verbs and value propositions targeting: {', '.join(page_queries[:3])}"
                )
            elif pos <= 5:
                rec_type = "rich_result"
                rec = (
                    f"Position {pos:.1f} should get ~{expected:.0%} CTR but getting {actual:.1%}. "
                    f"Add FAQ schema, review snippets, or How-To markup to win rich results."
                )
            elif pos <= 10:
                rec_type = "meta_rewrite"
                rec = (
                    f"Position {pos:.1f} CTR is {actual:.1%} vs expected {expected:.1%}. "
                    f"Rewrite meta description with clear CTA and value proposition."
                )
            else:
                rec_type = "faq"
                rec = (
                    f"Position {pos:.1f} — add FAQ section targeting People Also Ask for "
                    f"'{page_queries[0] if page_queries else 'related queries'}' to boost visibility."
                )

            opportunities.append(CTROpportunity(
                url=row["url"],
                current_ctr=round(actual, 4),
                expected_ctr=round(expected, 4),
                ctr_gap=round(gap, 4),
                impressions=int(row["impressions"]),
                clicks=int(row["clicks"]),
                position=round(pos, 1),
                top_queries=page_queries,
                recommendation_type=rec_type,
                recommendation=rec,
                estimated_click_gain=est_clicks,
                priority_score=round(est_clicks * (1 / max(pos, 1)), 2),
                evidence=(
                    f"GSC: {int(row['impressions'])} impressions, {int(row['clicks'])} clicks, "
                    f"CTR {actual:.1%} vs expected {expected:.1%} at position {pos:.1f}"
                ),
            ))

        opportunities.sort(key=lambda x: x.priority_score, reverse=True)
        logger.info("CTR analysis: %d improvement opportunities", len(opportunities))
        return opportunities
