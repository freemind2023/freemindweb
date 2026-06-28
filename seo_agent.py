#!/usr/bin/env python3
"""
SEO Agent — Autonomous SEO Operating System

Single command to execute the complete local SEO workflow:
  data collection → intelligence → roadmap update → website optimization

Usage:
    python seo_agent.py              # Interactive menu
    python seo_agent.py full         # Complete pipeline
    python seo_agent.py analyze      # Data + Intelligence (no changes)
    python seo_agent.py roadmap      # Update roadmap only
    python seo_agent.py optimize     # Website optimizer only
    python seo_agent.py validate     # Validate website only
    python seo_agent.py review       # Show pending git changes
    python seo_agent.py rollback     # Rollback last changes
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Project root
ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

from config import (
    PROJECT_ROOT, DATA_DIR, OUTPUT_DIR, BACKUPS_DIR, LOGS_DIR,
    WEBSITE_ROOT, GA4_PROPERTY_ID, SEARCH_CONSOLE_PROPERTY,
    SERVICE_ACCOUNT_FILE, SETTINGS, CREDENTIALS_DIR,
)

# ─── Logging ────────────────────────────────────────────────────────

def setup_logging():
    today = datetime.now()
    daily_dir = LOGS_DIR / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    monthly_dir = LOGS_DIR / "monthly"
    monthly_dir.mkdir(parents=True, exist_ok=True)
    errors_dir = LOGS_DIR / "errors"
    errors_dir.mkdir(parents=True, exist_ok=True)
    perf_dir = LOGS_DIR / "performance"
    perf_dir.mkdir(parents=True, exist_ok=True)

    daily_log = daily_dir / f"seo_agent_{today:%Y-%m-%d}.log"
    error_log = errors_dir / f"errors_{today:%Y-%m-%d}.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if not root_logger.handlers:
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s — %(message)s")

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(fmt)
        root_logger.addHandler(console)

        daily_handler = logging.FileHandler(daily_log, encoding="utf-8")
        daily_handler.setLevel(logging.INFO)
        daily_handler.setFormatter(fmt)
        root_logger.addHandler(daily_handler)

        err_handler = logging.FileHandler(error_log, encoding="utf-8")
        err_handler.setLevel(logging.ERROR)
        err_handler.setFormatter(fmt)
        root_logger.addHandler(err_handler)

    return logging.getLogger("seo_agent")


# ─── Display helpers ────────────────────────────────────────────────

BANNER = r"""
  ____  _____ ___       _                    _
 / ___|| ____/ _ \     / \   __ _  ___ _ __ | |_
 \___ \|  _|| | | |   / _ \ / _` |/ _ \ '_ \| __|
  ___) | |__| |_| |  / ___ \ (_| |  __/ | | | |_
 |____/|_____\___/  /_/   \_\__, |\___|_| |_|\__|
                             |___/
 Free Mind Consultancy — Autonomous SEO Operating System
"""


def header(title: str):
    print()
    print("=" * 64)
    print(f"  {title}")
    print("=" * 64)


def step(num: int, total: int, label: str):
    pct = int(num / total * 100)
    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
    print(f"\n  [{bar}] Step {num}/{total} — {label}")


def ok(msg: str):
    print(f"    [OK]   {msg}")


def warn(msg: str):
    print(f"    [WARN] {msg}")


def fail(msg: str):
    print(f"    [FAIL] {msg}")


def metric(label: str, value):
    print(f"    {label:30s} {value}")


# ─── Step 1: System Validation ──────────────────────────────────────

def validate_system(logger) -> bool:
    header("STEP 1 — SYSTEM VALIDATION")
    checks_passed = True

    # Config
    if GA4_PROPERTY_ID:
        ok(f"GA4 Property ID: {GA4_PROPERTY_ID}")
    else:
        fail("GA4_PROPERTY_ID not set in .env")
        checks_passed = False

    if SEARCH_CONSOLE_PROPERTY:
        ok(f"Search Console: {SEARCH_CONSOLE_PROPERTY}")
    else:
        fail("SEARCH_CONSOLE_PROPERTY not set in .env")
        checks_passed = False

    # Credentials
    sa_path = Path(SERVICE_ACCOUNT_FILE)
    if sa_path.exists():
        ok(f"Service account: {sa_path.name}")
    else:
        fail(f"Service account not found: {sa_path}")
        checks_passed = False

    # Website
    ws_path = Path(WEBSITE_ROOT)
    if ws_path.exists():
        html_count = len(list(ws_path.rglob("*.html")))
        ok(f"Website root: {ws_path} ({html_count} HTML files)")
    else:
        fail(f"Website root not found: {ws_path}")
        checks_passed = False

    # Roadmap
    wb_path = ROOT / "01_seo_audit_roadmap.xlsx"
    if wb_path.exists():
        ok(f"Roadmap: {wb_path.name}")
    else:
        fail(f"Roadmap not found: {wb_path}")
        checks_passed = False

    # Directories
    for d in [DATA_DIR, OUTPUT_DIR, BACKUPS_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # API connectivity
    try:
        from scripts.apis.analytics import GA4Client
        client = GA4Client(GA4_PROPERTY_ID, SERVICE_ACCOUNT_FILE)
        client.authenticate()
        ok("GA4 API connection verified")
    except Exception as e:
        fail(f"GA4 API: {e}")
        checks_passed = False

    try:
        from scripts.apis.search_console import SearchConsoleClient
        client = SearchConsoleClient(SEARCH_CONSOLE_PROPERTY, SERVICE_ACCOUNT_FILE)
        client.authenticate()
        ok("Search Console API connection verified")
    except Exception as e:
        fail(f"Search Console API: {e}")
        checks_passed = False

    if checks_passed:
        print("\n    All systems operational.")
    else:
        print("\n    Some checks failed. Fix the issues above before continuing.")

    return checks_passed


# ─── Step 2+3: Data Collection + Warehouse ──────────────────────────

def collect_data(logger) -> dict:
    header("STEP 2 — DATA COLLECTION")
    now = datetime.now()

    from scripts.fetch_ga4 import fetch_ga4_data
    from scripts.fetch_search_console import fetch_search_console_data
    from scripts.combine_data import combine_data

    print("    Fetching Google Analytics 4...")
    ga4_snap, ga4_paths = fetch_ga4_data(year=now.year, month=now.month)
    ok(f"GA4: {len(ga4_snap.landing_pages)} landing pages, {len(ga4_snap.traffic_sources)} sources")

    print("    Fetching Google Search Console...")
    gsc_snap, gsc_paths = fetch_search_console_data(year=now.year, month=now.month)
    ok(f"GSC: {len(gsc_snap.queries)} queries, {len(gsc_snap.pages)} pages")

    header("STEP 3 — HISTORICAL WAREHOUSE UPDATE")
    print("    Merging GA4 + GSC data...")
    result = combine_data(year=now.year, month=now.month)
    if result:
        combined_snap, combined_paths = result
        missing = combined_snap.missing_data_report()
        ok(f"Combined: {len(combined_snap.pages)} pages")
        ok(f"Archived to history/{now.year}/{now.month:02d}/")
        metric("Missing search data", f"{missing['pages_missing_search_data']} pages")
        metric("Missing analytics data", f"{missing['pages_missing_analytics_data']} pages")
    else:
        warn("No data to combine")
        combined_snap = None

    return {
        "ga4_landing_pages": len(ga4_snap.landing_pages),
        "ga4_traffic_sources": len(ga4_snap.traffic_sources),
        "gsc_queries": len(gsc_snap.queries),
        "gsc_pages": len(gsc_snap.pages),
        "combined_pages": len(combined_snap.pages) if combined_snap else 0,
    }


# ─── Step 4+5: Intelligence + Roadmap ──────────────────────────────

def run_intelligence(logger) -> dict:
    header("STEP 4 — SEO INTELLIGENCE ENGINE")

    from scripts.intelligence.roadmap_manager import RoadmapManager

    wb_path = ROOT / "01_seo_audit_roadmap.xlsx"
    manager = RoadmapManager(
        workbook_path=wb_path,
        data_dir=DATA_DIR,
        website_root=WEBSITE_ROOT,
        output_dir=OUTPUT_DIR,
        backups_dir=BACKUPS_DIR,
        settings=SETTINGS,
    )

    result = manager.run()

    ok(f"Opportunities detected: {result['opportunities_detected']}")
    ok(f"Report: {Path(result['report']).name}")

    header("STEP 5 — ROADMAP UPDATE")
    ok(f"Tasks: {result['tasks_total']} total ({result['tasks_done']} done, {result['tasks_pending']} pending)")
    ok(f"Cells modified: {result['cells_modified']}")
    ok(f"Backup: {Path(result['backup']).name}")

    return result


# ─── Step 6+7: Website Intelligence + Optimization Plan ────────────

def run_website_intelligence(logger) -> dict:
    header("STEP 6 — WEBSITE INTELLIGENCE")

    from scripts.optimizer.optimizer import Optimizer

    optimizer = Optimizer(
        website_root=WEBSITE_ROOT,
        data_dir=DATA_DIR,
        output_dir=OUTPUT_DIR,
        backups_dir=BACKUPS_DIR,
    )

    result = optimizer.analyze()

    ok(f"Pages crawled: {result['pages_crawled']}")
    ok(f"Issues found: {result['total_issues']}")
    ok(f"Orphan pages: {result['orphan_pages']}")
    ok(f"Internal links: {result['internal_links']}")

    header("STEP 7 — OPTIMIZATION PLAN")
    ok(f"Changes planned: {result['planned_changes']}")
    ok(f"Files affected: {result['files_affected']}")
    ok(f"Plan saved: {Path(result['plan_path']).name}")

    return result


# ─── Step 8: Interactive Approval ───────────────────────────────────

def interactive_approval(logger) -> str:
    header("STEP 8 — APPROVAL")

    plan_path = OUTPUT_DIR / "implementation_plan.json"
    if not plan_path.exists():
        warn("No implementation plan found. Run 'analyze' first.")
        return "skip"

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    total = plan["total_changes"]

    if total == 0:
        ok("No changes to approve.")
        return "skip"

    # Group by type
    by_type = {}
    for c in plan["changes"]:
        by_type.setdefault(c["change_type"], []).append(c)

    print(f"\n    {total} changes planned across {plan['files_affected']} files:\n")
    for ct, changes in sorted(by_type.items(), key=lambda x: -len(x[1])):
        print(f"      {ct:25s}  {len(changes):3d} changes")

    print("\n    Options:")
    print("      [A] Approve ALL changes")
    print("      [T] Approve by TYPE (choose which categories)")
    print("      [S] Skip — do not modify any files")
    print("      [Q] Quit")

    try:
        choice = input("\n    Your choice [A/T/S/Q]: ").strip().upper()
    except (EOFError, KeyboardInterrupt):
        choice = "S"

    if choice == "A":
        for c in plan["changes"]:
            c["approved"] = True
        plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
        ok(f"Approved all {total} changes")
        return "all"

    elif choice == "T":
        print("\n    Available types:")
        type_list = list(by_type.keys())
        for i, ct in enumerate(type_list, 1):
            print(f"      [{i}] {ct} ({len(by_type[ct])} changes)")

        try:
            nums = input("    Enter numbers (comma-separated): ").strip()
            selected = set()
            for n in nums.split(","):
                n = n.strip()
                if n.isdigit() and 1 <= int(n) <= len(type_list):
                    selected.add(type_list[int(n) - 1])

            approved_count = 0
            for c in plan["changes"]:
                if c["change_type"] in selected:
                    c["approved"] = True
                    approved_count += 1
            plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
            ok(f"Approved {approved_count} changes in categories: {', '.join(selected)}")
            return "partial"
        except (EOFError, KeyboardInterrupt):
            return "skip"

    elif choice == "Q":
        return "quit"
    else:
        ok("Skipped — no modifications will be made.")
        return "skip"


# ─── Step 9+10: Apply + Validate ───────────────────────────────────

def apply_and_validate(logger) -> dict:
    header("STEP 9 — APPLY APPROVED CHANGES")

    from scripts.optimizer.optimizer import Optimizer

    optimizer = Optimizer(
        website_root=WEBSITE_ROOT,
        data_dir=DATA_DIR,
        output_dir=OUTPUT_DIR,
        backups_dir=BACKUPS_DIR,
    )

    result = optimizer.apply(approve_all=False)  # Uses pre-approved plan

    ok(f"Approved: {result.get('approved', 0)}")
    ok(f"Succeeded: {result.get('succeeded', 0)}")
    if result.get("failed", 0) > 0:
        warn(f"Failed: {result['failed']}")

    header("STEP 10 — VALIDATION")
    validation = result.get("validation", {})
    if validation.get("can_deploy"):
        ok(f"Validation PASSED — {validation.get('passed', 0)} files clean")
    else:
        warn(f"Validation issues: {len(validation.get('errors', []))} errors, {len(validation.get('warnings', []))} warnings")
        for err in validation.get("errors", [])[:5]:
            warn(f"  {err}")

    return result


# ─── Step 11: Git Review ───────────────────────────────────────────

def git_review(logger) -> dict:
    header("STEP 11 — GIT REVIEW")

    from scripts.optimizer.git_manager import GitManager

    git = GitManager(Path(WEBSITE_ROOT))

    if not git.is_repo():
        warn("Website directory is not a git repository.")
        warn("Initialize with: git init")
        return {"is_repo": False}

    diff = git.get_diff()
    if diff.files_changed:
        ok(f"Files changed: {len(diff.files_changed)}")
        ok(f"Lines added:   +{diff.insertions}")
        ok(f"Lines removed: -{diff.deletions}")
        print()
        for f in diff.files_changed[:10]:
            print(f"      {f}")
        if len(diff.files_changed) > 10:
            print(f"      ... and {len(diff.files_changed) - 10} more")
        print()
        print("    Run 'git diff' to see full changes.")
        print("    Run 'git add . && git commit' to commit when ready.")
    else:
        ok("No uncommitted changes in website directory.")

    return diff.to_dict()


# ─── Final Summary ──────────────────────────────────────────────────

def print_summary(start_time: float, results: dict):
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    header("FINAL SUMMARY")

    data = results.get("data", {})
    intel = results.get("intelligence", {})
    website = results.get("website", {})
    apply_result = results.get("apply", {})

    metric("Execution time", f"{minutes}m {seconds}s")
    print()
    metric("GA4 landing pages", data.get("ga4_landing_pages", "—"))
    metric("GA4 traffic sources", data.get("ga4_traffic_sources", "—"))
    metric("GSC queries", data.get("gsc_queries", "—"))
    metric("GSC pages", data.get("gsc_pages", "—"))
    metric("Combined pages", data.get("combined_pages", "—"))
    print()
    metric("SEO opportunities detected", intel.get("opportunities_detected", "—"))
    metric("Roadmap cells updated", intel.get("cells_modified", "—"))
    metric("Roadmap tasks done", intel.get("tasks_done", "—"))
    metric("Roadmap tasks pending", intel.get("tasks_pending", "—"))
    print()
    metric("Website pages crawled", website.get("pages_crawled", "—"))
    metric("SEO issues detected", website.get("total_issues", "—"))
    metric("Changes planned", website.get("planned_changes", "—"))
    metric("Orphan pages", website.get("orphan_pages", "—"))
    print()
    if apply_result:
        metric("Changes applied", apply_result.get("succeeded", 0))
        metric("Changes failed", apply_result.get("failed", 0))
        val = apply_result.get("validation", {})
        metric("Validation", "PASS" if val.get("can_deploy") else "NEEDS REVIEW")
    print()
    metric("Roadmap backup", Path(intel.get("backup", "—")).name if intel.get("backup") else "—")
    metric("Intelligence report", Path(intel.get("report", "—")).name if intel.get("report") else "—")
    print()
    print("    Master roadmap: 01_seo_audit_roadmap.xlsx")
    print()


# ─── Command handlers ──────────────────────────────────────────────

def cmd_full(logger):
    """Complete pipeline — all 11 steps."""
    start = time.time()
    results = {}

    # Step 1
    if not validate_system(logger):
        print("\n  Aborting — fix validation errors above.")
        return 1

    # Steps 2-3
    results["data"] = collect_data(logger)

    # Steps 4-5
    results["intelligence"] = run_intelligence(logger)

    # Steps 6-7
    results["website"] = run_website_intelligence(logger)

    # Step 8
    approval = interactive_approval(logger)
    if approval == "quit":
        print("\n  Exiting.")
        return 0

    # Steps 9-10
    if approval in ("all", "partial"):
        results["apply"] = apply_and_validate(logger)
    else:
        ok("No changes applied (skipped).")
        results["apply"] = {}

    # Step 11
    git_review(logger)

    # Summary
    print_summary(start, results)
    return 0


def cmd_analyze(logger):
    """Data + Intelligence — no modifications."""
    start = time.time()
    results = {}

    if not validate_system(logger):
        return 1

    results["data"] = collect_data(logger)
    results["intelligence"] = run_intelligence(logger)
    results["website"] = run_website_intelligence(logger)

    print_summary(start, results)
    return 0


def cmd_roadmap(logger):
    """Update roadmap only (uses existing data)."""
    start = time.time()
    results = {"data": {}, "website": {}}

    results["intelligence"] = run_intelligence(logger)

    print_summary(start, results)
    return 0


def cmd_optimize(logger):
    """Website optimizer only."""
    start = time.time()
    results = {"data": {}, "intelligence": {}}

    results["website"] = run_website_intelligence(logger)
    approval = interactive_approval(logger)
    if approval in ("all", "partial"):
        results["apply"] = apply_and_validate(logger)

    print_summary(start, results)
    return 0


def cmd_validate(logger):
    """Validate website only."""
    header("WEBSITE VALIDATION")

    from scripts.optimizer.validation_engine import ValidationEngine
    engine = ValidationEngine()
    result = engine.full_site_validation(Path(WEBSITE_ROOT))

    ok(f"Files validated: {result['total_files']}")
    ok(f"Passed: {result['passed']}")
    if result["failed"] > 0:
        warn(f"Failed: {result['failed']}")
        for r in result["results"]:
            if not r["passed"]:
                for err in r["errors"]:
                    warn(f"  {r['file_path']}: {err}")
    return 0


def cmd_review(logger):
    """Show pending git changes."""
    git_review(logger)
    return 0


def cmd_rollback(logger):
    """Rollback last changes."""
    header("ROLLBACK")

    from scripts.optimizer.optimizer import Optimizer
    optimizer = Optimizer(
        website_root=WEBSITE_ROOT,
        data_dir=DATA_DIR,
        output_dir=OUTPUT_DIR,
        backups_dir=BACKUPS_DIR,
    )
    result = optimizer.rollback()
    if "error" in result:
        warn(result["error"])
    else:
        ok(f"Rolled back {result.get('succeeded', 0)} files")
    return 0


def cmd_interactive(logger):
    """Interactive menu."""
    print(BANNER)
    print("  Commands:")
    print("    [1] full      — Complete pipeline (all 11 steps)")
    print("    [2] analyze   — Data + Intelligence (read-only)")
    print("    [3] roadmap   — Update roadmap only")
    print("    [4] optimize  — Website optimizer")
    print("    [5] validate  — Validate website")
    print("    [6] review    — Git review")
    print("    [7] rollback  — Undo last changes")
    print("    [Q] quit")
    print()

    try:
        choice = input("  Select: ").strip()
    except (EOFError, KeyboardInterrupt):
        return 0

    commands = {
        "1": cmd_full, "full": cmd_full,
        "2": cmd_analyze, "analyze": cmd_analyze,
        "3": cmd_roadmap, "roadmap": cmd_roadmap,
        "4": cmd_optimize, "optimize": cmd_optimize,
        "5": cmd_validate, "validate": cmd_validate,
        "6": cmd_review, "review": cmd_review,
        "7": cmd_rollback, "rollback": cmd_rollback,
    }

    handler = commands.get(choice.lower())
    if handler:
        return handler(logger)
    elif choice.upper() == "Q":
        return 0
    else:
        print(f"  Unknown choice: {choice}")
        return 1


# ─── Main ───────────────────────────────────────────────────────────

def main():
    logger = setup_logging()
    print(BANNER)

    if len(sys.argv) < 2:
        return cmd_interactive(logger)

    command = sys.argv[1].lower()
    commands = {
        "full": cmd_full,
        "analyze": cmd_analyze,
        "roadmap": cmd_roadmap,
        "optimize": cmd_optimize,
        "validate": cmd_validate,
        "review": cmd_review,
        "rollback": cmd_rollback,
    }

    handler = commands.get(command)
    if handler:
        return handler(logger)
    else:
        print(f"  Unknown command: {command}")
        print("  Available: full, analyze, roadmap, optimize, validate, review, rollback")
        return 1


if __name__ == "__main__":
    sys.exit(main())
