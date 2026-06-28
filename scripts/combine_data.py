"""
Combine GA4 and Search Console data into a unified combined_pages.csv.

Loads the latest processed landing pages and search pages for the
current month, merges them by URL, and saves the combined dataset
to data/processed/combined_pages.csv with a historical archive.
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATA_DIR, LOGS_DIR, SETTINGS
from scripts.processors.merge_data import DataMerger

logger = logging.getLogger(__name__)


def setup_logging():
    log_file = LOGS_DIR / f"combine_data_{datetime.now():%Y-%m-%d}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def combine_data(year: int | None = None, month: int | None = None):
    """Load latest GA4 and GSC data for the month, merge, and save."""
    setup_logging()
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    merger = DataMerger(DATA_DIR)

    # Load processed data
    ga4_df = merger.load_latest_analytics(year, month)
    gsc_df = merger.load_latest_search_console(year, month)

    if ga4_df is None and gsc_df is None:
        logger.error(
            "No data found for %d/%02d. Run fetch_ga4.py and "
            "fetch_search_console.py first.",
            year, month,
        )
        return None

    if ga4_df is None:
        logger.warning("No GA4 data for %d/%02d — merging with GSC only", year, month)
        import pandas as pd
        ga4_df = pd.DataFrame(columns=["page_path"])

    if gsc_df is None:
        logger.warning("No GSC data for %d/%02d — merging with GA4 only", year, month)
        import pandas as pd
        gsc_df = pd.DataFrame(columns=["page"])

    lookback = SETTINGS.get("ga4", {}).get("default_lookback_days", 30)
    start_date = (now - timedelta(days=lookback)).strftime("%Y-%m-%d")
    end_date = now.strftime("%Y-%m-%d")

    snapshot = merger.merge(
        analytics_landing_pages=ga4_df,
        search_console_pages=gsc_df,
        start_date=start_date,
        end_date=end_date,
    )

    paths = merger.save_combined(snapshot, year=year, month=month)

    logger.info(
        "Data merge complete — %d combined pages saved to %s",
        len(snapshot.pages),
        paths["combined_csv"],
    )
    return snapshot, paths


if __name__ == "__main__":
    combine_data()
