"""
Google Search Console API wrapper.

Handles authentication, request construction, retry logic, and response
parsing for the Search Console API. All GSC interactions go through
SearchConsoleClient.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Optional

from google.auth.exceptions import GoogleAuthError
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2


class GSCAuthenticationError(Exception):
    pass


class GSCRequestError(Exception):
    pass


class SearchConsoleClient:
    """Reusable wrapper around the Google Search Console API."""

    def __init__(
        self,
        site_url: str,
        service_account_file: str,
    ):
        self._site_url = site_url
        self._sa_path = Path(service_account_file)
        self._credentials: Optional[service_account.Credentials] = None
        self._service = None

    # ------------------------------------------------------------------
    # Credential validation
    # ------------------------------------------------------------------

    def validate_credentials(self) -> bool:
        """Check that the service-account file exists and is valid JSON
        with the required fields. Does NOT make a network call."""
        if not self._sa_path.exists():
            raise GSCAuthenticationError(
                f"Service account file not found: {self._sa_path}"
            )

        try:
            data = json.loads(self._sa_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise GSCAuthenticationError(
                f"Service account file is not valid JSON: {exc}"
            )

        required = {"type", "project_id", "private_key", "client_email"}
        missing = required - set(data.keys())
        if missing:
            raise GSCAuthenticationError(
                f"Service account file missing fields: {missing}"
            )

        if data.get("type") != "service_account":
            raise GSCAuthenticationError(
                f"Expected type 'service_account', got '{data.get('type')}'"
            )

        if not self._site_url:
            raise GSCAuthenticationError("SEARCH_CONSOLE_PROPERTY is not set")

        logger.info("Credentials validated for project '%s'", data["project_id"])
        return True

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def authenticate(self) -> None:
        """Build Google credentials and instantiate the API service."""
        self.validate_credentials()
        try:
            self._credentials = (
                service_account.Credentials.from_service_account_file(
                    str(self._sa_path),
                    scopes=SCOPES,
                )
            )
            self._service = build(
                "searchconsole",
                "v1",
                credentials=self._credentials,
            )
            logger.info("Search Console client authenticated successfully")
        except GoogleAuthError as exc:
            raise GSCAuthenticationError(f"Authentication failed: {exc}")

    # ------------------------------------------------------------------
    # Connection test
    # ------------------------------------------------------------------

    def test_connection(self) -> dict:
        """Verify connectivity by listing accessible sites.

        Returns a dict with status info; raises on failure.
        """
        if self._service is None:
            self.authenticate()

        sites = self._execute_with_retry(
            self._service.sites().list()
        )

        site_entries = sites.get("siteEntry", [])
        urls = [s["siteUrl"] for s in site_entries]

        found = self._site_url in urls
        # Also check with/without trailing slash
        alt = (
            self._site_url.rstrip("/") + "/"
            if not self._site_url.endswith("/")
            else self._site_url.rstrip("/")
        )
        found = found or alt in urls
        # SC may also store as sc-domain: variant
        domain = self._site_url.replace("https://", "").replace("http://", "").rstrip("/")
        found = found or f"sc-domain:{domain}" in urls

        result = {
            "status": "connected",
            "target_property": self._site_url,
            "property_found": found,
            "accessible_sites": urls,
        }

        if found:
            logger.info(
                "Search Console connection verified — property '%s' accessible",
                self._site_url,
            )
        else:
            logger.warning(
                "Connected to Search Console but property '%s' not found. "
                "Accessible sites: %s. Grant access to the service account.",
                self._site_url,
                urls,
            )

        return result

    # ------------------------------------------------------------------
    # Query execution
    # ------------------------------------------------------------------

    def query(
        self,
        start_date: str,
        end_date: str,
        dimensions: list[str],
        row_limit: int = 5000,
        start_row: int = 0,
        search_type: str = "web",
    ) -> dict[str, Any]:
        """Execute a Search Analytics query.

        Parameters:
            start_date / end_date: YYYY-MM-DD strings
            dimensions: e.g. ["query", "page", "country", "device"]
            row_limit: max rows per response (API max 25000)
            start_row: for pagination
            search_type: "web", "image", "video", "news", "discover"
        """
        if self._service is None:
            self.authenticate()

        body = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": dimensions,
            "rowLimit": min(row_limit, 25_000),
            "startRow": start_row,
            "type": search_type,
        }

        request = (
            self._service
            .searchanalytics()
            .query(siteUrl=self._site_url, body=body)
        )

        return self._execute_with_retry(request)

    def list_sitemaps(self) -> list[dict]:
        """List sitemaps submitted for this property."""
        if self._service is None:
            self.authenticate()

        request = self._service.sitemaps().list(siteUrl=self._site_url)
        response = self._execute_with_retry(request)
        return response.get("sitemap", [])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _execute_with_retry(self, request) -> dict:
        """Execute an API request with exponential-backoff retry."""
        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return request.execute()
            except HttpError as exc:
                status = exc.resp.status if exc.resp else None
                # Only retry on transient errors
                if status and status < 500 and status != 429:
                    raise GSCRequestError(
                        f"Search Console request failed (HTTP {status}): {exc}"
                    )
                last_exc = exc
            except Exception as exc:
                last_exc = exc

            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    "GSC request failed (attempt %d/%d): %s — retrying in %ds",
                    attempt,
                    MAX_RETRIES,
                    last_exc,
                    wait,
                )
                time.sleep(wait)

        raise GSCRequestError(
            f"Search Console request failed after {MAX_RETRIES} attempts: {last_exc}"
        )

    @property
    def site_url(self) -> str:
        return self._site_url
