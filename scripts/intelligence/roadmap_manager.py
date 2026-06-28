"""
Roadmap Manager — the brain of the SEO Intelligence Engine.

Reads the existing Excel roadmap, runs all analyzers against live
data, compares opportunities against roadmap tasks, and updates
the next 30 days of the roadmap with evidence-based adjustments.

Never deletes history. Never rewrites completed tasks. Only updates
pending tasks in the actionable window.
"""

import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from .backup_manager import BackupManager
from .excel_reader import ExcelReader, RoadmapTask
from .excel_updater import ExcelUpdater, CellUpdate
from .opportunity_detector import OpportunityDetector, SEOOpportunity
from .priority_engine import PriorityEngine
from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class RoadmapManager:
    def __init__(
        self,
        workbook_path: Path,
        data_dir: Path,
        website_root: str,
        output_dir: Path,
        backups_dir: Path,
        settings: dict,
    ):
        self._workbook_path = workbook_path
        self._data_dir = data_dir
        self._settings = settings

        self._backup_mgr = BackupManager(backups_dir)
        self._reader = ExcelReader(workbook_path)
        self._updater = ExcelUpdater(workbook_path)
        self._detector = OpportunityDetector(data_dir, website_root, settings)
        self._priority_engine = PriorityEngine(settings)
        self._report_gen = ReportGenerator(output_dir / "reports")

    def run(self, year: int | None = None, month: int | None = None) -> dict:
        """Execute the full intelligence + roadmap update cycle."""
        now = datetime.now()
        year = year or now.year
        month = month or now.month

        logger.info("=" * 60)
        logger.info("ROADMAP MANAGER — %d/%02d", year, month)
        logger.info("=" * 60)

        # 1. Backup before any changes
        backup_path = self._backup_mgr.create_backup(self._workbook_path)
        logger.info("Step 1: Backup → %s", backup_path.name)

        # 2. Read current roadmap
        roadmap_data = self._reader.read_all()
        tasks = roadmap_data["tasks"]
        done_tasks = [t for t in tasks if t.is_done()]
        pending_tasks = [t for t in tasks if t.is_pending()]
        logger.info(
            "Step 2: Read roadmap — %d tasks (%d done, %d pending)",
            len(tasks), len(done_tasks), len(pending_tasks),
        )

        # 3. Load live data
        combined_df = self._load_combined()
        queries_df = self._load_queries(year, month)
        logger.info(
            "Step 3: Loaded data — %d combined pages, %d query rows",
            len(combined_df), len(queries_df),
        )

        # 4. Run intelligence engine
        opportunities = self._detector.detect_all(combined_df, queries_df, year, month)
        ranked = self._priority_engine.score_and_rank(opportunities)
        logger.info("Step 4: Detected %d opportunities", len(ranked))

        # 5. Generate intelligence report
        report_path = self._report_gen.generate_intelligence_report(ranked, year, month)
        logger.info("Step 5: Report → %s", report_path.name)

        # 6. Compare opportunities against roadmap and queue updates
        updates = self._map_opportunities_to_tasks(ranked, pending_tasks, combined_df, queries_df)
        logger.info("Step 6: Queued %d cell updates", len(updates))

        # 7. Apply updates
        cells_modified = self._updater.apply_all()
        logger.info("Step 7: Applied %d cell updates to workbook", cells_modified)

        return {
            "backup": str(backup_path),
            "report": str(report_path),
            "tasks_total": len(tasks),
            "tasks_done": len(done_tasks),
            "tasks_pending": len(pending_tasks),
            "opportunities_detected": len(ranked),
            "cells_modified": cells_modified,
        }

    def _load_combined(self) -> pd.DataFrame:
        path = self._data_dir / "processed" / "combined_pages.csv"
        if path.exists():
            return pd.read_csv(path, encoding="utf-8")
        logger.warning("No combined_pages.csv found")
        return pd.DataFrame()

    def _load_queries(self, year: int, month: int) -> pd.DataFrame:
        path = self._data_dir / "search_console" / str(year) / f"{month:02d}" / "queries.csv"
        if path.exists():
            return pd.read_csv(path, encoding="utf-8")
        logger.warning("No queries.csv for %d/%02d", year, month)
        return pd.DataFrame()

    def _map_opportunities_to_tasks(
        self,
        opportunities: list[SEOOpportunity],
        pending_tasks: list[RoadmapTask],
        combined_df: pd.DataFrame,
        queries_df: pd.DataFrame,
    ) -> list[CellUpdate]:
        """Compare detected opportunities against pending roadmap tasks
        and queue evidence-based updates for the next 30 days."""
        next_30 = pending_tasks[:30]
        if not next_30:
            logger.info("No pending tasks to update")
            return []

        updates_count = 0
        timestamp = datetime.now().strftime("%Y-%m-%d")

        for task in next_30:
            evidence_notes = []
            title_lower = task.title.lower()
            detail_lower = task.detail.lower()

            # --- Match task against data evidence ---

            # Indexing tasks (Week 2): check GSC impressions
            if "index" in title_lower or "sitemap" in title_lower:
                indexed_pages = len(combined_df[combined_df["impressions"] > 0])
                total_pages = len(combined_df)
                evidence_notes.append(
                    f"[{timestamp}] GSC: {indexed_pages}/{total_pages} pages have search impressions"
                )

            # CTR/title/meta tasks: inject CTR data
            if any(w in title_lower for w in ["title", "meta description", "ctr"]):
                low_ctr = combined_df[
                    (combined_df["impressions"] >= 10) & (combined_df["ctr"] < 0.02)
                ]
                evidence_notes.append(
                    f"[{timestamp}] {len(low_ctr)} pages with CTR < 2% and 10+ impressions"
                )

            # Keyword tasks: inject keyword counts
            if any(w in title_lower for w in ["keyword", "queries", "gsc"]):
                if not queries_df.empty:
                    unique_q = queries_df["query"].nunique()
                    avg_pos = queries_df["position"].mean()
                    evidence_notes.append(
                        f"[{timestamp}] GSC: {unique_q} unique queries, avg position {avg_pos:.1f}"
                    )

            # Content tasks: inject engagement data
            if any(w in title_lower for w in ["blog", "content", "write", "publish"]):
                blog_pages = combined_df[combined_df["url"].str.contains("/blog/", na=False)]
                if not blog_pages.empty:
                    total_sessions = int(blog_pages["sessions"].sum())
                    avg_bounce = blog_pages["bounce_rate"].mean()
                    evidence_notes.append(
                        f"[{timestamp}] Blog: {total_sessions} total sessions, {avg_bounce:.0%} avg bounce"
                    )

            # Internal linking tasks
            if "internal link" in title_lower or "orphan" in title_lower:
                orphans = len(combined_df[combined_df["landing_page_status"] == "inactive"])
                direct_only = len(combined_df[combined_df["landing_page_status"] == "direct_only"])
                evidence_notes.append(
                    f"[{timestamp}] {orphans} inactive pages, {direct_only} direct-only pages"
                )

            # CTA / conversion tasks
            if any(w in title_lower for w in ["cta", "lead", "conversion", "contact"]):
                no_conv = len(combined_df[(combined_df["sessions"] > 5) & (combined_df["conversions"] == 0)])
                evidence_notes.append(
                    f"[{timestamp}] {no_conv} pages with 5+ sessions but 0 conversions"
                )

            # Performance tasks
            if any(w in title_lower for w in ["pagespeed", "performance", "core web"]):
                evidence_notes.append(
                    f"[{timestamp}] Run PageSpeed audit — data pending"
                )

            # E-E-A-T tasks
            if any(w in title_lower for w in ["e-e-a-t", "eeat", "author", "schema", "about"]):
                tech_issues = [
                    o for o in opportunities
                    if o.category == "technical" and "schema" in o.title.lower()
                ]
                evidence_notes.append(
                    f"[{timestamp}] {len(tech_issues)} pages with missing schema markup"
                )

            # Brand keyword tasks
            if "brand" in title_lower:
                brand_queries = queries_df[
                    queries_df["query"].str.contains("freemind|koelai", case=False, na=False)
                ] if not queries_df.empty else pd.DataFrame()
                if not brand_queries.empty:
                    brand_clicks = int(brand_queries["clicks"].sum())
                    brand_imp = int(brand_queries["impressions"].sum())
                    evidence_notes.append(
                        f"[{timestamp}] Brand: {brand_clicks} clicks, {brand_imp} impressions"
                    )

            # Check if any high-priority opportunities should boost this task
            matching_opps = self._find_matching_opportunities(task, opportunities)
            if matching_opps:
                top = matching_opps[0]
                evidence_notes.append(
                    f"[{timestamp}] TOP OPP: {top.title[:60]} (score: {top.priority_score:.0f})"
                )

            # Queue the notes update (append, don't overwrite)
            if evidence_notes:
                existing_notes = task.notes.strip()
                new_notes = "; ".join(evidence_notes)
                if existing_notes:
                    combined_notes = f"{existing_notes} | {new_notes}"
                else:
                    combined_notes = new_notes

                self._updater.queue_update(CellUpdate(
                    sheet="101-Day Roadmap",
                    row=task.row_number,
                    column="notes",
                    value=combined_notes[:500],  # Excel cell limit safety
                    reason="Data-driven evidence injection",
                ))
                updates_count += 1

        return self._updater.get_pending_changes()

    def _find_matching_opportunities(
        self,
        task: RoadmapTask,
        opportunities: list[SEOOpportunity],
    ) -> list[SEOOpportunity]:
        """Find opportunities that are relevant to a specific roadmap task."""
        matches = []
        title_lower = task.title.lower()
        detail_lower = task.detail.lower()

        for opp in opportunities[:50]:  # Only check top 50
            opp_lower = opp.title.lower()

            # Match by category relevance
            if opp.category == "keyword" and any(w in title_lower for w in ["keyword", "queries"]):
                matches.append(opp)
            elif opp.category == "ctr" and any(w in title_lower for w in ["title", "meta", "ctr"]):
                matches.append(opp)
            elif opp.category == "technical" and any(w in title_lower for w in ["schema", "canonical", "h1", "fix"]):
                matches.append(opp)
            elif opp.category == "page" and any(w in title_lower for w in ["content", "page", "blog"]):
                matches.append(opp)

        return sorted(matches, key=lambda x: x.priority_score, reverse=True)
