"""
Tests for data model validation, serialization, and missing-data detection.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.data_models.analytics_model import AnalyticsSnapshot, LandingPageRow, TrafficSourceRow
from scripts.data_models.search_console_model import SearchConsoleSnapshot, SearchQueryRow, SearchPageRow
from scripts.data_models.combined_model import CombinedPageRow, CombinedSnapshot, COMBINED_COLUMNS


# --- Analytics Model ---

def test_landing_page_valid():
    lp = LandingPageRow(page_path="/", sessions=100, total_users=80, bounce_rate=0.4)
    assert lp.validate() == []


def test_landing_page_invalid_bounce():
    lp = LandingPageRow(page_path="/", bounce_rate=1.5)
    errors = lp.validate()
    assert any("bounce_rate" in e for e in errors)


def test_landing_page_empty_path():
    lp = LandingPageRow(page_path="")
    errors = lp.validate()
    assert any("page_path" in e for e in errors)


def test_analytics_snapshot_metadata():
    snap = AnalyticsSnapshot(
        property_id="123",
        start_date="2026-06-01",
        end_date="2026-06-28",
        landing_pages=[LandingPageRow(page_path="/")],
    )
    meta = snap.to_metadata()
    assert meta["source"] == "google_analytics_4"
    assert meta["property_id"] == "123"
    assert meta["landing_page_count"] == 1


def test_traffic_source_valid():
    ts = TrafficSourceRow(source="google", medium="organic", sessions=50)
    assert ts.validate() == []


def test_traffic_source_negative_sessions():
    ts = TrafficSourceRow(source="google", medium="cpc", sessions=-1)
    errors = ts.validate()
    assert any("sessions" in e for e in errors)


# --- Search Console Model ---

def test_search_query_valid():
    q = SearchQueryRow(query="seo tools", page="https://example.com/", clicks=10, impressions=100, ctr=0.1, position=5.2)
    assert q.validate() == []


def test_search_query_invalid_ctr():
    q = SearchQueryRow(query="test", page="/", ctr=2.0)
    errors = q.validate()
    assert any("ctr" in e for e in errors)


def test_search_page_aggregation():
    p = SearchPageRow(page="https://example.com/blog", clicks=50, impressions=1000, ctr=0.05, avg_position=8.3, query_count=15)
    assert p.validate() == []
    assert p.to_dict()["query_count"] == 15


def test_search_console_snapshot_metadata():
    snap = SearchConsoleSnapshot(
        site_url="sc-domain:example.com",
        start_date="2026-06-01",
        end_date="2026-06-28",
        queries=[SearchQueryRow(query="test", page="/")],
        pages=[SearchPageRow(page="/")],
        total_clicks=10,
        total_impressions=500,
    )
    meta = snap.to_metadata()
    assert meta["source"] == "google_search_console"
    assert meta["query_count"] == 1
    assert meta["page_count"] == 1


# --- Combined Model ---

def test_combined_page_active_status():
    p = CombinedPageRow(url="/", sessions=10, impressions=50, clicks=5)
    assert p.landing_page_status == "active"


def test_combined_page_indexed_no_traffic():
    p = CombinedPageRow(url="/old-page", sessions=0, impressions=100, clicks=2)
    assert p.landing_page_status == "indexed_no_traffic"


def test_combined_page_direct_only():
    p = CombinedPageRow(url="/internal", sessions=20, impressions=0)
    assert p.landing_page_status == "direct_only"


def test_combined_page_inactive():
    p = CombinedPageRow(url="/dead", sessions=0, impressions=0)
    assert p.landing_page_status == "inactive"


def test_combined_page_missing_fields():
    p = CombinedPageRow(url="/orphan", sessions=0, total_users=0, clicks=0, impressions=0)
    missing = p.missing_fields()
    assert "search_data" in missing
    assert "analytics_data" in missing


def test_combined_page_no_missing():
    p = CombinedPageRow(url="/", sessions=10, total_users=5, clicks=3, impressions=100)
    assert p.missing_fields() == []


def test_combined_snapshot_missing_report():
    snap = CombinedSnapshot(
        start_date="2026-06-01",
        end_date="2026-06-28",
        pages=[
            CombinedPageRow(url="/ok", sessions=10, clicks=5, impressions=100),
            CombinedPageRow(url="/no-search", sessions=10, clicks=0, impressions=0),
            CombinedPageRow(url="/no-analytics", sessions=0, total_users=0, clicks=5, impressions=50),
        ],
    )
    report = snap.missing_data_report()
    assert report["total_pages"] == 3
    assert report["pages_missing_search_data"] == 1
    assert report["pages_missing_analytics_data"] == 1


def test_combined_columns_match_model():
    p = CombinedPageRow(url="/test")
    d = p.to_dict()
    assert set(COMBINED_COLUMNS) == set(d.keys())


def test_combined_snapshot_validation_empty():
    snap = CombinedSnapshot(start_date="2026-06-01", end_date="2026-06-28", pages=[])
    errors = snap.validate()
    assert any("no pages" in e for e in errors)


def test_combined_snapshot_metadata_totals():
    snap = CombinedSnapshot(
        start_date="2026-06-01",
        end_date="2026-06-28",
        pages=[
            CombinedPageRow(url="/a", sessions=10, clicks=5, impressions=100),
            CombinedPageRow(url="/b", sessions=20, clicks=8, impressions=200),
        ],
    )
    meta = snap.to_metadata()
    assert meta["total_sessions"] == 30
    assert meta["total_clicks"] == 13
    assert meta["total_impressions"] == 300
