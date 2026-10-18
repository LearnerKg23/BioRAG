import re
from typing import List, Optional
from lxml import etree
from ..models.article import Article, ArticleMetadata, ArticleSection


SECTION_TYPE_PATTERNS = {
    "abstract": re.compile(r"^(abstract|summary)", re.IGNORECASE),
    "introduction": re.compile(r"^(introduction|background)", re.IGNORECASE),
    "methods": re.compile(r"^(methods|materials and methods|methodology|experimental procedures|patients and methods)", re.IGNORECASE),
    "results": re.compile(r"^(results|findings|observations)", re.IGNORECASE),
    "discussion": re.compile(r"^(discussion|implications)", re.IGNORECASE),
    "conclusion": re.compile(r"^(conclusion|conclusions|concluding remarks)", re.IGNORECASE),
}


def normalize_section_type(title: str) -> str:
    """Classify arbitrary section heading into normalized canonical category."""
    clean_title = title.strip()
    for sec_type, pattern in SECTION_TYPE_PATTERNS.items():
        if pattern.search(clean_title):
            return sec_type
    return "other"


def clean_xml_text(element: Optional[etree._Element]) -> str:
    """Extract clean string from element, resolving internal markup and spacing."""
    if element is None:
        return ""
    # Extract all text, including children (such as <i>, <b>, <sub>, <sup>)
    text = "".join(element.itertext())
    # Clean excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


class JATSArticleParser:
    """Parses standard NLM/NCBI JATS (Journal Article Tag Suite) XML into Article domain models."""

    @classmethod
    def parse(cls, xml_content: str | bytes, fallback_id: Optional[str] = None) -> Article:
        if isinstance(xml_content, str):
            xml_content = xml_content.encode("utf-8")

        # Parse XML with recovery for slightly malformed payloads
        parser = etree.XMLParser(recover=True, remove_blank_text=True, encoding="utf-8")
        root = etree.fromstring(xml_content, parser=parser)

        # 1. Metadata Extraction
        front = root.find(".//front")
        
        # Title
        title_el = root.find(".//article-title")
        title = clean_xml_text(title_el) or "Untitled Biomedical Article"

        # Identifiers
        pmid = None
        pmcid = None
        doi = None

        for el in root.findall(".//article-id"):
            id_type = el.get("pub-id-type", "").lower()
            val = clean_xml_text(el)
            if id_type == "pmid":
                pmid = val
            elif id_type in ("pmc", "pmcid"):
                pmcid = val if val.startswith("PMC") else f"PMC{val}"
            elif id_type == "doi":
                doi = val

        # Fallback to provided fallback_id if PMCID or PMID is missing
        if not pmcid and fallback_id and fallback_id.upper().startswith("PMC"):
            pmcid = fallback_id.upper()
        if not pmid and fallback_id and fallback_id.isdigit():
            pmid = fallback_id

        primary_id = pmcid or pmid or doi or (fallback_id or "UNKNOWN_DOC")

        # Authors
        authors: List[str] = []
        for contrib in root.findall(".//contrib[@contrib-type='author']"):
            surname_el = contrib.find(".//surname")
            given_el = contrib.find(".//given-names")
            if surname_el is not None:
                surname = clean_xml_text(surname_el)
                given = clean_xml_text(given_el) if given_el is not None else ""
                full_name = f"{given} {surname}".strip() if given else surname
                if full_name:
                    authors.append(full_name)

        # Journal
        journal_el = root.find(".//journal-title")
        if journal_el is None:
            journal_el = root.find(".//journal-id")
        journal = clean_xml_text(journal_el) or None

        # Publication Year
        pub_year = None
        year_el = root.find(".//pub-date/year")
        if year_el is not None:
            year_text = clean_xml_text(year_el)
            if year_text.isdigit():
                pub_year = int(year_text)

        # Abstract
        abstract_el = root.find(".//abstract")
        abstract = clean_xml_text(abstract_el)

        # Keywords / MeSH terms
        mesh_terms: List[str] = []
        for kwd in root.findall(".//kwd"):
            t = clean_xml_text(kwd)
            if t:
                mesh_terms.append(t)

        url = f"https://europepmc.org/article/PMC/{pmcid.replace('PMC', '')}" if pmcid else (
            f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None
        )

        metadata = ArticleMetadata(
            pmid=pmid,
            pmcid=pmcid,
            doi=doi,
            title=title,
            authors=authors,
            journal=journal,
            publication_year=pub_year,
            is_open_access=True,
            mesh_terms=mesh_terms,
            url=url,
        )

        # 2. Body Section Parsing
        sections: List[ArticleSection] = []
        body = root.find(".//body")
        order = 0

        if body is not None:
            # Iterate through top-level or direct section elements
            sec_elements = body.findall("./sec")
            # If no direct ./sec, search .//sec
            if not sec_elements:
                sec_elements = body.findall(".//sec")

            for sec in sec_elements:
                title_elem = sec.find("./title")
                sec_title = clean_xml_text(title_elem) if title_elem is not None else f"Section {order + 1}"
                
                # Gather paragraph text within this section (excluding nested sub-section titles if present)
                paragraphs: List[str] = []
                for p in sec.findall(".//p"):
                    p_text = clean_xml_text(p)
                    if p_text:
                        paragraphs.append(p_text)

                content = "\n\n".join(paragraphs).strip()
                if content:
                    norm_type = normalize_section_type(sec_title)
                    sections.append(
                        ArticleSection(
                            title=sec_title,
                            section_type=norm_type,
                            content=content,
                            order=order
                        )
                    )
                    order += 1

        # If body is empty or had no parsed sections, but abstract exists, create an abstract section
        if not sections and abstract:
            sections.append(
                ArticleSection(
                    title="Abstract",
                    section_type="abstract",
                    content=abstract,
                    order=0
                )
            )

        return Article(
            id=primary_id,
            metadata=metadata,
            abstract=abstract,
            sections=sections,
        )
