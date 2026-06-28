"""
Central configuration loader for the SEO Agent.

Reads environment variables from .env and settings from config/settings.yaml.
All scripts import from here instead of loading config independently.
"""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Project root is the directory containing this file
PROJECT_ROOT = Path(__file__).parent.resolve()

# Load .env
load_dotenv(PROJECT_ROOT / ".env")

# Paths
CREDENTIALS_DIR = PROJECT_ROOT / "credentials"
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
OUTPUT_DIR = PROJECT_ROOT / "output"
BACKUPS_DIR = PROJECT_ROOT / "backups"
WEBSITE_DIR = PROJECT_ROOT / "website"

# Environment variables
GA4_PROPERTY_ID = os.getenv("GA4_PROPERTY_ID", "")
SEARCH_CONSOLE_PROPERTY = os.getenv("SEARCH_CONSOLE_PROPERTY", "")
_raw_sa_path = os.getenv(
    "SERVICE_ACCOUNT_FILE",
    str(CREDENTIALS_DIR / "service-account.json"),
)
SERVICE_ACCOUNT_FILE = str(
    Path(_raw_sa_path) if Path(_raw_sa_path).is_absolute()
    else PROJECT_ROOT / _raw_sa_path
)
WEBSITE_ROOT = os.getenv("WEBSITE_ROOT", str(WEBSITE_DIR))


def load_settings() -> dict:
    """Load settings from config/settings.yaml."""
    settings_path = CONFIG_DIR / "settings.yaml"
    if settings_path.exists():
        with open(settings_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def load_website_config() -> dict:
    """Load website configuration from config/website_config.yaml."""
    config_path = CONFIG_DIR / "website_config.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


SETTINGS = load_settings()
WEBSITE_CONFIG = load_website_config()
