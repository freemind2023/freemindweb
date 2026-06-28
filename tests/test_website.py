"""
Tests for the website intelligence and optimizer modules.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import pandas as pd

from scripts.website.crawler import WebsiteCrawler, PageData
from scripts.website.page_mapper import PageMapper, PageProfile
from scripts.website.metadata_manager import MetadataManager
from scripts.website.schema_manager import SchemaManager
from scripts.website.canonical_manager import CanonicalManager
from scripts.website.content_optimizer import ContentOptimizer
from scripts.website.image_optimizer import ImageOptimizer
from scripts.website.faq_manager import FAQManager
from scripts.website.deployment_validator import DeploymentValidator
from scripts.optimizer.change_planner import ChangePlanner
from scripts.optimizer.git_manager import GitManager


SAMPLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Book Publishing Services India — Free Mind Consultancy India Is The Best</title>
  <meta name="description" content="We offer book publishing services in India for authors, professors, and government officers.">
  <meta property="og:title" content="Book Publishing Services India">
  <meta property="og:description" content="Book publishing in India">
  <meta name="twitter:title" content="Book Publishing">
  <meta name="twitter:description" content="Publishing services">
  <link rel="canonical" href="https://www.freemindconsult.com/services/book-publishing-india.html">
</head>
<body>
  <h1>Book Publishing Services</h1>
  <p>We help authors publish books in India. Our services include editing, formatting, and distribution.</p>
  <img src="images/book.jpg" alt="">
  <img src="images/author.jpg">
  <a href="/services/ghostwriting-india.html">Ghostwriting</a>
  <a href="https://amazon.com">Amazon</a>
  <footer>Free Mind Consultancy</footer>
</body>
</html>"""


@pytest.fixture
def html_file(tmp_path):
    p = tmp_path / "test.html"
    p.write_text(SAMPLE_HTML, encoding="utf-8")
    return p


# --- MetadataManager ---

class TestMetadataManager:
    def test_read_metadata(self, html_file):
        meta = MetadataManager.read_metadata(html_file)
        assert "Book Publishing" in meta["title"]
        assert "book publishing" in meta["meta_description"].lower()
        assert meta["og_title"] == "Book Publishing Services India"

    def test_update_title(self):
        result = MetadataManager.update_title(SAMPLE_HTML, "New Title | Free Mind")
        assert "<title>New Title | Free Mind</title>" in result

    def test_update_meta_description(self):
        result = MetadataManager.update_meta_description(SAMPLE_HTML, "New description here.")
        assert 'content="New description here."' in result

    def test_update_all_metadata(self):
        result = MetadataManager.update_all_metadata(SAMPLE_HTML, title="T", description="D")
        assert "<title>T</title>" in result
        assert 'name="description" content="D"' in result


# --- SchemaManager ---

class TestSchemaManager:
    def test_create_service_schema(self):
        s = SchemaManager.create_service_schema("Test Service", "Description", "https://example.com/")
        assert s["@type"] == "Service"
        assert s["name"] == "Test Service"

    def test_create_faq_schema(self):
        s = SchemaManager.create_faq_schema([
            {"question": "Q1?", "answer": "A1."},
            {"question": "Q2?", "answer": "A2."},
        ])
        assert s["@type"] == "FAQPage"
        assert len(s["mainEntity"]) == 2

    def test_inject_schema(self):
        schema = {"@context": "https://schema.org", "@type": "Service", "name": "Test"}
        result = SchemaManager.inject_schema(SAMPLE_HTML, schema)
        assert "application/ld+json" in result
        assert '"@type": "Service"' in result


# --- CanonicalManager ---

class TestCanonicalManager:
    def test_read_canonical(self):
        c = CanonicalManager.read_canonical(SAMPLE_HTML)
        assert c == "https://www.freemindconsult.com/services/book-publishing-india.html"

    def test_set_canonical(self):
        result = CanonicalManager.set_canonical(SAMPLE_HTML, "https://example.com/new")
        assert 'href="https://example.com/new"' in result

    def test_validate_canonical(self):
        issues = CanonicalManager.validate_canonical(SAMPLE_HTML, "https://wrong.com/")
        assert any("mismatch" in i for i in issues)


