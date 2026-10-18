import os
import json
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from ..core.config import settings
from ..rag.vectorstore import FAISSIndexManager
from ..rag.bm25 import BM25IndexManager
from ..rag.hybrid_retriever import BioHybridRetriever, RetrievalMode
from ..rag.generator import BioRAGGenerator
from ..rag.pipeline import BioRAGPipeline
from ..evaluation.experiment_runner import BenchmarkRunner

router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])


class ExecuteBenchmarkRequest(BaseModel):
    mode: RetrievalMode = Field(RetrievalMode.HYBRID_RRF, description="Retrieval strategy to benchmark")
    k: int = Field(5, ge=1, le=10, description="Top-K context size")
    run_name: Optional[str] = Field(None, description="Custom name/tag for this evaluation run")


def _run_benchmark_job(mode: RetrievalMode, k: int, run_name: Optional[str]):
    faiss_mgr = FAISSIndexManager(index_dir=settings.FAISS_INDEX_DIR)
    bm25_mgr = BM25IndexManager(index_path=settings.BM25_INDEX_PATH)
    faiss_mgr.load()
    bm25_mgr.load()

    generator = BioRAGGenerator()
    pipeline = BioRAGPipeline(faiss_manager=faiss_mgr, bm25_manager=bm25_mgr, generator=generator)

    dataset_path = os.path.join(settings.BENCHMARKS_DIR, "benchmark_dataset.json")
    runner = BenchmarkRunner(
        pipeline=pipeline,
        dataset_path=dataset_path,
        results_dir=settings.BENCHMARK_RESULTS_DIR
    )
    runner.run_strategy_benchmark(mode=mode, k=k, run_name=run_name)


@router.get("/runs")
def list_benchmark_runs():
    """List all completed benchmark runs and their summary statistics."""
    os.makedirs(settings.BENCHMARK_RESULTS_DIR, exist_ok=True)
    runs = []

    for fname in sorted(os.listdir(settings.BENCHMARK_RESULTS_DIR), reverse=True):
        if fname.endswith(".json"):
            fpath = os.path.join(settings.BENCHMARK_RESULTS_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    runs.append({
                        "run_id": data.get("run_id"),
                        "run_name": data.get("run_name"),
                        "retrieval_mode": data.get("retrieval_mode"),
                        "k": data.get("k"),
                        "mean_reciprocal_rank": data.get("mean_reciprocal_rank"),
                        "mean_recall@5": data.get("mean_recall@5"),
                        "mean_ndcg@5": data.get("mean_ndcg@5"),
                        "mean_latency_ms": data.get("mean_latency_ms"),
                        "abstention_accuracy": data.get("abstention_accuracy"),
                        "timestamp": data.get("timestamp"),
                    })
            except Exception:
                continue

    return {"total_runs": len(runs), "runs": runs}


@router.get("/runs/{run_id}")
def get_benchmark_run_detail(run_id: str):
    """Retrieve complete metrics and per-question breakdowns for a specific run."""
    clean_id = os.path.basename(run_id).replace(".json", "")
    fpath = os.path.join(settings.BENCHMARK_RESULTS_DIR, f"{clean_id}.json")

    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail=f"Benchmark run '{run_id}' not found.")

    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)


@router.post("/execute")
def execute_benchmark(req: ExecuteBenchmarkRequest, background_tasks: BackgroundTasks):
    """Trigger an evaluation run across the benchmark dataset."""
    background_tasks.add_task(_run_benchmark_job, req.mode, req.k, req.run_name)
    return {
        "status": "accepted",
        "message": f"Benchmark job queued for {req.mode.value} (k={req.k}). Results will be recorded in /api/benchmark/runs."
    }


@router.get("/dataset")
def get_benchmark_dataset():
    """Retrieve benchmark QA test questions and ground-truth metadata."""
    dataset_path = os.path.join(settings.BENCHMARKS_DIR, "benchmark_dataset.json")
    if not os.path.exists(dataset_path):
        raise HTTPException(status_code=404, detail="Benchmark dataset not found.")

    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)
