"""
Optimize website images for SEO and performance.

Scans all images in the website directory, checks file sizes, formats,
dimensions, and alt text. Compresses oversized images, converts to WebP
where appropriate, and generates missing alt text suggestions.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import WEBSITE_ROOT, OUTPUT_DIR, BACKUPS_DIR, SETTINGS


def optimize_images():
    """Audit and optimize website images."""
    # TODO: Implement image optimization
    # 1. Scan website directory for image files
    # 2. Check each image: file size, dimensions, format
    # 3. Flag images exceeding size thresholds from settings
    # 4. Compress oversized images (save originals to backups/)
    # 5. Convert to WebP where supported
    # 6. Check HTML for missing alt text on <img> tags
    # 7. Suggest descriptive alt text with keywords
    # 8. Save optimized images to output/ and report to output/recommendations/
    raise NotImplementedError("Image optimization not yet implemented")


if __name__ == "__main__":
    optimize_images()
