"""
Rollback manager — restore files from backups when changes cause issues.
"""

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class RollbackManager:
    def __init__(self, backups_dir: Path):
        self._backups_dir = backups_dir

    def list_backups(self, filename_stem: str = "") -> list[Path]:
        """List available backups, optionally filtered by filename."""
        pattern = f"{filename_stem}_*" if filename_stem else "*"
        return sorted(
            self._backups_dir.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

    def rollback_file(self, original_path: Path) -> bool:
        """Restore a file from its most recent backup."""
        backups = self.list_backups(original_path.stem)
        if not backups:
            logger.error("No backups found for %s", original_path.name)
            return False
        shutil.copy2(backups[0], original_path)
        logger.info("Rolled back %s from %s", original_path.name, backups[0].name)
        return True

    def rollback_all(self, file_paths: list[Path]) -> dict:
        """Rollback multiple files."""
        results = {"succeeded": 0, "failed": 0, "files": []}
        for path in file_paths:
            if self.rollback_file(path):
                results["succeeded"] += 1
                results["files"].append(str(path))
            else:
                results["failed"] += 1
        logger.info(
            "Rollback complete: %d succeeded, %d failed",
            results["succeeded"], results["failed"],
        )
        return results
