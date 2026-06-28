"""
Creates a structured implementation plan from SEO intelligence
findings matched against website page profiles.

Each planned change has a type, target file, before/after preview,
priority, and validation requirements.
"""

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime

from scripts.website.page_mapper import PageProfile
from scripts.website.title_optimizer import TitleOptimizer

logger = logging.getLogger(__name__)


@dataclass
class PlannedChange:
    id: int
    file_path: str
    url: str
    change_type: str  # title, meta_description, schema, h1, canonical, alt_text, faq, internal_link
    description: str
    before: str
    after: str
    priority: float
    seo_impact: str  # critical, high, medium, low
    confidence: float  # 0.0-1.0
    evidence: str
    approved: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ImplementationPlan:
    created_at: str = ""
    total_changes: int = 0
    files_affected: int = 0
    changes: list[PlannedChange] = field(default_factory=list)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def approve_all(self):
        for c in self.changes:
            c.approved = True

    def approve_by_id(self, change_id: int):
        for c in self.changes:
            if c.id == change_id:
                c.approved = True

    def get_approved(self) -> list[PlannedChange]:
        return [c for c in self.changes if c.approved]

    def to_dict(self) -> dict:
        return {
            "created_at": self.created_at,
            "total_changes": self.total_changes,
            "files_affected": self.files_affected,
            "changes": [c.to_dict() for c in self.changes],
        }


class ChangePlanner:
    def create_plan(self, profiles: list[PageProfile]) -> ImplementationPlan:
        """Generate a complete implementation plan from page profiles."""
        plan = ImplementationPlan()
        change_id = 1

        for profile in profiles:
            # Title optimization
            new_title = TitleOptimizer.suggest_title(profile)
            if new_title:
                plan.changes.append(PlannedChange(
                    id=change_id,
                    file_path=profile.file_path,
                    url=profile.url,
                    change_type="title",
                    description=f"Optimize title tag (currently {profile.title_length} chars)",
                    before=profile.title,
                    after=new_title,
                    priority=80 if profile.impressions > 10 else 50,
                    seo_impact="high",
                    confidence=0.9,
                    evidence=f"Title is {profile.title_length} chars (max 60). "
                             f"Page has {profile.impressions} impressions, {profile.ctr:.1%} CTR.",
                ))
                change_id += 1

            # Missing meta description
            if "missing_meta_description" in profile.issues:
                plan.changes.append(PlannedChange(
                    id=change_id,
                    file_path=profile.file_path,
                    url=profile.url,
                    change_type="meta_description",
                    description="Add missing meta description",
                    before="(none)",
                    after="[TO BE GENERATED — requires keyword context]",
                    priority=70,
                    seo_impact="high",
                    confidence=0.8,
                    evidence="Page has no meta description. Google will auto-generate one, "
                             "often poorly.",
                ))
                change_id += 1

            # Missing canonical
            if "missing_canonical" in profile.issues:
                expected = f"https://www.freemindconsult.com{profile.relative_url}"
                plan.changes.append(PlannedChange(
                    id=change_id,
                    file_path=profile.file_path,
                    url=profile.url,
                    change_type="canonical",
                    description="Add missing canonical tag",
                    before="(none)",
                    after=expected,
                    priority=90,
                    seo_impact="critical",
                    confidence=1.0,
                    evidence="Missing canonical can cause duplicate content issues.",
                ))
                change_id += 1

            # Missing schema
            if "missing_schema" in profile.issues:
                schema_type = "Article" if "/blog/" in profile.relative_url else "Service"
                plan.changes.append(PlannedChange(
                    id=change_id,
                    file_path=profile.file_path,
                    url=profile.url,
                    change_type="schema",
                    description=f"Add {schema_type} JSON-LD schema",
                    before="(no schema)",
                    after=f"{schema_type} schema with structured data",
                    priority=60,
                    seo_impact="medium",
                    confidence=0.9,
                    evidence="Page has no structured data. Schema enables rich results.",
                ))
                change_id += 1

            # Missing H1
            if "missing_h1" in profile.issues:
                plan.changes.append(PlannedChange(
                    id=change_id,
                    file_path=profile.file_path,
                    url=profile.url,
                    change_type="h1",
                    description="Add missing H1 heading",
                    before="(no H1)",
                    after=profile.primary_keyword.title() if profile.primary_keyword else profile.title,
                    priority=75,
                    seo_impact="high",
                    confidence=0.9,
                    evidence="Page has no H1. Google uses H1 as a strong ranking signal.",
                ))
                change_id += 1

            # Missing alt text
            if "missing_alt_text" in profile.issues:
                plan.changes.append(PlannedChange(
                    id=change_id,
                    file_path=profile.file_path,
                    url=profile.url,
                    change_type="alt_text",
                    description=f"Fix {profile.images_missing_alt} images missing alt text",
                    before=f"{profile.images_missing_alt} images without alt",
                    after="Descriptive alt text on all images",
                    priority=40,
                    seo_impact="medium",
                    confidence=1.0,
                    evidence="Missing alt text hurts accessibility and image SEO.",
                ))
                change_id += 1

            # Missing OG tags
            if "missing_og_tags" in profile.issues:
                plan.changes.append(PlannedChange(
                    id=change_id,
                    file_path=profile.file_path,
                    url=profile.url,
                    change_type="og_tags",
                    description="Add missing Open Graph meta tags",
                    before="(no OG tags)",
                    after="og:title, og:description, og:image, og:url",
                    priority=35,
                    seo_impact="low",
                    confidence=1.0,
                    evidence="Missing OG tags means poor social media previews.",
                ))
                change_id += 1

        plan.changes.sort(key=lambda c: c.priority, reverse=True)
        for i, c in enumerate(plan.changes):
            c.id = i + 1

        plan.total_changes = len(plan.changes)
        plan.files_affected = len(set(c.file_path for c in plan.changes))

        logger.info(
            "Created implementation plan: %d changes across %d files",
            plan.total_changes, plan.files_affected,
        )
        return plan
