"""
Master opportunity detector — orchestrates all analyzers and
produces a unified list of prioritized SEO opportunities.

Combines keyword, page, CTR, trend, and technical findings into
a single ranked output.
"""

import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path

import pandas as pd

from .keyword_analyzer import KeywordAnalyzer, KeywordOpportunity
from .page_analyzer import PageAnalyzer, PageIssue
from .ctr_analyzer import CTRAnalyzer, CTROpportunity
from .trend_analyzer import TrendAnalyzer, Trend

logger = logging.getLogger(__name__)


@dataclass
class SEOOpportunity:
    id: int
    category: str  # keyword, page, ctr, trend, technical, content_gap
    title: str
    detail: str
    priority_score: float
    business_impact: str  # critical, high, medium, low
    seo_impact: str
    difficulty: str  # easy, medium, hard
    estimated_traffic_gain: int
    estimated_lead_gain: int
    estimated_time: str
    confidence: float  # 0.0 to 1.0
    evidence: str
    affected_pages: list[str]
    dependencies: list[str] = field(default_factory=list)
    roadmap_day: int = 0  # maps to roadmap task if applicable

    def to_dict(self) -> dict:
        return asdict(self)


class OpportunityDetector:
    def __init__(self, data_dir: Path, website_root: str, settings: dict):
        self._data_dir = data_dir
        self._settings = settings
        self._keyword_analyzer = KeywordAnalyzer(data_dir, settings)
        self._page_analyzer = PageAnalyzer(data_dir, website_root, settings)
        self._ctr_analyzer = CTRAnalyzer(data_dir, settings)
        self._trend_analyzer = TrendAnalyzer(data_dir)

    def detect_all(
        self,
        combined_df: pd.DataFrame,
        queries_df: pd.DataFrame,
        year: int,
        month: int,
    ) -> list[SEOOpportunity]:
        """Run all analyzers and produce a unified, ranked opportunity list."""
        opportunities = []
        opp_id = 1

        # 1. Keyword opportunities
        kw_opps = self._keyword_analyzer.analyze(queries_df)
        for kw in kw_opps:
            opportunities.append(SEOOpportunity(
                id=opp_id,
                category="keyword",
                title=f"[{kw.opportunity_type.upper()}] {kw.query}",
                detail=kw.evidence,
                priority_score=kw.priority_score,
                business_impact="high" if kw.intent == "commercial" else "medium",
                seo_impact="high" if kw.position <= 10 else "medium",
                difficulty="easy" if kw.opportunity_type == "striking_distance" else "medium",
                estimated_traffic_gain=kw.estimated_traffic_gain,
                estimated_lead_gain=max(1, kw.estimated_traffic_gain // 50),
                estimated_time="30 min",
                confidence=0.8 if kw.impressions >= 20 else 0.5,
                evidence=kw.evidence,
                affected_pages=[kw.page],
            ))
            opp_id += 1

        # 2. Page performance issues
        page_issues = self._page_analyzer.analyze_combined(combined_df)
        for pi in page_issues:
            opportunities.append(SEOOpportunity(
                id=opp_id,
                category="page",
                title=f"[{pi.issue_type.upper()}] {pi.url}",
                detail=pi.detail,
                priority_score={"critical": 100, "high": 75, "medium": 50, "low": 25}[pi.severity],
                business_impact=pi.business_impact,
                seo_impact=pi.seo_impact,
                difficulty="easy" if pi.estimated_time in ("5 min", "10 min", "15 min") else "medium",
                estimated_traffic_gain=5,
                estimated_lead_gain=1,
                estimated_time=pi.estimated_time,
                confidence=0.9,
                evidence=pi.evidence,
                affected_pages=[pi.url],
            ))
            opp_id += 1

        # 3. Technical HTML issues
        tech_issues = self._page_analyzer.analyze_html()
        for ti in tech_issues:
            opportunities.append(SEOOpportunity(
                id=opp_id,
                category="technical",
                title=f"[{ti.issue_type.upper()}] {ti.url}",
                detail=ti.detail,
                priority_score={"critical": 100, "high": 75, "medium": 50, "low": 25}[ti.severity],
                business_impact=ti.business_impact,
                seo_impact=ti.seo_impact,
                difficulty="easy",
                estimated_traffic_gain=3,
                estimated_lead_gain=0,
                estimated_time=ti.estimated_time,
                confidence=1.0,  # HTML facts are certain
                evidence=ti.evidence,
                affected_pages=[ti.url],
            ))
            opp_id += 1

        # 4. CTR opportunities
        ctr_opps = self._ctr_analyzer.analyze(combined_df, queries_df)
        for co in ctr_opps:
            opportunities.append(SEOOpportunity(
                id=opp_id,
                category="ctr",
                title=f"[CTR_GAP] {co.url}",
                detail=co.recommendation,
                priority_score=co.priority_score,
                business_impact="high" if co.estimated_click_gain > 10 else "medium",
                seo_impact="high",
                difficulty="easy",
                estimated_traffic_gain=co.estimated_click_gain,
                estimated_lead_gain=max(1, co.estimated_click_gain // 30),
                estimated_time="20 min",
                confidence=0.7,
                evidence=co.evidence,
                affected_pages=[co.url],
            ))
            opp_id += 1

        # 5. Trends
        trends = self._trend_analyzer.analyze(year, month)
        for t in trends:
            if t.direction in ("falling", "lost"):
                opportunities.append(SEOOpportunity(
                    id=opp_id,
                    category="trend",
                    title=f"[{t.direction.upper()}] {t.entity} ({t.metric})",
                    detail=t.evidence,
                    priority_score=abs(t.change_absolute) * 2,
                    business_impact="high" if t.metric == "clicks" else "medium",
                    seo_impact="high",
                    difficulty="medium",
                    estimated_traffic_gain=int(abs(t.change_absolute)),
                    estimated_lead_gain=max(1, int(abs(t.change_absolute)) // 50),
                    estimated_time="45 min",
                    confidence=0.6,
                    evidence=t.evidence,
                    affected_pages=[t.entity] if t.entity_type == "page" else [],
                ))
                opp_id += 1

        # Sort by priority score descending
        opportunities.sort(key=lambda x: x.priority_score, reverse=True)
        logger.info("Detected %d total opportunities across all categories", len(opportunities))
        return opportunities
