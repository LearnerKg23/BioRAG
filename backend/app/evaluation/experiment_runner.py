import os
import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from ..rag.hybrid_retriever import BioHybridRetriever, RetrievalMode
from ..rag.pipeline import BioRAGPipeline
from .ir_metrics import IRMetrics


class BenchmarkRunner:
    """Executes systematic quantitative evaluations comparing retrieval strategies, chunking modes, and latency."""

    DEFAULT_DATASET_PATH = "data/benchmarks/benchmark_dataset.json"
    RESULTS_DIR = "data/benchmarks/results"

    def __init__(
        self,
        pipeline: BioRAGPipeline,
        dataset_path: str = DEFAULT_DATASET_PATH,
        results_dir: str = RESULTS_DIR,
    ):
        self.pipeline = pipeline
        self.dataset_path = dataset_path
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)

    def load_dataset(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Benchmark dataset not found at {self.dataset_path}")
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def run_strategy_benchmark(
        self,
        mode: RetrievalMode = RetrievalMode.HYBRID_RRF,
        k: int = 5,
        run_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute evaluation over all benchmark questions for a specific retrieval configuration."""
        dataset = self.load_dataset()
        start_time = time.perf_counter()

        per_question_results: List[Dict[str, Any]] = []
        rr_list: List[float] = []
        recall_1_list: List[float] = []
        recall_3_list: List[float] = []
        recall_5_list: List[float] = []
        ndcg_5_list: List[float] = []
        latencies_ms: List[float] = []
        abstention_correct = 0
        abstention_total = 0

        for item in dataset:
            q_id = item["question_id"]
            query = item["question"]
            ground_truth = set(item.get("ground_truth_pmids", []))
            is_answerable = item.get("is_answerable", True)

            q_start = time.perf_counter()
            response = self.pipeline.answer_question(query=query, k=k, mode=mode)
            q_latency = (time.perf_counter() - q_start) * 1000
            latencies_ms.append(q_latency)

            # Evaluate Abstention accuracy
            if not is_answerable:
                abstention_total += 1
                if not response.has_sufficient_evidence:
                    abstention_correct += 1

            # Extract retrieved doc identifiers
            retrieved_ids = []
            for c in response.citations:
                if c.pmid:
                    retrieved_ids.append(c.pmid)
                if c.pmcid:
                    retrieved_ids.append(c.pmcid)
                retrieved_ids.append(c.chunk_id)

            # Compute IR metrics if ground truth exists
            metrics = {}
            if ground_truth:
                metrics = IRMetrics.evaluate_query(retrieved_ids, ground_truth, k_values=(1, 3, 5))
                rr_list.append(metrics.get("reciprocal_rank", 0.0))
                recall_1_list.append(metrics.get("recall@1", 0.0))
                recall_3_list.append(metrics.get("recall@3", 0.0))
                recall_5_list.append(metrics.get("recall@5", 0.0))
                ndcg_5_list.append(metrics.get("ndcg@5", 0.0))

            per_question_results.append({
                "question_id": q_id,
                "question": query,
                "is_answerable": is_answerable,
                "has_sufficient_evidence": response.has_sufficient_evidence,
                "confidence_score": response.confidence_score,
                "latency_ms": round(q_latency, 2),
                "metrics": metrics,
            })

        total_duration = time.perf_counter() - start_time
        num_answerable = len(rr_list) or 1

        summary = {
            "run_id": f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "run_name": run_name or f"eval_{mode.value}_k{k}",
            "retrieval_mode": mode.value,
            "k": k,
            "total_questions": len(dataset),
            "mean_reciprocal_rank": round(sum(rr_list) / num_answerable, 4) if rr_list else 0.0,
            "mean_recall@1": round(sum(recall_1_list) / num_answerable, 4) if recall_1_list else 0.0,
            "mean_recall@3": round(sum(recall_3_list) / num_answerable, 4) if recall_3_list else 0.0,
            "mean_recall@5": round(sum(recall_5_list) / num_answerable, 4) if recall_5_list else 0.0,
            "mean_ndcg@5": round(sum(ndcg_5_list) / num_answerable, 4) if ndcg_5_list else 0.0,
            "mean_latency_ms": round(sum(latencies_ms) / len(latencies_ms), 2) if latencies_ms else 0.0,
            "abstention_accuracy": round(abstention_correct / abstention_total, 4) if abstention_total else 1.0,
            "duration_seconds": round(total_duration, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "per_question_results": per_question_results,
        }

        # Save to disk
        out_file = os.path.join(self.results_dir, f"{summary['run_id']}.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return summary

    def run_multi_strategy_comparison(self, k: int = 5) -> List[Dict[str, Any]]:
        """Run comparison across all retrieval modes for benchmarking dashboard."""
        strategies = [
            RetrievalMode.BM25_ONLY,
            RetrievalMode.FAISS_COSINE,
            RetrievalMode.FAISS_MMR,
            RetrievalMode.HYBRID_RRF,
        ]
        results = []
        for s in strategies:
            res = self.run_strategy_benchmark(mode=s, k=k)
            results.append(res)
        return results