# --- ContentOptimizer ---

class TestContentOptimizer:
    def test_fix_h1(self):
        html_no_h1 = "<html><body><section><p>Text</p></section></body></html>"
        result = ContentOptimizer.fix_h1(html_no_h1, "My Heading")
        assert "My Heading" in result
        assert "<h1>" in result

    def test_word_count(self):
        count = ContentOptimizer.get_word_count(SAMPLE_HTML)
        assert count > 5


# --- ImageOptimizer ---

class TestImageOptimizer:
    def test_fix_missing_alt(self):
        result = ImageOptimizer.fix_missing_alt(SAMPLE_HTML)
        # The second img had no alt at all; first had empty alt
        assert 'alt="Free Mind Consultancy' in result

    def test_audit_images(self):
        audit = ImageOptimizer.audit_images(SAMPLE_HTML)
        assert len(audit) == 2
        assert audit[0]["has_alt"] is False  # empty alt
        assert audit[1]["has_alt"] is False  # no alt attr


# --- FAQManager ---

class TestFAQManager:
    def test_has_faq_false(self):
        assert FAQManager.has_faq(SAMPLE_HTML) is False

    def test_add_faq_section(self):
        questions = [
            {"question": "How much does it cost?", "answer": "It depends on the scope."},
            {"question": "How long does it take?", "answer": "2-4 weeks."},
        ]
        result = FAQManager.add_faq_section(SAMPLE_HTML, questions)
        assert "Frequently Asked Questions" in result
        assert "How much does it cost?" in result
        assert "FAQPage" in result


# --- DeploymentValidator ---

class TestDeploymentValidator:
    def test_validate_valid_file(self, html_file):
        v = DeploymentValidator()
        result = v.validate_file(html_file)
        assert result.passed is True

    def test_validate_missing_elements(self, tmp_path):
        bad = tmp_path / "bad.html"
        bad.write_text("<html><head></head><body></body></html>", encoding="utf-8")
        v = DeploymentValidator()
        result = v.validate_file(bad)
        assert any("title" in e.lower() for e in result.errors)


# --- PageMapper ---

class TestPageMapper:
    def test_normalize_url(self):
        assert PageMapper.normalize_url("https://example.com/blog/") == "/blog"
        assert PageMapper.normalize_url("/") == "/"
        assert PageMapper.normalize_url("https://example.com/") == "/"

    def test_build_profiles_scoring(self, tmp_path):
        html_path = tmp_path / "test.html"
        html_path.write_text(SAMPLE_HTML, encoding="utf-8")
        page = PageData(
            file_path=str(html_path),
            url="https://example.com/test",
            relative_url="/test",
            title="Long Title " * 10,
            title_length=100,
            h1=["H1"],
            images=[{"has_alt": False}, {"has_alt": True}],
            word_count=500,
        )
        mapper = PageMapper()
        profiles = mapper.build_profiles([page])
        assert len(profiles) == 1
        assert profiles[0].technical_score < 100  # should lose points for long title
        assert "title_too_long" in profiles[0].issues


# --- ChangePlanner ---

class TestChangePlanner:
    def test_create_plan(self):
        profile = PageProfile(
            url="https://example.com/test",
            relative_url="/test",
            file_path="/tmp/test.html",
            title="A" * 80,
            title_length=80,
            meta_description="",
            meta_description_length=0,
            canonical="",
            issues=["title_too_long", "missing_meta_description", "missing_canonical"],
            impressions=100,
            ctr=0.01,
        )
        planner = ChangePlanner()
        plan = planner.create_plan([profile])
        assert plan.total_changes >= 3
        assert plan.files_affected == 1
        types = [c.change_type for c in plan.changes]
        assert "title" in types
        assert "meta_description" in types
        assert "canonical" in types


# --- GitManager ---

class TestGitManager:
    def test_generate_commit_message(self, tmp_path):
        gm = GitManager(tmp_path)
        msg = gm.generate_commit_message([
            {"type": "title", "file": "/tmp/index.html"},
            {"type": "title", "file": "/tmp/about.html"},
            {"type": "canonical", "file": "/tmp/index.html"},
        ])
        assert "2 title" in msg
        assert "1 canonical" in msg
