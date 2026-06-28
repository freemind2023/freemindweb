"""
Add and manage FAQ sections with FAQPage schema markup.
"""

import json
import logging

from bs4 import BeautifulSoup

from .schema_manager import SchemaManager

logger = logging.getLogger(__name__)


class FAQManager:
    @staticmethod
    def has_faq(html: str) -> bool:
        soup = BeautifulSoup(html, "html.parser")
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                data = json.loads(script.string)
                if data.get("@type") == "FAQPage":
                    return True
            except (json.JSONDecodeError, TypeError):
                pass
        return False

    @staticmethod
    def add_faq_section(html: str, questions: list[dict], insert_before: str = "footer") -> str:
        """Add an FAQ HTML section and FAQPage schema.

        questions: [{"question": "...", "answer": "..."}]
        """
        if FAQManager.has_faq(html):
            logger.info("FAQ already exists, skipping")
            return html

        # Build HTML
        faq_html = '\n<section class="faq-section" style="max-width:760px;margin:48px auto;padding:0 20px;">\n'
        faq_html += '  <h2>Frequently Asked Questions</h2>\n'
        for q in questions:
            faq_html += f'  <div class="faq-item" style="border-top:1px solid var(--color-border);padding-top:24px;margin-top:24px;">\n'
            faq_html += f'    <h3>{q["question"]}</h3>\n'
            faq_html += f'    <p>{q["answer"]}</p>\n'
            faq_html += f'  </div>\n'
        faq_html += '</section>\n'

        # Insert before footer or end of body
        soup = BeautifulSoup(html, "html.parser")
        target = soup.find(insert_before) or soup.find("body")
        if target:
            faq_soup = BeautifulSoup(faq_html, "html.parser")
            if target.name == "body":
                target.append(faq_soup)
            else:
                target.insert_before(faq_soup)

        result = str(soup)

        # Add schema
        schema = SchemaManager.create_faq_schema(questions)
        result = SchemaManager.inject_schema(result, schema)

        logger.info("Added FAQ section with %d questions", len(questions))
        return result
