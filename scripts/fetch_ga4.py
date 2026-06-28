"""
Fetch data from Google Analytics 4 Data API.

Pulls key metrics and dimensions for the configured date range,
processes the response into structured landing page and traffic source
data, and saves raw JSON + processed CSVs + metadata to the
year/month warehouse structure.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import GA4_PROPERTY_ID, SERVICE_ACCOUNT_FILE, DATA_DIR, LOGS_DIR, SETTINGS
from scripts.apis.analytics import GA4Client
from scripts.processors.analytics_processor import AnalyticsProcessor

logger = logging.getLogger(__name__)


def setup_logging():
    log_file = LOGS_DIR / f"fetch_ga4_{datetime.now():%Y-%m-%d}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def fetch_ga4_data(year: int | None = None, month: int | None = None):
    """Fetch GA4 data, process it, and save to the warehouse."""
    setup_logging()
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    ga4_settings = SETTINGS.get("ga4", {})
    lookback = ga4_settings.get("default_lookback_days", 30)
    metrics = ga4_settings.get("metrics", ["sessions", "totalUsers"])
    dimensions = ga4_settings.get("dimensions", ["pagePath"])

    client = GA4Client(
        property_id=GA4_PROPERTY_ID,
        service_account_file=SERVICE_ACCOUNT_FILE,
    )
    client.authenticate()

    start_date = f"{lookback}daysAgo"
    end_date = "today"
    logger.info("Fetching GA4 data — last %d days", lookback)

    # Paginate through all results
    all_rows = []
    offset = 0
    row_limit = 10_000

    while True:
        response = client.run_report(
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
            dimensions=dimensions,
            row_limit=row_limit,
            offset=offset,
        )

        dim_headers = [h.name for h in response.dimension_headers]
        met_headers = [h.name for h in response.metric_headers]

        batch = []
        for row in response.rows:
            entry = {}
            for i, dv in enumerate(row.dimension_values):
                entry[dim_headers[i]] = dv.value
            for i, mv in enumerate(row.metric_values):
                entry[met_headers[i]] = mv.value
            batch.append(entry)

        all_rows.extend(batch)

        if len(batch) < row_limit:
            break
        offset += row_limit

    logger.info("Fetched %d total rows from GA4", len(all_rows))

    # Resolve actual date strings for the snapshot
    actual_start = (now - __import__("datetime").timedelta(days=lookback)).strftime("%Y-%m-%d")
    actual_end = now.strftime("%Y-%m-%d")

    # Process into structured snapshot
    processor = AnalyticsProcessor(DATA_DIR)
    snapshot = processor.process_response(
        raw_rows=all_rows,
        property_id=GA4_PROPERTY_ID,
        start_date=actual_start,
        end_date=actual_end,
        dim_headers=dim_headers if all_rows else [],
        met_headers=met_headers if all_rows else [],
    )

    # Save to warehouse
    paths = processor.save_snapshot(
        snapshot=snapshot,
        raw_response=all_rows,
        year=year,
        month=month,
    )

    logger.info(
        "GA4 fetch complete — %d landing pages, %d traffic sources",
        len(snapshot.landing_pages),
        len(snapshot.traffic_sources),
    )
    return snapshot, paths


if __name__ == "__main__":
    fetch_ga4_data()
