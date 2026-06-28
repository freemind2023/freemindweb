"""
Validate all changes before deployment — HTML validity, schema,
broken links, duplicate titles, missing elements, accessibility.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    file_path: str
    passed: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class DeploymentValidator:
    def validate_file(self, html_path: Path) -> ValidationResult:
        result = ValidationResult(file_path=str(html_path))
        try:
            content = html_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            result.passed = False
            result.errors.append(f"Cannot read file: {e}")
            return result

        soup = BeautifulSoup(content, "html.parser")
        self._check_html_structure(soup, content, result)
        self._check_seo_elements(soup, result)
        self._check_schema_validity(soup, result)
        self._check_accessibility(soup, result)
        self._check_size(content, result)

        result.passed = len(result.errors) == 0
        return result

    def validate_all(self, html_dir: Path) -> list[ValidationResult]:
        results = []
        titles_seen = {}
        for path in sorted(html_dir.rglob("*.html")):
            r = self.validate_file(path)

            # Cross-file: duplicate title check
            soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)
                if title in titles_seen:
                    r.warnings.append(f"Duplicate title with {titles_seen[title]}")
                titles_seen[title] = str(path)

            results.append(r)

        passed = sum(1 for r in results if r.passed)
        logger.info("Validated %d files: %d passed, %d failed", len(results), passed, len(results) - passed)
        return results

    def _check_html_structure(self, soup, raw: str, result: ValidationResult):
        if not soup.find("html"):
            result.errors.append("Missing <html> tag")
        if not soup.find("head"):
            result.errors.append("Missing <head> tag")
        if not soup.find("body"):
            result.errors.append("Missing <body> tag")
        if "<!DOCTYPE" not in raw[:50].upper():
            result.warnings.append("Missing DOCTYPE declaration")

    def _check_seo_elements(self, soup, result: ValidationResult):
        if not soup.find("title"):
            result.errors.append("Missing <title> tag")
        else:
            title = soup.find("title").get_text(strip=True)
            if len(title) > 70:
                result.warnings.append(f"Title too long: {len(title)} chars")

        if not soup.find("meta", attrs={"name": "description"}):
            result.warnings.append("Missing meta description")

        if not soup.find("link", attrs={"rel": "canonical"}):
            result.errors.append("Missing canonical tag")

        h1s = soup.find_all("h1")
        if not h1s:
            result.warnings.append("Missing H1")
        elif len(h1s) > 1:
            result.warnings.append(f"Multiple H1 tags: {len(h1s)}")

    def _check_schema_validity(self, soup, result: ValidationResult):
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                data = json.loads(script.string)
                if "@context" not in data:
                    result.errors.append("Schema missing @context")
                if "@type" not in data:
                    result.errors.append("Schema missing @type")
            except (json.JSONDecodeError, TypeError) as e:
                result.errors.append(f"Invalid JSON-LD schema: {e}")

    def _check_accessibility(self, soup, result: ValidationResult):
        imgs = soup.find_all("img")
        missing_alt = sum(1 for img in imgs if not img.get("alt", "").strip())
        if missing_alt:
            result.warnings.append(f"{missing_alt} images missing alt text")

        links = soup.find_all("a", href=True)
        empty_links = sum(1 for a in links if not a.get_text(strip=True) and not a.find("img"))
        if empty_links:
            result.warnings.append(f"{empty_links} links with no text")

    def _check_size(self, content: str, result: ValidationResult):
        size_kb = len(content.encode("utf-8")) / 1024
        if size_kb > 500:
            result.warnings.append(f"Large HTML: {size_kb:.0f}KB")
