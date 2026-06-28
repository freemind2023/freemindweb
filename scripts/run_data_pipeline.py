"""
Run the full data pipeline: fetch GA4 + GSC, then merge into combined_pages.csv.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.fetch_ga4 import fetch_ga4_data
from scripts.fetch_search_console import fetch_search_console_data
from scripts.combine_data import combine_data


def main():
    print("=== STEP 1: Fetch GA4 ===")
    ga4_snap, ga4_paths = fetch_ga4_data()
    print(f"  Landing pages: {len(ga4_snap.landing_pages)}")
    print(f"  Traffic sources: {len(ga4_snap.traffic_sources)}")
    print()

    print("=== STEP 2: Fetch Search Console ===")
    gsc_snap, gsc_paths = fetch_search_console_data()
    print(f"  Queries: {len(gsc_snap.queries)}")
    print(f"  Pages: {len(gsc_snap.pages)}")
    print()

    print("=== STEP 3: Combine Data ===")
    result = combine_data()
    if result:
        combined_snap, combined_paths = result
        print(f"  Combined pages: {len(combined_snap.pages)}")
        print(f"  Output: {combined_paths['combined_csv']}")
        missing = combined_snap.missing_data_report()
        print(f"  Missing search data: {missing['pages_missing_search_data']}")
        print(f"  Missing analytics data: {missing['pages_missing_analytics_data']}")
    else:
        print("  No data to combine.")

    print()
    print("=== PIPELINE COMPLETE ===")


if __name__ == "__main__":
    main()
