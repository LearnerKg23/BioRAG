from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..core.config import settings
from ..models.chunk import DocumentChunk
from ..rag.vectorstore import FAISSIndexManager
from ..rag.bm25 import BM25IndexManager
from ..rag.hybrid_retriever import BioHybridRetriever, RetrievalMode

router = APIRouter(prefix="/api/retrieval", tags=["retrieval"])


class RetrievalInspectRequest(BaseModel):
    query: str = Field(..., description="Query string to evaluate")
    k: int = Field(5, ge=1, le=20, description="Top-K passages to retrieve")
    mode: RetrievalMode = Field(RetrievalMode.HYBRID_RRF, description="Retrieval strategy: hybrid_rrf, faiss_mmr, faiss_cosine, bm25_only")


@router.post("/inspect")
def inspect_retrieval(req: RetrievalInspectRequest):
    """Retrieve and inspect ranked passages and scores without generating an answer."""
    faiss_mgr = FAISSIndexManager(index_dir=settings.FAISS_INDEX_DIR)
    bm25_mgr = BM25IndexManager(index_path=settings.BM25_INDEX_PATH)

    faiss_loaded = faiss_mgr.load()
    bm25_loaded = bm25_mgr.load()

    if not faiss_loaded and not bm25_loaded:
        raise HTTPException(
            status_code=404,
            detail="No indices available. Please ingest papers first using POST /api/papers/ingest."
        )

    hybrid = BioHybridRetriever(faiss_manager=faiss_mgr, bm25_manager=bm25_mgr)
    chunks = hybrid.retrieve(query=req.query, k=req.k, mode=req.mode)

    return {
        "query": req.query,
        "mode": req.mode.value,
        "retrieved_count": len(chunks),
        "chunks": [c.model_dump() for c in chunks]
    }
