import json
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..core.config import settings
from ..models.response import BioRAGResponse
from ..rag.vectorstore import FAISSIndexManager
from ..rag.bm25 import BM25IndexManager
from ..rag.hybrid_retriever import BioHybridRetriever, RetrievalMode
from ..rag.generator import BioRAGGenerator
from ..rag.pipeline import BioRAGPipeline

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatQueryRequest(BaseModel):
    query: str = Field(..., description="Biomedical research question")
    k: int = Field(5, ge=1, le=15, description="Number of context passages to retrieve")
    mode: RetrievalMode = Field(RetrievalMode.HYBRID_RRF, description="Retrieval strategy")


def _get_pipeline() -> BioRAGPipeline:
    """Helper to initialize pipeline with current indices."""
    faiss_mgr = FAISSIndexManager(index_dir=settings.FAISS_INDEX_DIR)
    bm25_mgr = BM25IndexManager(index_path=settings.BM25_INDEX_PATH)
    faiss_mgr.load()
    bm25_mgr.load()

    generator = BioRAGGenerator(
        api_key=settings.GROQ_API_KEY,
        model_name=settings.DEFAULT_LLM_MODEL
    )

    return BioRAGPipeline(
        faiss_manager=faiss_mgr,
        bm25_manager=bm25_mgr,
        generator=generator
    )


@router.post("/query", response_model=BioRAGResponse)
def query_biorag(req: ChatQueryRequest):
    """Execute end-to-end question answering with verifiable citations and contradiction detection."""
    pipeline = _get_pipeline()
    response = pipeline.answer_question(query=req.query, k=req.k, mode=req.mode)
    return response


@router.get("/stream")
async def stream_biorag_answer(
    query: str = Query(..., description="Biomedical research query"),
    k: int = Query(5, ge=1, le=15),
    mode: RetrievalMode = Query(RetrievalMode.HYBRID_RRF)
):
    """Server-Sent Events (SSE) streaming endpoint for real-time answer generation."""
    pipeline = _get_pipeline()

    # 1. Retrieve chunks
    chunks = pipeline.retriever.retrieve(query=query, k=k, mode=mode)

    async def event_generator():
        # First event: emit retrieved sources
        sources_payload = [
            {
                "chunk_id": c.chunk_id,
                "pmid": c.pmid,
                "title": c.paper_title,
                "section": c.section_name,
                "text": c.raw_content[:200] + "..."
            }
            for c in chunks
        ]
        yield f"event: sources\ndata: {json.dumps(sources_payload)}\n\n"

        # Stream tokens
        async for token in pipeline.generator.astream_generate(query=query, chunks=chunks):
            yield f"event: token\ndata: {json.dumps(token)}\n\n"

        # Final event
        yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
