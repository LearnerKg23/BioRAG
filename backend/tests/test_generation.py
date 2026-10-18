import pytest
from backend.app.models.chunk import DocumentChunk
from backend.app.rag.embeddings import MockBiomedicalEmbeddings
from backend.app.rag.vectorstore import FAISSIndexManager
from backend.app.rag.bm25 import BM25IndexManager
from backend.app.rag.generator import BioRAGGenerator
from backend.app.rag.pipeline import BioRAGPipeline
from backend.app.rag.hybrid_retriever import RetrievalMode


@pytest.fixture
def sample_evidence():
    return [
        DocumentChunk(
            chunk_id="chunk_melanoma_01",
            document_id="PMC1001",
            pmid="380001",
            pmcid="PMC1001",
            doi="10.1038/s41586-024-001",
            paper_title="Targeting BRAF V600E in Melanoma",
            journal="Nature",
            publication_year=2024,
            section_name="Results",
            section_type="results",
            chunk_index=0,
            token_count=45,
            text="[Paper: Targeting BRAF V600E in Melanoma | Section: Results]\nDabrafenib combined with trametinib significantly prolonged progression-free survival in BRAF V600E metastatic melanoma.",
            raw_content="Dabrafenib combined with trametinib significantly prolonged progression-free survival in BRAF V600E metastatic melanoma.",
        ),
        DocumentChunk(
            chunk_id="chunk_melanoma_02",
            document_id="PMC1002",
            pmid="380002",
            pmcid="PMC1002",
            doi="10.1038/s41586-024-002",
            paper_title="Resistance Pathways in Melanoma",
            journal="Cell",
            publication_year=2024,
            section_name="Discussion",
            section_type="discussion",
            chunk_index=1,
            token_count=40,
            text="[Paper: Resistance Pathways in Melanoma | Section: Discussion]\nSecondary NRAS Q61K mutations frequently reactivate MAPK signaling and bypass RAF inhibition.",
            raw_content="Secondary NRAS Q61K mutations frequently reactivate MAPK signaling and bypass RAF inhibition.",
        ),
    ]


def test_generator_grounded_answer(sample_evidence):
    generator = BioRAGGenerator()  # Operates in mock/fallback mode without API key
    query = "What is the efficacy of dabrafenib in BRAF V600E melanoma?"

    response = generator.generate(query, sample_evidence)

    assert response.query == query
    assert response.has_sufficient_evidence is True
    assert len(response.citations) > 0
    assert response.confidence_score > 0.5

    # Check citation mapping
    cit = response.citations[0]
    assert cit.pmid in ("380001", "380002")
    assert cit.title in ("Targeting BRAF V600E in Melanoma", "Resistance Pathways in Melanoma")


def test_generator_abstention_on_empty():
    generator = BioRAGGenerator()
    query = "What is the role of Mars gravity on mitochondrial fission?"

    response = generator.generate(query, [])

    assert response.has_sufficient_evidence is False
    assert response.abstention_reason is not None
    assert "[ABSTAIN: INSUFFICIENT_EVIDENCE]" in response.answer


def test_contradiction_parsing():
    generator = BioRAGGenerator()
    raw_text = (
        "Study A showed increased apoptosis [PMID: 380001, Sec: Results].\n\n"
        "### Conflicting or Divergent Findings\n"
        "However, Study B reported no significant difference in cell death under hypoxic conditions."
    )
    chunks = [
        DocumentChunk(
            chunk_id="c1",
            document_id="d1",
            pmid="380001",
            paper_title="Study A",
            section_name="Results",
            section_type="results",
            text="Study A content",
            raw_content="Study A content"
        )
    ]

    response = generator._build_response("Hypoxia in cancer", raw_text, chunks)
    assert len(response.conflicts_detected) == 1
    assert "Hypoxia" in response.conflicts_detected[0].topic


def test_end_to_end_biorag_pipeline(sample_evidence):
    embeddings = MockBiomedicalEmbeddings(dimension=64)
    faiss_mgr = FAISSIndexManager(embeddings=embeddings)
    faiss_mgr.build_from_chunks(sample_evidence)

    bm25_mgr = BM25IndexManager()
    bm25_mgr.build_from_chunks(sample_evidence)

    generator = BioRAGGenerator()

    pipeline = BioRAGPipeline(
        faiss_manager=faiss_mgr,
        bm25_manager=bm25_mgr,
        generator=generator,
        dense_weight=0.6,
        sparse_weight=0.4
    )

    response = pipeline.answer_question(
        query="BRAF V600E dabrafenib",
        k=2,
        mode=RetrievalMode.HYBRID_RRF
    )

    assert response.has_sufficient_evidence is True
    assert len(response.citations) > 0
    assert response.confidence_score >= 0.5
