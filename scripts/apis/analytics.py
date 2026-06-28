"""
Google Analytics 4 Data API wrapper.

Handles authentication, request construction, retry logic, and response
parsing for the GA4 Data API. All GA4 interactions go through GA4Client.
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    RunReportResponse,
)
from google.auth.exceptions import GoogleAuthError
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2


class GA4AuthenticationError(Exception):
    pass


class GA4RequestError(Exception):
    pass


class GA4Client:
    """Reusable wrapper around the GA4 Data API."""

    def __init__(
        self,
        property_id: str,
        service_account_file: str,
    ):
        self._property_id = property_id
        self._sa_path = Path(service_account_file)
        self._credentials: Optional[service_account.Credentials] = None
        self._client: Optional[BetaAnalyticsDataClient] = None

    # ------------------------------------------------------------------
    # Credential validation
    # ------------------------------------------------------------------

    def validate_credentials(self) -> bool:
        """Check that the service-account file exists and is valid JSON
        with the required fields. Does NOT make a network call."""
        if not self._sa_path.exists():
            raise GA4AuthenticationError(
                f"Service account file not found: {self._sa_path}"
            )

        try:
            data = json.loads(self._sa_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise GA4AuthenticationError(
                f"Service account file is not valid JSON: {exc}"
            )

        required = {"type", "project_id", "private_key", "client_email"}
        missing = required - set(data.keys())
        if missing:
            raise GA4AuthenticationError(
                f"Service account file missing fields: {missing}"
            )

        if data.get("type") != "service_account":
            raise GA4AuthenticationError(
                f"Expected type 'service_account', got '{data.get('type')}'"
            )

        if not self._property_id:
            raise GA4AuthenticationError("GA4_PROPERTY_ID is not set")

        logger.info("Credentials validated for project '%s'", data["project_id"])
        return True

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def authenticate(self) -> None:
        """Build Google credentials and instantiate the API client."""
        self.validate_credentials()
        try:
            self._credentials = (
                service_account.Credentials.from_service_account_file(
                    str(self._sa_path),
                    scopes=SCOPES,
                )
            )
            self._client = BetaAnalyticsDataClient(
                credentials=self._credentials,
            )
            logger.info("GA4 client authenticated successfully")
        except GoogleAuthError as exc:
            raise GA4AuthenticationError(f"Authentication failed: {exc}")

    # ------------------------------------------------------------------
    # Connection test
    # ------------------------------------------------------------------

    def test_connection(self) -> dict:
        """Verify connectivity by requesting a minimal 1-day report.

        Returns a dict with status info; raises on failure.
        """
        if self._client is None:
            self.authenticate()

        request = RunReportRequest(
            property=f"properties/{self._property_id}",
            date_ranges=[DateRange(start_date="yesterday", end_date="today")],
            metrics=[Metric(name="sessions")],
            limit=1,
        )

        response = self._run_with_retry(request)
        row_count = response.row_count

        result = {
            "status": "connected",
            "property_id": self._property_id,
            "row_count": row_count,
        }
        logger.info("GA4 connection verified — %d rows available", row_count)
        return result

    # ------------------------------------------------------------------
    # Report execution (with retry)
    # ------------------------------------------------------------------

    def run_report(
        self,
        start_date: str,
        end_date: str,
        metrics: list[str],
        dimensions: list[str],
        row_limit: int = 10_000,
        offset: int = 0,
    ) -> RunReportResponse:
        """Execute a GA4 report request.

        Parameters use the GA4 API naming conventions — e.g.
        metrics=["sessions", "totalUsers"],
        dimensions=["pagePath", "sessionSource"].
        """
        if self._client is None:
            self.authenticate()

        request = RunReportRequest(
            property=f"properties/{self._property_id}",
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            metrics=[Metric(name=m) for m in metrics],
            dimensions=[Dimension(name=d) for d in dimensions],
            limit=row_limit,
            offset=offset,
        )

        return self._run_with_retry(request)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_with_retry(self, request: RunReportRequest) -> RunReportResponse:
        """Execute a request with exponential-backoff retry on transient errors."""
        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return self._client.run_report(request)
            except Exception as exc:
                last_exc = exc
                if attempt == MAX_RETRIES:
                    break
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    "GA4 request failed (attempt %d/%d): %s — retrying in %ds",
                    attempt,
                    MAX_RETRIES,
                    exc,
                    wait,
                )
                time.sleep(wait)

        raise GA4RequestError(
            f"GA4 request failed after {MAX_RETRIES} attempts: {last_exc}"
        )

    @property
    def property_id(self) -> str:
        return self._property_id
