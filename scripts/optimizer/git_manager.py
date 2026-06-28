"""
Git integration — diff, summary, commit workflow.

Never commits directly. Creates diffs for review, generates
human-readable summaries, and waits for explicit approval.
"""

import logging
import subprocess
from dataclasses import dataclass, field, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class GitDiff:
    files_changed: list[str] = field(default_factory=list)
    insertions: int = 0
    deletions: int = 0
    diff_text: str = ""
    summary: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class GitManager:
    def __init__(self, repo_root: Path):
        self._root = repo_root

    def _run(self, *args) -> str:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self._root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning("Git command failed: %s", e)
            return ""

    def is_repo(self) -> bool:
        return (self._root / ".git").exists()

    def init(self) -> bool:
        if self.is_repo():
            return True
        self._run("init")
        return self.is_repo()

    def get_status(self) -> str:
        return self._run("status", "--short")

    def get_diff(self) -> GitDiff:
        """Get current unstaged diff."""
        diff_text = self._run("diff")
        stat = self._run("diff", "--stat")
        changed = self._run("diff", "--name-only").split("\n") if diff_text else []
        changed = [f for f in changed if f.strip()]

        insertions = 0
        deletions = 0
        for line in diff_text.split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                insertions += 1
            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1

        return GitDiff(
            files_changed=changed,
            insertions=insertions,
            deletions=deletions,
            diff_text=diff_text,
            summary=stat,
        )

    def stage_files(self, files: list[str]):
        """Stage specific files for commit."""
        for f in files:
            self._run("add", f)
        logger.info("Staged %d files", len(files))

    def create_commit(self, message: str) -> str:
        """Create a commit with the given message. Returns commit hash."""
        result = self._run("commit", "-m", message)
        hash_line = self._run("rev-parse", "--short", "HEAD")
        logger.info("Created commit: %s", hash_line)
        return hash_line

    def generate_commit_message(self, changes: list[dict]) -> str:
        """Generate a descriptive commit message from applied changes."""
        types = {}
        for c in changes:
            ct = c.get("type", "unknown")
            types[ct] = types.get(ct, 0) + 1

        parts = [f"{count} {ctype}" for ctype, count in sorted(types.items())]
        summary = ", ".join(parts)

        files = set(Path(c.get("file", "")).name for c in changes)

        msg = f"SEO: {summary}\n\n"
        msg += "Changes applied by SEO Agent optimizer:\n"
        for ctype, count in sorted(types.items()):
            msg += f"  - {ctype}: {count} files\n"
        msg += f"\nFiles: {', '.join(sorted(files))}"
        return msg

    def show_review(self, changes: list[dict]) -> str:
        """Generate a human-readable review of pending changes."""
        lines = ["=" * 60, "SEO OPTIMIZER — CHANGE REVIEW", "=" * 60, ""]

        diff = self.get_diff()
        lines.append(f"Files changed:  {len(diff.files_changed)}")
        lines.append(f"Lines added:    +{diff.insertions}")
        lines.append(f"Lines removed:  -{diff.deletions}")
        lines.append("")

        if diff.files_changed:
            lines.append("Changed files:")
            for f in diff.files_changed:
                lines.append(f"  - {f}")
            lines.append("")

        lines.append("Applied changes:")
        for c in changes:
            lines.append(f"  #{c.get('change_id', '?')} [{c.get('type', '')}] {Path(c.get('file', '')).name}")
        lines.append("")
        lines.append("Run 'git diff' to review exact changes before committing.")
        lines.append("=" * 60)

        return "\n".join(lines)
