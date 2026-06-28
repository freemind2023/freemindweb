"""
Tests for data processors — analytics, search console, and merge.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import pytest

from scripts.processors.analytics_processor import AnalyticsProcessor
from scripts.processors.search_console_processor import SearchConsoleProcessor
from scripts.processors.merge_data import DataMerger


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create a temporary data directory structure."""
    for sub in ["analytics", "search_console", "processed", "history", "cache"]:
        (tmp_path / sub).mkdir()
    return tmp_path


# --- Analytics Processor ---

class TestAnalyticsProcessor:
    def test_process_empty_response(self, tmp_data_dir):
        proc = AnalyticsProcessor(tmp_data_dir)
        snap = proc.process_response(
            raw_rows=[],
            property_id="123",
            start_date="2026-06-01",
            end_date="2026-06-28",
            dim_headers=[],
            met_headers=[],
        )
        assert snap.row_count == 0
        assert len(snap.landing_pages) == 0
        assert len(snap.traffic_sources) == 0

    def test_process_rows_aggregates_by_page(self, tmp_data_dir):
        rows = [
            {"pagePath": "/", "sessionSource": "google", "sessionMedium": "organic",
             "sessions": "50", "totalUsers": "40", "newUsers": "20",
             "bounceRate": "0.3", "averageSessionDuration": "120",
             "screenPageViews": "80", "conversions": "5"},
            {"pagePath": "/", "sessionSource": "direct", "sessionMedium": "(none)",
             "sessions": "30", "totalUsers": "25", "newUsers": "10",
             "bounceRate": "0.5", "averageSessionDuration": "60",
             "screenPageViews": "40", "conversions": "2"},
        ]
        proc = AnalyticsProcessor(tmp_data_dir)
        snap = proc.process_response(
            raw_rows=rows,
            property_id="123",
            start_date="2026-06-01",
            end_date="2026-06-28",
            dim_headers=["pagePath", "sessionSource", "sessionMedium"],
            met_headers=["sessions", "totalUsers", "newUsers", "bounceRate",
                         "averageSessionDuration", "screenPageViews", "conversions"],
        )
        assert len(snap.landing_pages) == 1
        lp = snap.landing_pages[0]
        assert lp.page_path == "/"
        assert lp.sessions == 80
        assert lp.conversions == 7
        assert len(snap.traffic_sources) == 2

    def test_save_creates_warehouse_files(self, tmp_data_dir):
        proc = AnalyticsProcessor(tmp_data_dir)
        snap = proc.process_response(
            raw_rows=[{"pagePath": "/test", "sessions": "10", "totalUsers": "8"}],
            property_id="123",
            start_date="2026-06-01",
            end_date="2026-06-28",
            dim_headers=["pagePath"],
            met_headers=["sessions", "totalUsers"],
        )
        paths = proc.save_snapshot(snap, [{"pagePath": "/test"}], year=2026, month=6)
        assert paths["raw"].exists()
        assert paths["landing_pages"].exists()
        assert paths["traffic_sources"].exists()
        assert paths["metadata"].exists()
        # Verify warehouse path structure
        assert "2026" in str(paths["raw"])
        assert "06" in str(paths["raw"])

    def test_no_overwrite(self, tmp_data_dir):
        proc = AnalyticsProcessor(tmp_data_dir)
        snap = proc.process_response([], "123", "2026-06-01", "2026-06-28", [], [])
        paths1 = proc.save_snapshot(snap, [], year=2026, month=6)
        paths2 = proc.save_snapshot(snap, [], year=2026, month=6)
        assert paths1["raw"] != paths2["raw"]
        assert paths1["raw"].exists()
        assert paths2["raw"].exists()


# --- Search Console Processor ---

class TestSearchConsoleProcessor:
    def test_process_empty_response(self, tmp_data_dir):
        proc = SearchConsoleProcessor(tmp_data_dir)
        snap = proc.process_response(
            raw_rows=[],
            site_url="sc-domain:example.com",
            start_date="2026-06-01",
            end_date="2026-06-28",
            dimensions=["query", "page"],
        )
        assert snap.row_count == 0
        assert len(snap.queries) == 0
        assert len(snap.pages) == 0

    def test_process_aggregates_by_page(self, tmp_data_dir):
        rows = [
            {"keys": ["seo tools", "https://example.com/"], "clicks": 10, "impressions": 200, "ctr": 0.05, "position": 5.0},
            {"keys": ["seo guide", "https://example.com/"], "clicks": 5, "impressions": 100, "ctr": 0.05, "position": 8.0},
            {"keys": ["marketing", "https://example.com/blog"], "clicks": 3, "impressions": 50, "ctr": 0.06, "position": 12.0},
        ]
        proc = SearchConsoleProcessor(tmp_data_dir)
        snap = proc.process_response(
            raw_rows=rows,
            site_url="sc-domain:example.com",
            start_date="2026-06-01",
            end_date="2026-06-28",
            dimensions=["query", "page"],
        )
        assert len(snap.queries) == 3
        assert len(snap.pages) == 2
        homepage = next(p for p in snap.pages if p.page == "https://example.com/")
        assert homepage.clicks == 15
        assert homepage.impressions == 300
        assert homepage.query_count == 2

    def test_save_creates_warehouse_files(self, tmp_data_dir):
        proc = SearchConsoleProcessor(tmp_data_dir)
        snap = proc.process_response(
            raw_rows=[{"keys": ["test", "/"], "clicks": 1, "impressions": 10, "ctr": 0.1, "position": 3.0}],
            site_url="sc-domain:example.com",
            start_date="2026-06-01",
            end_date="2026-06-28",
            dimensions=["query", "page"],
        )
        paths = proc.save_snapshot(snap, [{"keys": ["test", "/"]}], year=2026, month=6)
        assert paths["raw"].exists()
        assert paths["queries"].exists()
        assert paths["pages"].exists()
        assert paths["metadata"].exists()


