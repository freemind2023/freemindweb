"""
Generate intelligence reports from analyzed data.

Produces structured JSON reports consumed by the roadmap manager.
These are internal data artifacts, not user-facing Markdown reports.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from .opportunity_detector import SEOOpportunity

logger = logging.getLogger(__name__)


class ReportGenerator:
    def __init__(self, output_dir: Path):
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def generate_intelligence_report(
        self,
        opportunities: list[SEOOpportunity],
        year: int,
        month: int,
    ) -> Path:
        """Generate a full intelligence report as JSON."""
        by_category = {}
        for opp in opportunities:
            by_category.setdefault(opp.category, []).append(opp.to_dict())

        report = {
            "generated_at": datetime.now().isoformat(),
            "period": f"{year}-{month:02d}",
            "total_opportunities": len(opportunities),
            "summary": {
                "keyword": len(by_category.get("keyword", [])),
                "page": len(by_category.get("page", [])),
                "ctr": len(by_category.get("ctr", [])),
                "technical": len(by_category.get("technical", [])),
                "trend": len(by_category.get("trend", [])),
                "content_gap": len(by_category.get("content_gap", [])),
            },
            "top_10": [o.to_dict() for o in opportunities[:10]],
            "by_category": by_category,
            "estimated_total_traffic_gain": sum(o.estimated_traffic_gain for o in opportunities),
            "estimated_total_lead_gain": sum(o.estimated_lead_gain for o in opportunities),
        }

        path = self._output_dir / f"intelligence_report_{year}_{month:02d}.json"
        path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Intelligence report saved: %s (%d opportunities)", path.name, len(opportunities))
        return path
