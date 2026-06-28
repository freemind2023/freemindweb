"""
Detect and manage redirects. Checks for redirect chains,
www/non-www consistency, and HTTP/HTTPS issues.
"""

import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

DOMAIN = "https://www.freemindconsult.com"


@dataclass
class RedirectIssue:
    source: str
    issue: str
    recommendation: str

    def to_dict(self) -> dict:
        return asdict(self)


class RedirectManager:
    @staticmethod
    def check_canonical_consistency(pages_data: list[dict]) -> list[RedirectIssue]:
        """Check that canonical URLs are consistent with the site domain."""
        issues = []
        for page in pages_data:
            canonical = page.get("canonical", "")
            url = page.get("url", "")
            if canonical and not canonical.startswith(DOMAIN):
                issues.append(RedirectIssue(
                    source=url,
                    issue=f"Canonical points to wrong domain: {canonical}",
                    recommendation=f"Change canonical to {url}",
                ))
            og_url = page.get("og_url", "")
            if og_url and og_url != url and og_url != canonical:
                issues.append(RedirectIssue(
                    source=url,
                    issue=f"og:url ({og_url}) doesn't match canonical ({canonical})",
                    recommendation=f"Set og:url to match canonical: {canonical or url}",
                ))
        return issues
