"""
Tests for the SEO Intelligence Engine.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import pytest

from scripts.intelligence.keyword_analyzer import KeywordAnalyzer, KeywordOpportunity
from scripts.intelligence.page_analyzer import PageAnalyzer, PageIssue
from scripts.intelligence.ctr_analyzer import CTRAnalyzer, CTROpportunity
from scripts.intelligence.trend_analyzer import TrendAnalyzer, Trend
from scripts.intelligence.priority_engine import PriorityEngine
from scripts.intelligence.opportunity_detector import OpportunityDetector, SEOOpportunity
from scripts.intelligence.excel_reader import ExcelReader
from scripts.intelligence.backup_manager import BackupManager


SETTINGS = {
    "analysis": {
        "min_impressions": 5,
        "low_ctr_threshold": 0.02,
        "striking_distance_min_position": 4,
        "striking_distance_max_position": 20,
        "min_content_word_count": 800,
    }
}


@pytest.fixture
def sample_queries():
    return pd.DataFrame([
        {"query": "how to publish a book in india", "page": "https://example.com/blog/publish", "clicks": 0, "impressions": 80, "ctr": 0.0, "position": 75.0, "country": "ind", "device": "DESKTOP"},
        {"query": "isbn registration india", "page": "https://example.com/blog/isbn", "clicks": 0, "impressions": 35, "ctr": 0.0, "position": 10.0, "country": "ind", "device": "DESKTOP"},
        {"query": "meme marketing india", "page": "https://example.com/meme/", "clicks": 0, "impressions": 11, "ctr": 0.0, "position": 54.0, "country": "ind", "device": "DESKTOP"},
        {"query": "freemind consultants", "page": "https://example.com/", "clicks": 3, "impressions": 5, "ctr": 0.6, "position": 2.0, "country": "ind", "device": "DESKTOP"},
        {"query": "google ads for doctors pune", "page": "https://example.com/clinic/", "clicks": 0, "impressions": 8, "ctr": 0.0, "position": 7.0, "country": "ind", "device": "MOBILE"},
    ])


@pytest.fixture
def sample_combined():
    return pd.DataFrame([
        {"url": "/", "clicks": 4, "impressions": 282, "ctr": 0.014, "avg_position": 6.4,
         "sessions": 76, "total_users": 58, "new_users": 46, "bounce_rate": 0.64,
         "avg_session_duration": 55.0, "screen_page_views": 103, "engagement_rate": 0.36,
         "conversions": 0, "landing_page_status": "active", "last_updated": "2026-06-28"},
        {"url": "/blog/isbn", "clicks": 0, "impressions": 35, "ctr": 0.0, "avg_position": 28.0,
         "sessions": 10, "total_users": 10, "new_users": 2, "bounce_rate": 0.5,
         "avg_session_duration": 20.0, "screen_page_views": 24, "engagement_rate": 0.5,
         "conversions": 0, "landing_page_status": "active", "last_updated": "2026-06-28"},
        {"url": "/dead-page", "clicks": 0, "impressions": 0, "ctr": 0.0, "avg_position": 0.0,
         "sessions": 0, "total_users": 0, "new_users": 0, "bounce_rate": 0.0,
         "avg_session_duration": 0.0, "screen_page_views": 0, "engagement_rate": 0.0,
         "conversions": 0, "landing_page_status": "inactive", "last_updated": "2026-06-28"},
    ])


# --- Keyword Analyzer ---

class TestKeywordAnalyzer:
    def test_find_striking_distance(self, sample_queries):
        analyzer = KeywordAnalyzer(Path("."), SETTINGS)
        opps = analyzer.analyze(sample_queries)
        striking = [o for o in opps if o.opportunity_type == "striking_distance"]
        assert len(striking) >= 1
        # isbn at position 10 with 35 impressions should be detected
        isbn_opp = [o for o in striking if "isbn" in o.query]
        assert len(isbn_opp) >= 1

    def test_brand_detection(self):
        assert KeywordAnalyzer._is_brand("freemind consultants") is True
        assert KeywordAnalyzer._is_brand("koelai ai platform") is True
        assert KeywordAnalyzer._is_brand("how to publish a book") is False

    def test_brand_not_ranking(self):
        queries = pd.DataFrame([
            {"query": "freemind consulting", "page": "https://example.com/", "clicks": 0,
             "impressions": 10, "ctr": 0.0, "position": 8.0, "country": "ind", "device": "DESKTOP"},
        ])
        analyzer = KeywordAnalyzer(Path("."), SETTINGS)
        opps = analyzer.analyze(queries)
        brand_opps = [o for o in opps if o.opportunity_type == "brand_not_ranking"]
        assert len(brand_opps) >= 1

    def test_intent_classification(self):
        assert KeywordAnalyzer._classify_intent("how to publish a book") == "informational"
        assert KeywordAnalyzer._classify_intent("best meme marketing company") == "commercial"
        assert KeywordAnalyzer._classify_intent("freemind consultants") == "navigational"

    def test_empty_queries(self):
        analyzer = KeywordAnalyzer(Path("."), SETTINGS)
        result = analyzer.analyze(pd.DataFrame())
        assert result == []


# --- Page Analyzer ---

class TestPageAnalyzer:
    def test_detect_no_conversions(self, sample_combined):
        analyzer = PageAnalyzer(Path("."), ".", SETTINGS)
        issues = analyzer.analyze_combined(sample_combined)
        no_conv = [i for i in issues if i.issue_type == "no_conversions"]
        assert len(no_conv) >= 1

    def test_detect_orphan(self, sample_combined):
        analyzer = PageAnalyzer(Path("."), ".", SETTINGS)
        issues = analyzer.analyze_combined(sample_combined)
        orphans = [i for i in issues if i.issue_type == "orphan_page"]
        assert len(orphans) == 1
        assert orphans[0].url == "/dead-page"

    def test_detect_poor_engagement(self, sample_combined):
        analyzer = PageAnalyzer(Path("."), ".", SETTINGS)
        issues = analyzer.analyze_combined(sample_combined)
        poor = [i for i in issues if i.issue_type == "poor_engagement"]
        # homepage has 0.64 bounce — below 0.7 threshold, so should not trigger
        # (only > 0.7 triggers)
        assert all(i.url != "/dead-page" for i in poor)


# --- CTR Analyzer ---

class TestCTRAnalyzer:
    def test_find_ctr_gaps(self, sample_combined, sample_queries):
        analyzer = CTRAnalyzer(Path("."), SETTINGS)
        opps = analyzer.analyze(sample_combined, sample_queries)
        # Homepage: position 6.4, CTR 1.4% vs expected ~5% — should be detected
        homepage = [o for o in opps if o.url == "/"]
        assert len(homepage) >= 1

    def test_empty_data(self):
        analyzer = CTRAnalyzer(Path("."), SETTINGS)
        result = analyzer.analyze(pd.DataFrame(), pd.DataFrame())
        assert result == []


# --- Priority Engine ---

class TestPriorityEngine:
    def test_scoring(self):
        engine = PriorityEngine(SETTINGS)
        opps = [
            SEOOpportunity(id=1, category="keyword", title="test1", detail="",
                priority_score=0, business_impact="high", seo_impact="high",
                difficulty="easy", estimated_traffic_gain=50, estimated_lead_gain=3,
                estimated_time="30 min", confidence=0.9, evidence="", affected_pages=[]),
            SEOOpportunity(id=2, category="technical", title="test2", detail="",
                priority_score=0, business_impact="low", seo_impact="low",
                difficulty="hard", estimated_traffic_gain=1, estimated_lead_gain=0,
                estimated_time="60 min", confidence=0.5, evidence="", affected_pages=[]),
        ]
        ranked = engine.score_and_rank(opps)
        assert ranked[0].title == "test1"
        assert ranked[0].priority_score > ranked[1].priority_score

    def test_top_n(self):
        engine = PriorityEngine(SETTINGS)
        opps = [
            SEOOpportunity(id=i, category="keyword", title=f"test{i}", detail="",
                priority_score=0, business_impact="medium", seo_impact="medium",
                difficulty="medium", estimated_traffic_gain=i, estimated_lead_gain=0,
                estimated_time="15 min", confidence=0.5, evidence="", affected_pages=[])
            for i in range(20)
        ]
        top = engine.get_top_n(opps, n=5)
        assert len(top) == 5


# --- Backup Manager ---

class TestBackupManager:
    def test_create_and_list(self, tmp_path):
        src = tmp_path / "test.xlsx"
        src.write_bytes(b"fake xlsx content")
        mgr = BackupManager(tmp_path / "backups")
        path = mgr.create_backup(src)
        assert path.exists()
        assert "SEO_Roadmap_" in path.name
        backups = mgr.list_backups()
        assert len(backups) == 1

    def test_missing_source(self, tmp_path):
        mgr = BackupManager(tmp_path / "backups")
        with pytest.raises(FileNotFoundError):
            mgr.create_backup(tmp_path / "nonexistent.xlsx")


# --- Trend Analyzer ---

class TestTrendAnalyzer:
    def test_mark_all_new_first_month(self, tmp_path, sample_queries):
        # Save queries as if it's the first month
        sc_dir = tmp_path / "search_console" / "2026" / "06"
        sc_dir.mkdir(parents=True)
        sample_queries.to_csv(sc_dir / "queries.csv", index=False)

        analyzer = TrendAnalyzer(tmp_path)
        trends = analyzer.analyze(2026, 6)
        new_trends = [t for t in trends if t.direction == "new"]
        assert len(new_trends) > 0
