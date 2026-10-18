import re
import pymupdf as fitz
from typing import Optional, List
from ..models.article import Article, ArticleMetadata, ArticleSection
from .xml_parser import normalize_section_type


class PDFArticleParser:
    """Fallback parser for articles available only as PDF documents."""

    HEADING_REGEX = re.compile(r"^(abstract|introduction|background|methods|materials and methods|results|discussion|conclusion)[\s:]*$", re.IGNORECASE)

    @classmethod
    def parse_file(cls, pdf_path: str, article_id: str, title: Optional[str] = None) -> Article:
        doc = fitz.open(pdf_path)
        full_pages: List[str] = []
        for page in doc:
            full_pages.append(page.get_text())

        doc_text = "\n\n".join(full_pages)
        return cls._parse_text(doc_text, article_id, title)

    @classmethod
    def parse_bytes(cls, pdf_bytes: bytes, article_id: str, title: Optional[str] = None) -> Article:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_pages: List[str] = []
        for page in doc:
            full_pages.append(page.get_text())

        doc_text = "\n\n".join(full_pages)
        return cls._parse_text(doc_text, article_id, title)

    @classmethod
    def _parse_text(cls, text: str, article_id: str, title: Optional[str] = None) -> Article:
        lines = text.splitlines()
        sections: List[ArticleSection] = []
        current_title = "Introduction"
        current_type = "introduction"
        current_paragraphs: List[str] = []
        order = 0
        abstract_text = ""

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            match = cls.HEADING_REGEX.match(stripped)
            if match:
                # Flush existing accumulated section
                if current_paragraphs:
                    sec_content = "\n\n".join(current_paragraphs).strip()
                    if sec_content:
                        sections.append(
                            ArticleSection(
                                title=current_title,
                                section_type=current_type,
                                content=sec_content,
                                order=order
                            )
                        )
                        order += 1
                        if current_type == "abstract" and not abstract_text:
                            abstract_text = sec_content
                    current_paragraphs = []

                current_title = stripped
                current_type = normalize_section_type(stripped)
            else:
                current_paragraphs.append(stripped)

        # Flush final section
        if current_paragraphs:
            sec_content = "\n\n".join(current_paragraphs).strip()
            if sec_content:
                sections.append(
                    ArticleSection(
                        title=current_title,
                        section_type=current_type,
                        content=sec_content,
                        order=order
                    )
                )
                if current_type == "abstract" and not abstract_text:
                    abstract_text = sec_content

        metadata = ArticleMetadata(
            title=title or f"Article {article_id}",
            pmcid=article_id if article_id.startswith("PMC") else None,
            pmid=article_id if article_id.isdigit() else None,
            is_open_access=True
        )

        return Article(
            id=article_id,
            metadata=metadata,
            abstract=abstract_text,
            sections=sections
        )
