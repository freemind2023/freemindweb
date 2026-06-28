"""
Apply approved changes to website files.

Reads the current HTML, applies the specific change, validates
the result, and writes back. Creates a backup before every write.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path

from .change_planner import PlannedChange
from scripts.website.metadata_manager import MetadataManager
from scripts.website.schema_manager import SchemaManager
from scripts.website.canonical_manager import CanonicalManager
from scripts.website.content_optimizer import ContentOptimizer
from scripts.website.image_optimizer import ImageOptimizer

logger = logging.getLogger(__name__)


class ImplementationEngine:
    def __init__(self, backups_dir: Path):
        self._backups_dir = backups_dir
        self._backups_dir.mkdir(parents=True, exist_ok=True)
        self._applied: list[dict] = []

    def apply_change(self, change: PlannedChange) -> bool:
        """Apply a single approved change. Returns True on success."""
        if not change.approved:
            logger.warning("Change #%d not approved — skipping", change.id)
            return False

        file_path = Path(change.file_path)
        if not file_path.exists():
            logger.error("File not found: %s", file_path)
            return False

        # Backup
        self._backup_file(file_path)

        html = file_path.read_text(encoding="utf-8", errors="ignore")
        original = html

        try:
            if change.change_type == "title":
                html = MetadataManager.update_all_metadata(html, title=change.after)

            elif change.change_type == "meta_description":
                html = MetadataManager.update_all_metadata(html, description=change.after)

            elif change.change_type == "canonical":
                html = CanonicalManager.set_canonical(html, change.after)

            elif change.change_type == "h1":
                html = ContentOptimizer.fix_h1(html, change.after)

            elif change.change_type == "alt_text":
                html = ImageOptimizer.fix_missing_alt(html)

            elif change.change_type == "schema":
                if "Article" in change.after:
                    schema = SchemaManager.create_article_schema(
                        headline=change.before if change.before != "(no schema)" else "",
                        url=change.url,
                    )
                else:
                    schema = SchemaManager.create_service_schema(
                        name="", description="", url=change.url,
                    )
                html = SchemaManager.inject_schema(html, schema)

            else:
                logger.warning("Unknown change type: %s", change.change_type)
                return False

            if html == original:
                logger.info("Change #%d: no modification needed for %s", change.id, change.change_type)
                return True

            file_path.write_text(html, encoding="utf-8")
            self._applied.append({
                "change_id": change.id,
                "file": str(file_path),
                "type": change.change_type,
                "applied_at": datetime.now().isoformat(),
            })
            logger.info("Applied change #%d (%s) to %s", change.id, change.change_type, file_path.name)
            return True

        except Exception as e:
            logger.error("Failed to apply change #%d: %s", change.id, e)
            # Restore from backup
            self._restore_file(file_path)
            return False

    def apply_all_approved(self, changes: list[PlannedChange]) -> dict:
        """Apply all approved changes. Returns summary."""
        approved = [c for c in changes if c.approved]
        succeeded = 0
        failed = 0
        for change in approved:
            if self.apply_change(change):
                succeeded += 1
            else:
                failed += 1

        logger.info("Applied %d/%d changes (%d failed)", succeeded, len(approved), failed)
        return {"approved": len(approved), "succeeded": succeeded, "failed": failed}

    def get_applied(self) -> list[dict]:
        return self._applied

    def _backup_file(self, file_path: Path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = self._backups_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
        shutil.copy2(file_path, backup)

    def _restore_file(self, file_path: Path):
        backups = sorted(
            self._backups_dir.glob(f"{file_path.stem}_*{file_path.suffix}"),
            key=lambda p: p.stat().st_mtime, reverse=True,
        )
        if backups:
            shutil.copy2(backups[0], file_path)
            logger.info("Restored %s from backup", file_path.name)
