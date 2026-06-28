"""
Fetch data from Google Search Console API.

Pulls search performance data with pagination, processes the response
into structured query and page-level data, and saves raw JSON +
processed CSVs + metadata to the year/month warehouse structure.
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import SEARCH_CONSOLE_PROPERTY, SERVICE_ACCOUNT_FILE, DATA_DIR, LOGS_DIR, SETTINGS
from scripts.apis.search_console import SearchConsoleClient
from scripts.processors.search_console_processor import SearchConsoleProcessor

logger = logging.getLogger(__name__)


def setup_logging():
    log_file = LOGS_DIR / f"fetch_search_console_{datetime.now():%Y-%m-%d}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def fetch_search_console_data(year: int | None = None, month: int | None = None):
    """Fetch Search Console data, process it, and save to the warehouse."""
    setup_logging()
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    sc_settings = SETTINGS.get("search_console", {})
    lookback = sc_settings.get("default_lookback_days", 30)
    row_limit = sc_settings.get("row_limit", 5000)
    dimensions = sc_settings.get("dimensions", ["query", "page"])

    end_date = now - timedelta(days=3)  # GSC data lags ~3 days
    start_date = end_date - timedelta(days=lookback)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    client = SearchConsoleClient(
        site_url=SEARCH_CONSOLE_PROPERTY,
        service_account_file=SERVICE_ACCOUNT_FILE,
    )
    client.authenticate()

    logger.info("Fetching Search Console data — %s to %s", start_str, end_str)

    # Paginate through all results
    all_rows = []
    start_row = 0

    while True:
        response = client.query(
            start_date=start_str,
            end_date=end_str,
            dimensions=dimensions,
            row_limit=row_limit,
            start_row=start_row,
        )

        rows = response.get("rows", [])
        if not rows:
            break

        all_rows.extend(rows)

        if len(rows) < row_limit:
            break
        start_row += row_limit

    logger.info("Fetched %d total rows from Search Console", len(all_rows))

    # Process into structured snapshot
    processor = SearchConsoleProcessor(DATA_DIR)
    snapshot = processor.process_response(
        raw_rows=all_rows,
        site_url=SEARCH_CONSOLE_PROPERTY,
        start_date=start_str,
        end_date=end_str,
        dimensions=dimensions,
    )

    # Save to warehouse
    paths = processor.save_snapshot(
        snapshot=snapshot,
        raw_response=all_rows,
        year=year,
        month=month,
    )

    logger.info(
        "Search Console fetch complete — %d queries, %d pages",
        len(snapshot.queries),
        len(snapshot.pages),
    )
    return snapshot, paths


if __name__ == "__main__":
    fetch_search_console_data()
