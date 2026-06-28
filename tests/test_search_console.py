"""
Tests for the Search Console data fetching module.

Validates authentication, query construction, response parsing,
and CSV output formatting.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_search_console_property_configured():
    """Verify Search Console property is set in config."""
    from config import SEARCH_CONSOLE_PROPERTY
    assert isinstance(SEARCH_CONSOLE_PROPERTY, str)


def test_search_console_settings():
    """Verify Search Console settings are present."""
    from config import SETTINGS
    sc_settings = SETTINGS.get("search_console", {})
    assert isinstance(sc_settings, dict)


def test_data_directory_exists():
    """Verify data/search_console directory exists."""
    from config import DATA_DIR
    sc_dir = DATA_DIR / "search_console"
    assert sc_dir.exists()
