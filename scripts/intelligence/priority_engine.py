"""
Priority scoring engine for SEO recommendations.

Scores every opportunity using a weighted formula combining business
impact, SEO impact, difficulty, estimated traffic gain, confidence,
and time investment. Produces a final ranked list.
"""

import logging
from dataclasses import dataclass
from .opportunity_detector import SEOOpportunity

logger = logging.getLogger(__name__)

IMPACT_WEIGHTS = {
    "critical": 1.0,
    "high": 0.8,
    "medium": 0.5,
    "low": 0.2,
}

DIFFICULTY_WEIGHTS = {
    "easy": 1.0,
    "medium": 0.6,
    "hard": 0.3,
}


class PriorityEngine:
    def __init__(self, settings: dict):
        self._settings = settings

    def score_and_rank(self, opportunities: list[SEOOpportunity]) -> list[SEOOpportunity]:
        """Re-score all opportunities with a unified priority formula and sort."""
        for opp in opportunities:
            opp.priority_score = self._compute_score(opp)

        ranked = sorted(opportunities, key=lambda x: x.priority_score, reverse=True)

        for i, opp in enumerate(ranked):
            opp.id = i + 1

        logger.info("Priority engine ranked %d opportunities", len(ranked))
        return ranked

    def _compute_score(self, opp: SEOOpportunity) -> float:
        biz = IMPACT_WEIGHTS.get(opp.business_impact, 0.5)
        seo = IMPACT_WEIGHTS.get(opp.seo_impact, 0.5)
        diff = DIFFICULTY_WEIGHTS.get(opp.difficulty, 0.6)

        traffic_factor = min(opp.estimated_traffic_gain / 10, 10)
        lead_factor = min(opp.estimated_lead_gain, 5)

        score = (
            (biz * 30)
            + (seo * 25)
            + (diff * 15)
            + (traffic_factor * 15)
            + (lead_factor * 5)
            + (opp.confidence * 10)
        )
        return round(score, 2)

    def get_top_n(self, opportunities: list[SEOOpportunity], n: int = 30) -> list[SEOOpportunity]:
        """Return top N opportunities after scoring."""
        ranked = self.score_and_rank(opportunities)
        return ranked[:n]

    def group_by_category(self, opportunities: list[SEOOpportunity]) -> dict[str, list[SEOOpportunity]]:
        """Group ranked opportunities by category."""
        groups: dict[str, list[SEOOpportunity]] = {}
        for opp in opportunities:
            groups.setdefault(opp.category, []).append(opp)
        return groups
