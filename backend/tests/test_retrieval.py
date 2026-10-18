import pytest
from backend.app.models.chunk import DocumentChunk
from backend.app.rag.embeddings import MockBiomedicalEmbeddings
from backend.app.rag.vectorstore import FAISSIndexManager
from backend.app.rag.bm25 import BM25IndexManager
from backend.app.rag.hybrid_retriever import BioHybridRetriever, RetrievalMode


@pytest.fixture
def sample_chunks():
    return [
        DocumentChunk(
            chunk_id="chunk_01",
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
            token_count=50,
            text="[Paper: Targeting BRAF V600E in Melanoma | Section: Results]\nDabrafenib combined with trametinib significantly prolonged progression-free survival in BRAF V600E metastatic melanoma patients.",
            raw_content="Dabrafenib combined with trametinib significantly prolonged progression-free survival in BRAF V600E metastatic melanoma patients.",
        ),
        DocumentChunk(
            chunk_id="chunk_02",
            document_id="PMC1002",
            pmid="380002",
            pmcid="PMC1002",
            doi="10.1038/s41586-024-002",
            paper_title="EGFR T790M Resistance in Lung Adenocarcinoma",
            journal="Cell",
            publication_year=2024,
            section_name="Results",
            section_type="results",
            chunk_index=0,
            token_count=50,
            text="[Paper: EGFR T790M Resistance in Lung Adenocarcinoma | Section: Results]\nOsimertinib selectively overcomes the EGFR T790M gatekeeper mutation in non-small cell lung cancer.",
            raw_content="Osimertinib selectively overcomes the EGFR T790M gatekeeper mutation in non-small cell lung cancer.",
        ),
        DocumentChunk(
            chunk_id="chunk_03",
            document_id="PMC1003",
            pmid="380003",
            pmcid="PMC1003",
            doi="10.1038/s41586-024-003",
            paper_title="Immunotherapy in Triple-Negative Breast Cancer",
            journal="Lancet Oncology",
            publication_year=2023,
            section_name="Discussion",
            section_type="discussion",
            chunk_index=0,
            token_count=50,
            text="[Paper: Immunotherapy in Triple-Negative Breast Cancer | Section: Discussion]\nPembrolizumab plus chemotherapy improved pathological complete response rates in PD-L1 positive TNBC.",
            raw_content="Pembrolizumab plus chemotherapy improved pathological complete response rates in PD-L1 positive TNBC.",
        ),
    ]


def test_faiss_index_manager(sample_chunks, tmp_path):
    embeddings = MockBiomedicalEmbeddings(dimension=64)
    manager = FAISSIndexManager(index_dir=str(tmp_path / "faiss"), embeddings=embeddings)

    # Build
    manager.build_from_chunks(sample_chunks)
    assert manager.vectorstore is not None

    # Save and reload
    manager.save()
    loaded_manager = FAISSIndexManager(index_dir=str(tmp_path / "faiss"), embeddings=embeddings)
    assert loaded_manager.load()

    # Similarity retrieval
    sim_retriever = loaded_manager.as_similarity_retriever(k=2)
    results = sim_retriever.invoke("BRAF melanoma")
    assert len(results) == 2

    # MMR retrieval
    mmr_retriever = loaded_manager.as_mmr_retriever(k=2, fetch_k=3, lambda_mult=0.7)
    mmr_results = mmr_retriever.invoke("BRAF melanoma")
    assert len(mmr_results) == 2


def test_bm25_index_manager(sample_chunks, tmp_path):
    bm25_file = str(tmp_path / "bm25" / "bm25.pkl")
    manager = BM25IndexManager(index_path=bm25_file)

    # Build
    manager.build_from_chunks(sample_chunks, k=2)

    # Keyword search for specific mutation
    retriever = manager.as_retriever(k=1)
    results = retriever.invoke("EGFR T790M")
    assert len(results) == 1
    assert "T790M" in results[0].page_content
    assert results[0].metadata["chunk_id"] == "chunk_02"

    # Save and reload
    manager.save()
    loaded_manager = BM25IndexManager(index_path=bm25_file)
    assert loaded_manager.load()

    reloaded_retriever = loaded_manager.as_retriever(k=1)
    reloaded_results = reloaded_retriever.invoke("Dabrafenib")
    assert len(reloaded_results) == 1
    assert results[0].metadata["chunk_id"] in ("chunk_01", "chunk_02")


def test_bio_hybrid_retriever(sample_chunks):
    embeddings = MockBiomedicalEmbeddings(dimension=64)
    faiss_mgr = FAISSIndexManager(embeddings=embeddings)
    faiss_mgr.build_from_chunks(sample_chunks)

    bm25_mgr = BM25IndexManager()
    bm25_mgr.build_from_chunks(sample_chunks)

    hybrid = BioHybridRetriever(
        faiss_manager=faiss_mgr,
        bm25_manager=bm25_mgr,
        dense_weight=0.6,
        sparse_weight=0.4
    )

    # Test Hybrid RRF
    rrf_chunks = hybrid.retrieve("BRAF V600E melanoma", k=2, mode=RetrievalMode.HYBRID_RRF)
    assert len(rrf_chunks) == 2
    assert rrf_chunks[0].chunk_id == "chunk_01"
    assert rrf_chunks[0].paper_title == "Targeting BRAF V600E in Melanoma"
    assert rrf_chunks[0].pmid == "380001"

    # Test individual modes
    bm25_chunks = hybrid.retrieve("Osimertinib", k=1, mode=RetrievalMode.BM25_ONLY)
    assert len(bm25_chunks) == 1
    assert bm25_chunks[0].chunk_id == "chunk_02"

    mmr_chunks = hybrid.retrieve("PD-L1 immunotherapy", k=1, mode=RetrievalMode.FAISS_MMR)
    assert len(mmr_chunks) == 1
