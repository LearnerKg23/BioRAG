import pytest
from backend.app.models.chunk import DocumentChunk
from backend.app.rag.embeddings import MockBiomedicalEmbeddings
from backend.app.rag.vectorstore import FAISSIndexManager
from backend.app.rag.bm25 import BM25IndexManager
from backend.app.rag.generator import BioRAGGenerator
from backend.app.rag.pipeline import BioRAGPipeline
from backend.app.rag.hybrid_retriever import RetrievalMode
from backend.app.evaluation.ir_metrics import IRMetrics
from backend.app.evaluation.ragas_eval import RagasEvaluator
from backend.app.evaluation.experiment_runner import BenchmarkRunner


def test_ir_metrics_calculation():
    retrieved = ["doc_A", "doc_B", "doc_C", "doc_D", "doc_E"]
    relevant = {"doc_B", "doc_E"}

    # Precision
    assert IRMetrics.precision_at_k(retrieved, relevant, k=1) == 0.0
    assert IRMetrics.precision_at_k(retrieved, relevant, k=2) == 0.5
    assert IRMetrics.precision_at_k(retrieved, relevant, k=5) == 0.4

    # Recall
    assert IRMetrics.recall_at_k(retrieved, relevant, k=1) == 0.0
    assert IRMetrics.recall_at_k(retrieved, relevant, k=2) == 0.5
    assert IRMetrics.recall_at_k(retrieved, relevant, k=5) == 1.0

    # Reciprocal Rank (first relevant is doc_B at rank 2 -> 1/2 = 0.5)
    assert IRMetrics.reciprocal_rank(retrieved, relevant) == 0.5

    # nDCG
    ndcg = IRMetrics.ndcg_at_k(retrieved, relevant, k=5)
    assert 0.0 < ndcg <= 1.0


def test_ragas_evaluator():
    context = [
        "Dabrafenib combined with trametinib suppresses ERK phosphorylation and inhibits tumor growth in BRAF V600E melanoma."
    ]
    grounded_answer = "Dabrafenib combined with trametinib suppresses ERK phosphorylation in melanoma."
    ungrounded_answer = "Patients should be administered aspirin and penicillin to treat bacterial meningitis."

    faith_grounded = RagasEvaluator.calculate_faithfulness(grounded_answer, context)
    faith_ungrounded = RagasEvaluator.calculate_faithfulness(ungrounded_answer, context)

    assert faith_grounded > faith_ungrounded
    assert faith_grounded >= 0.8
    assert faith_ungrounded <= 0.2

    relevance = RagasEvaluator.calculate_answer_relevance("Dabrafenib melanoma", grounded_answer)
    assert relevance >= 0.5


def test_benchmark_runner_execution(tmp_path):
    chunks = [
        DocumentChunk(
            chunk_id="PMC1001_chunk_0",
            document_id="PMC1001",
            pmid="38123456",
            paper_title="Dabrafenib in Melanoma",
            section_name="Results",
            section_type="results",
            text="Dabrafenib blocks hyperactive MAPK signaling in BRAF V600E melanoma.",
            raw_content="Dabrafenib blocks hyperactive MAPK signaling in BRAF V600E melanoma.",
        ),
        DocumentChunk(
            chunk_id="PMC1002_chunk_0",
            document_id="PMC1002",
            pmid="380002",
            paper_title="Osimertinib in NSCLC",
            section_name="Results",
            section_type="results",
            text="Osimertinib selectively overcomes the EGFR T790M gatekeeper mutation in NSCLC.",
            raw_content="Osimertinib selectively overcomes the EGFR T790M gatekeeper mutation in NSCLC.",
        ),
    ]

    embeddings = MockBiomedicalEmbeddings(dimension=64)
    faiss_mgr = FAISSIndexManager(embeddings=embeddings)
    faiss_mgr.build_from_chunks(chunks)

    bm25_mgr = BM25IndexManager()
    bm25_mgr.build_from_chunks(chunks)

    generator = BioRAGGenerator()
    pipeline = BioRAGPipeline(
        faiss_manager=faiss_mgr,
        bm25_manager=bm25_mgr,
        generator=generator
    )

    runner = BenchmarkRunner(
        pipeline=pipeline,
        dataset_path="data/benchmarks/benchmark_dataset.json",
        results_dir=str(tmp_path / "results")
    )

    results = runner.run_strategy_benchmark(mode=RetrievalMode.HYBRID_RRF, k=3)

    assert "mean_reciprocal_rank" in results
    assert "mean_recall@3" in results
    assert "abstention_accuracy" in results
    assert len(results["per_question_results"]) == 5
