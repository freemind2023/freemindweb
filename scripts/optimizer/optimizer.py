"""
Main SEO Optimizer — orchestrates the complete pipeline from
website crawl → intelligence comparison → change planning →
implementation → validation → git review.

Never deploys automatically. All changes require explicit approval.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from scripts.website.crawler import WebsiteCrawler
from scripts.website.page_mapper import PageMapper
from scripts.website.component_detector import ComponentDetector
from scripts.website.internal_link_manager import InternalLinkManager
from scripts.website.deployment_validator import DeploymentValidator
from .change_planner import ChangePlanner, ImplementationPlan
from .implementation_engine import ImplementationEngine
from .validation_engine import ValidationEngine
from .rollback_manager import RollbackManager
from .git_manager import GitManager

logger = logging.getLogger(__name__)


class Optimizer:
    def __init__(
        self,
        website_root: str,
        data_dir: Path,
        output_dir: Path,
        backups_dir: Path,
    ):
        self._website_root = website_root
        self._data_dir = data_dir
        self._output_dir = output_dir
        self._backups_dir = backups_dir

        self._crawler = WebsiteCrawler(website_root)
        self._mapper = PageMapper()
        self._planner = ChangePlanner()
        self._engine = ImplementationEngine(backups_dir / "website_files")
        self._validator = ValidationEngine()
        self._rollback = RollbackManager(backups_dir / "website_files")
        self._git = GitManager(Path(website_root))

    def analyze(self) -> dict:
        """Phase 1: Crawl website and build intelligence report. No modifications."""
        logger.info("=" * 60)
        logger.info("SEO OPTIMIZER — ANALYSIS PHASE")
        logger.info("=" * 60)

        # 1. Crawl
        pages = self._crawler.crawl()
        inventory_path = self._output_dir / "website_inventory.json"
        self._crawler.save_inventory(inventory_path)

        # 2. Detect components
        detector = ComponentDetector()
        components = detector.detect(pages)

        # 3. Load SEO data
        combined_df = self._load_csv(self._data_dir / "processed" / "combined_pages.csv")
        queries_df = self._load_latest_queries()

        # 4. Build enriched profiles
        profiles = self._mapper.build_profiles(pages, combined_df, queries_df)

        # 5. Analyze internal links
        link_mgr = InternalLinkManager(pages)
        link_report = link_mgr.analyze()

        # 6. Create implementation plan
        plan = self._planner.create_plan(profiles)

        # 7. Save plan
        plan_path = self._output_dir / "implementation_plan.json"
        plan_path.write_text(
            json.dumps(plan.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # 8. Save profiles
        profiles_path = self._output_dir / "page_profiles.json"
        profiles_path.write_text(
            json.dumps([p.to_dict() for p in profiles], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        result = {
            "pages_crawled": len(pages),
            "components_detected": len(components),
            "profiles_built": len(profiles),
            "total_issues": sum(len(p.issues) for p in profiles),
            "planned_changes": plan.total_changes,
            "files_affected": plan.files_affected,
            "orphan_pages": len(link_report.orphan_pages),
            "internal_links": link_report.total_links,
            "inventory_path": str(inventory_path),
            "plan_path": str(plan_path),
            "profiles_path": str(profiles_path),
        }

        logger.info("")
        logger.info("ANALYSIS COMPLETE")
        logger.info("  Pages crawled:     %d", result["pages_crawled"])
        logger.info("  Issues found:      %d", result["total_issues"])
        logger.info("  Changes planned:   %d", result["planned_changes"])
        logger.info("  Files affected:    %d", result["files_affected"])
        logger.info("  Orphan pages:      %d", result["orphan_pages"])
        logger.info("")
        logger.info("Review the plan at: %s", plan_path)
        logger.info("NO CHANGES HAVE BEEN MADE. Run 'apply' to implement.")

        return result

    def apply(self, approve_all: bool = False) -> dict:
        """Phase 2: Apply approved changes from the plan."""
        plan_path = self._output_dir / "implementation_plan.json"
        if not plan_path.exists():
            logger.error("No implementation plan found. Run 'analyze' first.")
            return {"error": "No plan found"}

        plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
        plan = ImplementationPlan(**{
            k: v for k, v in plan_data.items() if k != "changes"
        })
        from .change_planner import PlannedChange
        plan.changes = [PlannedChange(**c) for c in plan_data["changes"]]

        if approve_all:
            plan.approve_all()
            logger.info("Auto-approved all %d changes", len(plan.changes))

        approved = plan.get_approved()
        if not approved:
            logger.info("No approved changes to apply.")
            return {"approved": 0, "applied": 0}

        logger.info("=" * 60)
        logger.info("SEO OPTIMIZER — IMPLEMENTATION PHASE")
        logger.info("=" * 60)
        logger.info("Applying %d approved changes...", len(approved))

        # Apply
        result = self._engine.apply_all_approved(approved)

        # Validate changed files
        changed_files = list(set(c.file_path for c in approved))
        validation = self._validator.validate_changed_files(changed_files)

        # Git review
        applied = self._engine.get_applied()
        if applied and self._git.is_repo():
            review = self._git.show_review(applied)
            logger.info("\n%s", review)

        result["validation"] = validation
        result["review"] = self._git.show_review(applied) if applied else ""

        # Save results
        results_path = self._output_dir / "optimization_results.json"
        results_path.write_text(
            json.dumps({
                "applied_at": datetime.now().isoformat(),
                "changes_applied": applied,
                "validation": validation,
                "summary": result,
            }, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.info("")
        logger.info("IMPLEMENTATION COMPLETE")
        logger.info("  Approved:   %d", result["approved"])
        logger.info("  Succeeded:  %d", result["succeeded"])
        logger.info("  Failed:     %d", result["failed"])
        logger.info("  Validation: %s", "PASS" if validation["can_deploy"] else "FAIL")
        logger.info("")
        logger.info("Review changes with 'git diff' before committing.")
        logger.info("To rollback: use the rollback manager.")

        return result

    def rollback(self) -> dict:
        """Rollback all recently changed files."""
        results_path = self._output_dir / "optimization_results.json"
        if not results_path.exists():
            return {"error": "No optimization results to rollback"}

        data = json.loads(results_path.read_text(encoding="utf-8"))
        files = [Path(c["file"]) for c in data.get("changes_applied", [])]
        return self._rollback.rollback_all(files)

    def _load_csv(self, path: Path) -> pd.DataFrame:
        if path.exists():
            return pd.read_csv(path, encoding="utf-8")
        return pd.DataFrame()

    def _load_latest_queries(self) -> pd.DataFrame:
        sc_dir = self._data_dir / "search_console"
        if not sc_dir.exists():
            return pd.DataFrame()
        years = sorted(sc_dir.iterdir(), reverse=True)
        for year_dir in years:
            months = sorted(year_dir.iterdir(), reverse=True)
            for month_dir in months:
                q_path = month_dir / "queries.csv"
                if q_path.exists():
                    return pd.read_csv(q_path, encoding="utf-8")
        return pd.DataFrame()