# --- Data Merger ---

class TestDataMerger:
    def test_normalize_url(self):
        assert DataMerger.normalize_url("https://example.com/blog/") == "/blog"
        assert DataMerger.normalize_url("https://example.com/") == "/"
        assert DataMerger.normalize_url("/Blog/Post") == "/blog/post"
        assert DataMerger.normalize_url("/") == "/"

    def test_merge_full_match(self, tmp_data_dir):
        ga4_df = pd.DataFrame([
            {"page_path": "/", "sessions": 100, "total_users": 80, "new_users": 30,
             "bounce_rate": 0.4, "avg_session_duration": 120, "screen_page_views": 150,
             "engagement_rate": 0.6, "conversions": 5},
        ])
        gsc_df = pd.DataFrame([
            {"page": "https://example.com/", "clicks": 50, "impressions": 1000,
             "ctr": 0.05, "avg_position": 6.2, "query_count": 20},
        ])
        merger = DataMerger(tmp_data_dir)
        snap = merger.merge(ga4_df, gsc_df, "2026-06-01", "2026-06-28")
        assert len(snap.pages) == 1
        p = snap.pages[0]
        assert p.url == "/"
        assert p.sessions == 100
        assert p.clicks == 50
        assert p.landing_page_status == "active"

    def test_merge_partial_ga4_only(self, tmp_data_dir):
        ga4_df = pd.DataFrame([
            {"page_path": "/internal", "sessions": 20, "total_users": 15},
        ])
        gsc_df = pd.DataFrame(columns=["page", "clicks", "impressions", "ctr", "avg_position"])
        merger = DataMerger(tmp_data_dir)
        snap = merger.merge(ga4_df, gsc_df, "2026-06-01", "2026-06-28")
        assert len(snap.pages) == 1
        assert snap.pages[0].landing_page_status == "direct_only"
        assert "search_data" in snap.pages[0].missing_fields()

    def test_merge_partial_gsc_only(self, tmp_data_dir):
        ga4_df = pd.DataFrame(columns=["page_path", "sessions", "total_users"])
        gsc_df = pd.DataFrame([
            {"page": "https://example.com/indexed", "clicks": 10, "impressions": 500,
             "ctr": 0.02, "avg_position": 15.0},
        ])
        merger = DataMerger(tmp_data_dir)
        snap = merger.merge(ga4_df, gsc_df, "2026-06-01", "2026-06-28")
        assert len(snap.pages) == 1
        assert snap.pages[0].landing_page_status == "indexed_no_traffic"
        assert "analytics_data" in snap.pages[0].missing_fields()

    def test_save_combined_creates_files(self, tmp_data_dir):
        snap = __import__("scripts.data_models.combined_model", fromlist=["CombinedSnapshot", "CombinedPageRow"])
        combined_snap = snap.CombinedSnapshot(
            start_date="2026-06-01",
            end_date="2026-06-28",
            pages=[snap.CombinedPageRow(url="/", sessions=10, clicks=5, impressions=100)],
        )
        merger = DataMerger(tmp_data_dir)
        paths = merger.save_combined(combined_snap, year=2026, month=6)
        assert paths["combined_csv"].exists()
        assert paths["metadata"].exists()
        assert paths["history_csv"].exists()
        # Verify CSV content
        df = pd.read_csv(paths["combined_csv"])
        assert len(df) == 1
        assert "url" in df.columns
        assert "landing_page_status" in df.columns

    def test_save_combined_no_overwrite_history(self, tmp_data_dir):
        from scripts.data_models.combined_model import CombinedSnapshot, CombinedPageRow
        snap = CombinedSnapshot(
            start_date="2026-06-01", end_date="2026-06-28",
            pages=[CombinedPageRow(url="/")],
        )
        merger = DataMerger(tmp_data_dir)
        p1 = merger.save_combined(snap, year=2026, month=6)
        p2 = merger.save_combined(snap, year=2026, month=6)
        assert p1["history_csv"] != p2["history_csv"]
        assert p1["history_csv"].exists()
        assert p2["history_csv"].exists()
