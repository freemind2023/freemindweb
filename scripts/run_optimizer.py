"""
Run the SEO Website Optimizer.

Usage:
    python scripts/run_optimizer.py analyze     # Crawl + plan (no changes)
    python scripts/run_optimizer.py apply       # Apply approved changes
    python scripts/run_optimizer.py apply --all # Auto-approve + apply all
    python scripts/run_optimizer.py rollback    # Undo last optimization
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATA_DIR, OUTPUT_DIR, BACKUPS_DIR, LOGS_DIR, WEBSITE_ROOT
from scripts.optimizer.optimizer import Optimizer


def setup_logging():
    log_file = LOGS_DIR / f"optimizer_{datetime.now():%Y-%m-%d}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def main():
    setup_logging()

    action = sys.argv[1] if len(sys.argv) > 1 else "analyze"
    approve_all = "--all" in sys.argv

    optimizer = Optimizer(
        website_root=WEBSITE_ROOT,
        data_dir=DATA_DIR,
        output_dir=OUTPUT_DIR,
        backups_dir=BACKUPS_DIR,
    )

    if action == "analyze":
        optimizer.analyze()
    elif action == "apply":
        optimizer.apply(approve_all=approve_all)
    elif action == "rollback":
        optimizer.rollback()
    else:
        print(f"Unknown action: {action}")
        print("Usage: python scripts/run_optimizer.py [analyze|apply|rollback]")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
