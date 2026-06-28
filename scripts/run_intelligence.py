"""
Run the SEO Intelligence Engine + Roadmap Update pipeline.

Executes:
1. Load all data from the warehouse
2. Run all analyzers (keyword, page, CTR, trends, technical)
3. Score and rank opportunities
4. Back up the roadmap workbook
5. Update the next 30 days with evidence
6. Save intelligence report
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATA_DIR, OUTPUT_DIR, BACKUPS_DIR, LOGS_DIR, WEBSITE_ROOT, SETTINGS
from scripts.intelligence.roadmap_manager import RoadmapManager

WORKBOOK_PATH = Path(__file__).parent.parent / "01_seo_audit_roadmap.xlsx"


def setup_logging():
    log_file = LOGS_DIR / f"intelligence_{datetime.now():%Y-%m-%d}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def main():
    setup_logging()
    logger = logging.getLogger("intelligence")

    logger.info("SEO Intelligence Engine — Starting")

    if not WORKBOOK_PATH.exists():
        logger.error("Roadmap workbook not found: %s", WORKBOOK_PATH)
        return 1

    manager = RoadmapManager(
        workbook_path=WORKBOOK_PATH,
        data_dir=DATA_DIR,
        website_root=WEBSITE_ROOT,
        output_dir=OUTPUT_DIR,
        backups_dir=BACKUPS_DIR,
        settings=SETTINGS,
    )

    result = manager.run()

    logger.info("")
    logger.info("=" * 60)
    logger.info("INTELLIGENCE ENGINE COMPLETE")
    logger.info("=" * 60)
    logger.info("Backup:              %s", result["backup"])
    logger.info("Report:              %s", result["report"])
    logger.info("Tasks total:         %d", result["tasks_total"])
    logger.info("Tasks done:          %d", result["tasks_done"])
    logger.info("Tasks pending:       %d", result["tasks_pending"])
    logger.info("Opportunities found: %d", result["opportunities_detected"])
    logger.info("Cells modified:      %d", result["cells_modified"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
