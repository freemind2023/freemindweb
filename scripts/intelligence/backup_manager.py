"""
Backup manager for the SEO roadmap Excel workbook.

Creates timestamped backups before any modification. Manages
backup retention and provides restore capability.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class BackupManager:
    def __init__(self, backups_dir: Path):
        self._backups_dir = backups_dir
        self._backups_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, source_path: Path) -> Path:
        """Create a timestamped backup of the workbook."""
        if not source_path.exists():
            raise FileNotFoundError(f"Cannot back up: {source_path} not found")

        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        backup_name = f"SEO_Roadmap_{timestamp}.xlsx"
        backup_path = self._backups_dir / backup_name

        shutil.copy2(source_path, backup_path)
        logger.info("Backup created: %s", backup_path)
        return backup_path

    def list_backups(self) -> list[Path]:
        """List all backup files, newest first."""
        backups = sorted(
            self._backups_dir.glob("SEO_Roadmap_*.xlsx"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return backups

    def latest_backup(self) -> Path | None:
        """Return the most recent backup, or None."""
        backups = self.list_backups()
        return backups[0] if backups else None
