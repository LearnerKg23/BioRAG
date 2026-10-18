from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ArticleSection(BaseModel):
    """Represents a discrete section within a scientific paper."""
    title: str = Field(..., description="Title of the section, e.g. 'Introduction', 'Results'")
    section_type: str = Field(..., description="Normalized section type: abstract, intro, methods, results, discussion, other")
    content: str = Field(..., description="Full text content of this section")
    order: int = Field(0, description="Sequential ordering within the paper")


class ArticleMetadata(BaseModel):
    """Comprehensive publication metadata extracted from Europe PMC / PubMed."""
    pmid: Optional[str] = Field(None, description="PubMed Identifier")
    pmcid: Optional[str] = Field(None, description="PubMed Central Identifier, e.g. PMC10928374")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    title: str = Field(..., description="Full title of the research article")
    authors: List[str] = Field(default_factory=list, description="List of author names")
    journal: Optional[str] = Field(None, description="Journal name")
    publication_year: Optional[int] = Field(None, description="Year of publication")
    publication_date: Optional[str] = Field(None, description="ISO format date or YYYY-MM")
    is_open_access: bool = Field(True, description="Whether article full-text is open access")
    mesh_terms: List[str] = Field(default_factory=list, description="MeSH subject terms or keywords")
    url: Optional[str] = Field(None, description="Direct URL to Europe PMC / PubMed article")


class Article(BaseModel):
    """Complete representation of an ingested biomedical publication."""
    id: str = Field(..., description="Primary identifier (PMCID preferred, or PMID)")
    metadata: ArticleMetadata
    abstract: str = Field(default="", description="Full abstract text")
    sections: List[ArticleSection] = Field(default_factory=list, description="Ordered sections of the article body")
    raw_xml_path: Optional[str] = Field(None, description="Path to raw cached JATS XML file if stored")
    ingested_at: Optional[str] = Field(None, description="ISO timestamp of ingestion")

    @property
    def full_text(self) -> str:
        """Combine abstract and all section content."""
        parts = []
        if self.abstract:
            parts.append(f"Abstract\n{self.abstract}")
        for s in self.sections:
            parts.append(f"{s.title}\n{s.content}")
        return "\n\n".join(parts)
