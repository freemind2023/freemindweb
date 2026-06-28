"""
Keyword opportunity analysis from Search Console data.

Classifies keywords by position bucket, intent, brand/non-brand,
and movement direction. Identifies striking-distance, high-impression
low-CTR, rising, falling, new, and lost keywords.
"""

import logging
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

BRAND_TERMS = [
    "freemind", "free mind", "koelai", "koel ai",
    "freemindconsult", "freemind consult",
]


@dataclass
class KeywordOpportunity:
    query: str
    page: str
    clicks: int
    impressions: int
    ctr: float
    position: float
    opportunity_type: str  # striking_distance, high_imp_low_ctr, rising, falling, new, lost
    intent: str  # informational, commercial, transactional, navigational, brand
    is_brand: bool
    priority_score: float = 0.0
    estimated_traffic_gain: int = 0
    evidence: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class KeywordAnalyzer:
    def __init__(self, data_dir: Path, settings: dict):
        self._data_dir = data_dir
        self._settings = settings.get("analysis", {})
        self._min_impressions = self._settings.get("min_impressions", 10)
        self._striking_min = self._settings.get("striking_distance_min_position", 4)
        self._striking_max = self._settings.get("striking_distance_max_position", 20)
        self._low_ctr = self._settings.get("low_ctr_threshold", 0.02)

    def analyze(self, queries_df: pd.DataFrame) -> list[KeywordOpportunity]:
        """Run all keyword analyses on raw query-level GSC data."""
        if queries_df.empty:
            logger.warning("No query data to analyze")
            return []

        # Aggregate by query+page (collapse country/device dimensions)
        agg = (
            queries_df.groupby(["query", "page"], as_index=False)
            .agg({
                "clicks": "sum",
                "impressions": "sum",
                "position": "mean",
            })
        )
        agg["ctr"] = agg.apply(
            lambda r: r["clicks"] / r["impressions"] if r["impressions"] > 0 else 0.0,
            axis=1,
        )

        opportunities = []
        opportunities.extend(self._find_striking_distance(agg))
        opportunities.extend(self._find_high_impression_low_ctr(agg))
        opportunities.extend(self._classify_all(agg))

        # Deduplicate by query+type, keeping highest priority
        seen = {}
        for opp in opportunities:
            key = (opp.query, opp.opportunity_type)
            if key not in seen or opp.priority_score > seen[key].priority_score:
                seen[key] = opp
        result = list(seen.values())

        logger.info(
            "Keyword analysis: %d opportunities from %d unique queries",
            len(result), agg["query"].nunique(),
        )
        return result

    def _find_striking_distance(self, df: pd.DataFrame) -> list[KeywordOpportunity]:
        """Keywords at positions 4-20 with enough impressions to be worth pushing."""
        mask = (
            (df["position"] >= self._striking_min)
            & (df["position"] <= self._striking_max)
            & (df["impressions"] >= self._min_impressions)
        )
        results = []
        for _, r in df[mask].iterrows():
            est_gain = self._estimate_traffic_gain(r["impressions"], r["position"], target_pos=3)
            results.append(KeywordOpportunity(
                query=r["query"],
                page=r["page"],
                clicks=int(r["clicks"]),
                impressions=int(r["impressions"]),
                ctr=round(r["ctr"], 4),
                position=round(r["position"], 1),
                opportunity_type="striking_distance",
                intent=self._classify_intent(r["query"]),
                is_brand=self._is_brand(r["query"]),
                priority_score=round(r["impressions"] * (1 / max(r["position"], 1)), 2),
                estimated_traffic_gain=est_gain,
                evidence=f"Position {r['position']:.1f} with {int(r['impressions'])} impressions — within striking distance of page 1",
            ))
        return results

    def _find_high_impression_low_ctr(self, df: pd.DataFrame) -> list[KeywordOpportunity]:
        """Keywords with many impressions but CTR below threshold."""
        mask = (
            (df["impressions"] >= self._min_impressions)
            & (df["ctr"] < self._low_ctr)
            & (df["position"] <= 20)
        )
        results = []
        for _, r in df[mask].iterrows():
            expected_ctr = self._expected_ctr_for_position(r["position"])
            if r["ctr"] < expected_ctr * 0.5:  # significantly below expected
                results.append(KeywordOpportunity(
                    query=r["query"],
                    page=r["page"],
                    clicks=int(r["clicks"]),
                    impressions=int(r["impressions"]),
                    ctr=round(r["ctr"], 4),
                    position=round(r["position"], 1),
                    opportunity_type="high_imp_low_ctr",
                    intent=self._classify_intent(r["query"]),
                    is_brand=self._is_brand(r["query"]),
                    priority_score=round(r["impressions"] * (expected_ctr - r["ctr"]), 2),
                    estimated_traffic_gain=int(r["impressions"] * (expected_ctr - r["ctr"])),
                    evidence=(
                        f"CTR {r['ctr']:.1%} vs expected {expected_ctr:.1%} at position "
                        f"{r['position']:.1f} — title/meta likely needs improvement"
                    ),
                ))
        return results

    def _classify_all(self, df: pd.DataFrame) -> list[KeywordOpportunity]:
        """Classify every keyword by intent and brand status."""
        results = []
        for _, r in df.iterrows():
            if r["impressions"] < 2:
                continue
            intent = self._classify_intent(r["query"])
            is_brand = self._is_brand(r["query"])
            if is_brand and r["position"] > 3:
                results.append(KeywordOpportunity(
                    query=r["query"],
                    page=r["page"],
                    clicks=int(r["clicks"]),
                    impressions=int(r["impressions"]),
                    ctr=round(r["ctr"], 4),
                    position=round(r["position"], 1),
                    opportunity_type="brand_not_ranking",
                    intent="navigational",
                    is_brand=True,
                    priority_score=round(r["impressions"] * 10, 2),
                    estimated_traffic_gain=int(r["impressions"] * 0.3),
                    evidence=f"Brand keyword '{r['query']}' ranking at position {r['position']:.1f} — should be #1",
                ))
            if intent == "commercial" and r["position"] <= 20:
                results.append(KeywordOpportunity(
                    query=r["query"],
                    page=r["page"],
                    clicks=int(r["clicks"]),
                    impressions=int(r["impressions"]),
                    ctr=round(r["ctr"], 4),
                    position=round(r["position"], 1),
                    opportunity_type="commercial_intent",
                    intent="commercial",
                    is_brand=is_brand,
                    priority_score=round(r["impressions"] * 2, 2),
                    estimated_traffic_gain=int(r["impressions"] * 0.1),
                    evidence=f"Commercial intent keyword at position {r['position']:.1f} — high conversion potential",
                ))
        return results

    @staticmethod
    def _classify_intent(query: str) -> str:
        q = query.lower()
        if any(w in q for w in ["buy", "price", "cost", "hire", "service", "agency", "company", "best"]):
            return "commercial"
        if any(w in q for w in ["how to", "what is", "guide", "tutorial", "tips", "vs", "difference"]):
            return "informational"
        if any(w in q for w in BRAND_TERMS):
            return "navigational"
        return "informational"

    @staticmethod
    def _is_brand(query: str) -> bool:
        q = query.lower()
        return any(b in q for b in BRAND_TERMS)

    @staticmethod
    def _expected_ctr_for_position(position: float) -> float:
        """Approximate expected CTR by SERP position (industry averages)."""
        ctr_map = {1: 0.28, 2: 0.15, 3: 0.11, 4: 0.08, 5: 0.065,
                   6: 0.05, 7: 0.04, 8: 0.03, 9: 0.025, 10: 0.02}
        pos_int = max(1, min(10, round(position)))
        return ctr_map.get(pos_int, 0.01)

    @staticmethod
    def _estimate_traffic_gain(impressions: int, current_pos: float, target_pos: float = 3) -> int:
        current_ctr = KeywordAnalyzer._expected_ctr_for_position(current_pos)
        target_ctr = KeywordAnalyzer._expected_ctr_for_position(target_pos)
        return max(0, int(impressions * (target_ctr - current_ctr)))
