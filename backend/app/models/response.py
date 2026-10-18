from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CitationItem(BaseModel):
    """Represents a passage-level citation linking a claim to its source paper."""
    pmid: Optional[str] = Field(None, description="PubMed ID")
    pmcid: Optional[str] = Field(None, description="PubMed Central ID")
    title: str = Field(..., description="Paper title")
    section: str = Field(..., description="Source section name, e.g. 'Results'")
    chunk_id: str = Field(..., description="Source chunk ID")
    doi: Optional[str] = Field(None, description="DOI link")
    supporting_text: str = Field(..., description="Extracted snippet supporting the claim")


class ContradictionItem(BaseModel):
    """Represents an identified conflict between findings across multiple papers."""
    topic: str = Field(..., description="Biological variable or finding in dispute")
    study_a_pmid: Optional[str] = Field(None, description="First study PMID")
    study_a_claim: str = Field(..., description="Reported finding in study A")
    study_b_pmid: Optional[str] = Field(None, description="Second study PMID")
    study_b_claim: str = Field(..., description="Reported finding in study B")
    potential_reason: Optional[str] = Field(None, description="Methodology, cohort, or dosage discrepancy")


class BioRAGResponse(BaseModel):
    """Structured response from the BioRAG assistant."""
    query: str = Field(..., description="Original user biomedical research query")
    answer: str = Field(..., description="Evidence-grounded synthesized answer with citation anchors")
    citations: List[CitationItem] = Field(default_factory=list, description="Verified passage citations")
    conflicts_detected: List[ContradictionItem] = Field(default_factory=list, description="Divergent or contradictory findings across studies")
    confidence_score: float = Field(0.0, description="Estimated confidence score (0.0 to 1.0)")
    has_sufficient_evidence: bool = Field(True, description="False if model abstained due to lack of evidence")
    abstention_reason: Optional[str] = Field(None, description="Explanation if system abstains")
    retrieval_mode: Optional[str] = Field(None, description="Retrieval strategy used")
    total_chunks_retrieved: int = Field(0, description="Count of evidence chunks provided to generator")
