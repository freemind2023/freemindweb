"""
Run the full SEO analysis pipeline.

Orchestrates all scripts in sequence: fetch data, combine, analyze,
and generate reports. Reads the pipeline step order from settings.yaml.
Logs each step's status and handles errors gracefully so one failure
doesn't block the remaining steps.
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LOGS_DIR, SETTINGS

STEP_MODULES = {
    "fetch_ga4": "scripts.fetch_ga4",
    "fetch_search_console": "scripts.fetch_search_console",
    "combine_data": "scripts.combine_data",
    "keyword_analysis": "scripts.keyword_analysis",
    "page_analysis": "scripts.page_analysis",
    "technical_audit": "scripts.technical_audit",
    "generate_monthly_report": "scripts.generate_monthly_report",
}


def setup_logging():
    """Configure logging for the pipeline run."""
    log_file = LOGS_DIR / f"pipeline_{datetime.now().strftime('%Y-%m-%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger("pipeline")


def run_pipeline():
    """Execute all pipeline steps in order."""
    logger = setup_logging()
    steps = SETTINGS.get("pipeline", {}).get("steps", list(STEP_MODULES.keys()))

    logger.info("Starting SEO pipeline with %d steps", len(steps))

    results = {}
    for step in steps:
        logger.info("Running step: %s", step)
        try:
            # TODO: Import and execute each step module's main function
            # module = importlib.import_module(STEP_MODULES[step])
            # module.main()
            logger.warning("Step '%s' not yet implemented — skipping", step)
            results[step] = "skipped"
        except Exception as e:
            logger.error("Step '%s' failed: %s", step, e)
            results[step] = f"failed: {e}"

    logger.info("Pipeline complete. Results: %s", results)
    return results


if __name__ == "__main__":
    run_pipeline()
