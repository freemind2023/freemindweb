"""
Read, create, and inject JSON-LD structured data into HTML pages.
"""

import json
import logging
import re
from pathlib import Path

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DOMAIN = "https://www.freemindconsult.com"


class SchemaManager:
    @staticmethod
    def read_schemas(html_path: Path) -> list[dict]:
        soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
        schemas = []
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                schemas.append(json.loads(script.string))
            except (json.JSONDecodeError, TypeError):
                pass
        return schemas

    @staticmethod
    def create_service_schema(name: str, description: str, url: str) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": name,
            "provider": {
                "@type": "Organization",
                "name": "Free Mind Consultancy",
                "url": DOMAIN,
            },
            "description": description,
            "areaServed": "India",
            "url": url,
        }

    @staticmethod
    def create_article_schema(headline: str, url: str, date_published: str = "", date_modified: str = "") -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": headline,
            "author": {"@type": "Organization", "name": "Free Mind Consultancy", "url": DOMAIN},
            "publisher": {
                "@type": "Organization",
                "name": "Free Mind Consultancy",
                "logo": {"@type": "ImageObject", "url": f"{DOMAIN}/images/logo.png"},
            },
            "datePublished": date_published or "2026-06-28",
            "dateModified": date_modified or date_published or "2026-06-28",
            "url": url,
        }

    @staticmethod
    def create_faq_schema(questions: list[dict]) -> dict:
        entities = []
        for q in questions:
            entities.append({
                "@type": "Question",
                "name": q["question"],
                "acceptedAnswer": {"@type": "Answer", "text": q["answer"]},
            })
        return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": entities}

    @staticmethod
    def create_breadcrumb_schema(items: list[dict]) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": item["name"], "item": item["url"]}
                for i, item in enumerate(items)
            ],
        }

    @staticmethod
    def create_local_business_schema() -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": "Free Mind Consultancy",
            "url": DOMAIN,
            "logo": f"{DOMAIN}/images/logo.png",
            "description": "Book publishing, ghostwriting, AI calling agents, LMS development, and consulting services for founders, authors, and professionals in India.",
            "address": {"@type": "PostalAddress", "addressCountry": "IN"},
            "areaServed": "India",
            "sameAs": [],
        }

    @staticmethod
    def inject_schema(html: str, schema: dict) -> str:
        """Insert a JSON-LD script block before </head>."""
        script = f'<script type="application/ld+json">\n{json.dumps(schema, ensure_ascii=False)}\n</script>'
        return html.replace("</head>", f"  {script}\n</head>", 1)

    @staticmethod
    def remove_schema_by_type(html: str, schema_type: str) -> str:
        """Remove a specific schema type from the HTML."""
        soup = BeautifulSoup(html, "html.parser")
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                data = json.loads(script.string)
                if data.get("@type") == schema_type:
                    script.decompose()
            except (json.JSONDecodeError, TypeError):
                pass
        return str(soup)
