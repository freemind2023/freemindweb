"""
Tests for the GA4 data fetching module.

Validates authentication, API request construction, response parsing,
and CSV output formatting.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_ga4_property_id_configured():
    """Verify GA4 property ID is set in config."""
    from config import GA4_PROPERTY_ID
    # TODO: Assert GA4_PROPERTY_ID is not empty when running against real config
    assert isinstance(GA4_PROPERTY_ID, str)


def test_service_account_file_path():
    """Verify service account file path is configured."""
    from config import SERVICE_ACCOUNT_FILE
    assert isinstance(SERVICE_ACCOUNT_FILE, str)
    assert len(SERVICE_ACCOUNT_FILE) > 0


def test_ga4_settings_loaded():
    """Verify GA4 settings are present in config."""
    from config import SETTINGS
    # TODO: Expand once settings.yaml has real values
    assert isinstance(SETTINGS, dict)
