"""
Verify connectivity to Google Analytics 4 and Google Search Console APIs.

Validates credentials, authenticates, and runs a minimal test query
against each API. Run this before any data-fetching scripts.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import GA4_PROPERTY_ID, SEARCH_CONSOLE_PROPERTY, SERVICE_ACCOUNT_FILE, LOGS_DIR
from scripts.apis.analytics import GA4Client, GA4AuthenticationError, GA4RequestError
from scripts.apis.search_console import SearchConsoleClient, GSCAuthenticationError, GSCRequestError


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                LOGS_DIR / "verify_connection.log", encoding="utf-8"
            ),
        ],
    )


def verify_ga4() -> bool:
    logger = logging.getLogger("verify.ga4")
    logger.info("=" * 50)
    logger.info("GOOGLE ANALYTICS 4")
    logger.info("=" * 50)
    logger.info("Property ID : %s", GA4_PROPERTY_ID)
    logger.info("Credentials : %s", SERVICE_ACCOUNT_FILE)

    client = GA4Client(
        property_id=GA4_PROPERTY_ID,
        service_account_file=SERVICE_ACCOUNT_FILE,
    )

    try:
        client.validate_credentials()
        logger.info("[PASS] Credentials valid")
    except GA4AuthenticationError as exc:
        logger.error("[FAIL] Credential validation: %s", exc)
        return False

    try:
        client.authenticate()
        logger.info("[PASS] Authentication successful")
    except GA4AuthenticationError as exc:
        logger.error("[FAIL] Authentication: %s", exc)
        return False

    try:
        result = client.test_connection()
        logger.info("[PASS] Connection verified — %d rows", result["row_count"])
        return True
    except GA4RequestError as exc:
        logger.error("[FAIL] Connection test: %s", exc)
        return False


def verify_gsc() -> bool:
    logger = logging.getLogger("verify.gsc")
    logger.info("=" * 50)
    logger.info("GOOGLE SEARCH CONSOLE")
    logger.info("=" * 50)
    logger.info("Property    : %s", SEARCH_CONSOLE_PROPERTY)
    logger.info("Credentials : %s", SERVICE_ACCOUNT_FILE)

    client = SearchConsoleClient(
        site_url=SEARCH_CONSOLE_PROPERTY,
        service_account_file=SERVICE_ACCOUNT_FILE,
    )

    try:
        client.validate_credentials()
        logger.info("[PASS] Credentials valid")
    except GSCAuthenticationError as exc:
        logger.error("[FAIL] Credential validation: %s", exc)
        return False

    try:
        client.authenticate()
        logger.info("[PASS] Authentication successful")
    except GSCAuthenticationError as exc:
        logger.error("[FAIL] Authentication: %s", exc)
        return False

    try:
        result = client.test_connection()
        if result["property_found"]:
            logger.info("[PASS] Property '%s' is accessible", SEARCH_CONSOLE_PROPERTY)
        else:
            logger.warning(
                "[WARN] Connected but property '%s' not found in accessible sites: %s",
                SEARCH_CONSOLE_PROPERTY,
                result["accessible_sites"],
            )
            logger.warning(
                "       Grant access to the service account email in Search Console settings."
            )
        return True
    except GSCRequestError as exc:
        logger.error("[FAIL] Connection test: %s", exc)
        return False


def main():
    setup_logging()
    logger = logging.getLogger("verify")

    logger.info("SEO Agent — API Connection Verification")
    logger.info("")

    ga4_ok = verify_ga4()
    logger.info("")
    gsc_ok = verify_gsc()

    logger.info("")
    logger.info("=" * 50)
    logger.info("RESULTS")
    logger.info("=" * 50)
    logger.info("GA4            : %s", "PASS" if ga4_ok else "FAIL")
    logger.info("Search Console : %s", "PASS" if gsc_ok else "FAIL")

    if ga4_ok and gsc_ok:
        logger.info("All connections verified. Ready to fetch data.")
        return 0
    else:
        logger.error("One or more connections failed. Fix the issues above and retry.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
