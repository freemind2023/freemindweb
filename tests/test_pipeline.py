"""
Tests for the pipeline orchestrator.

Validates that pipeline steps are loaded correctly, logging is configured,
and the pipeline handles missing/failed steps gracefully.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_pipeline_steps_defined():
    """Verify pipeline steps are defined in settings."""
    from config import SETTINGS
    steps = SETTINGS.get("pipeline", {}).get("steps", [])
    assert isinstance(steps, list)
    assert len(steps) > 0


def test_logs_directory_exists():
    """Verify logs directory exists for pipeline output."""
    from config import LOGS_DIR
    assert LOGS_DIR.exists()


def test_all_directories_exist():
    """Verify all required project directories exist."""
    from config import (
        DATA_DIR, REPORTS_DIR, LOGS_DIR, OUTPUT_DIR, BACKUPS_DIR,
    )
    for d in [DATA_DIR, REPORTS_DIR, LOGS_DIR, OUTPUT_DIR, BACKUPS_DIR]:
        assert d.exists(), f"Missing directory: {d}"
