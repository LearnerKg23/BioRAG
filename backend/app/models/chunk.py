from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Represents a discrete semantic chunk of a biomedical paper with rich metadata."""
    chunk_id: str = Field(..., description="Unique chunk identifier, e.g. 'PMC10800001_results_chunk_01'")
    document_id: str = Field(..., description="Source paper ID (PMCID or PMID)")
    pmid: Optional[str] = Field(None, description="PubMed ID")
    pmcid: Optional[str] = Field(None, description="PubMed Central ID")
    doi: Optional[str] = Field(None, description="DOI identifier")
    paper_title: str = Field(..., description="Full title of the source paper")
    journal: Optional[str] = Field(None, description="Journal name")
    publication_year: Optional[int] = Field(None, description="Publication year")
    section_name: str = Field(..., description="Exact original section title (e.g. 'Materials and Methods')")
    section_type: str = Field(..., description="Canonical section type: abstract, introduction, methods, results, discussion, conclusion, other")
    chunk_index: int = Field(0, description="Sequential index within the document")
    token_count: int = Field(0, description="Estimated or exact token count")
    text: str = Field(..., description="Full text content of this chunk, including contextual section prefix")
    raw_content: str = Field(..., description="Clean passage content without prepended prefix")

    def to_metadata_dict(self) -> Dict[str, Any]:
        """Convert chunk metadata to dictionary for vectorstore (FAISS) storage."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "pmid": self.pmid or "",
            "pmcid": self.pmcid or "",
            "doi": self.doi or "",
            "paper_title": self.paper_title,
            "journal": self.journal or "",
            "publication_year": self.publication_year or 0,
            "section_name": self.section_name,
            "section_type": self.section_type,
            "chunk_index": self.chunk_index,
            "token_count": self.token_count,
        }
