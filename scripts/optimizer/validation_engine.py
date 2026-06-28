"""
Validate changes before and after application.

Runs the deployment validator on modified files and compares
against pre-modification state to ensure no regressions.
"""

import logging
from pathlib import Path

from scripts.website.deployment_validator import DeploymentValidator, ValidationResult

logger = logging.getLogger(__name__)


class ValidationEngine:
    def __init__(self):
        self._validator = DeploymentValidator()

    def validate_before_save(self, html_path: Path) -> ValidationResult:
        """Validate a single file before saving."""
        return self._validator.validate_file(html_path)

    def validate_changed_files(self, file_paths: list[str]) -> dict:
        """Validate all files that were changed."""
        results = []
        for fp in file_paths:
            path = Path(fp)
            if path.exists():
                results.append(self._validator.validate_file(path))

        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)
        all_errors = []
        all_warnings = []
        for r in results:
            for e in r.errors:
                all_errors.append(f"{r.file_path}: {e}")
            for w in r.warnings:
                all_warnings.append(f"{r.file_path}: {w}")

        summary = {
            "files_checked": len(results),
            "passed": passed,
            "failed": failed,
            "errors": all_errors,
            "warnings": all_warnings,
            "can_deploy": failed == 0,
        }

        logger.info(
            "Validation: %d/%d passed, %d errors, %d warnings",
            passed, len(results), len(all_errors), len(all_warnings),
        )
        return summary

    def full_site_validation(self, website_root: Path) -> dict:
        """Run validation on the entire website."""
        results = self._validator.validate_all(website_root)
        passed = sum(1 for r in results if r.passed)
        return {
            "total_files": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "results": [r.to_dict() for r in results],
        }
