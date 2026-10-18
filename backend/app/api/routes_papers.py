import os
from typing import List, Optional
from fastapi import APIRouter, Query, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from ..core.config import settings
from ..ingestion.europe_pmc import EuropePMCClient
from ..ingestion.manifest import DocumentManifest
from ..rag.chunker import BiomedicalSectionChunker
from ..rag.vectorstore import FAISSIndexManager
from ..rag.bm25 import BM25IndexManager

router = APIRouter(prefix="/api/papers", tags=["papers"])


class IngestRequest(BaseModel):
    query: str = Field(..., description="Europe PMC search query to ingest papers for")
    limit: int = Field(5, ge=1, le=50, description="Max papers to ingest and index")


def _run_ingest_and_index(query: str, limit: int):
    """Background task to fetch, chunk, and update FAISS/BM25 indices."""
    manifest = DocumentManifest(db_path=settings.MANIFEST_DB_PATH)
    os.makedirs(settings.RAW_PAPERS_DIR, exist_ok=True)
    chunker = BiomedicalSectionChunker()

    with EuropePMCClient() as client:
        articles = client.search_and_ingest(query=query, limit=limit)

    all_new_chunks = []
    for art in articles:
        file_path = os.path.join(settings.RAW_PAPERS_DIR, f"{art.id.replace('/', '_')}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(art.model_dump_json(indent=2))
        manifest.add_article(art, file_path=file_path)
        chunks = chunker.chunk_article(art)
        all_new_chunks.extend(chunks)

    if all_new_chunks:
        # Build/update FAISS
        faiss_mgr = FAISSIndexManager(index_dir=settings.FAISS_INDEX_DIR)
        faiss_mgr.build_from_chunks(all_new_chunks)
        faiss_mgr.save()

        # Build/update BM25
        bm25_mgr = BM25IndexManager(index_path=settings.BM25_INDEX_PATH)
        bm25_mgr.build_from_chunks(all_new_chunks)
        bm25_mgr.save()


@router.get("/search")
def search_europe_pmc(
    query: str = Query(..., description="Biomedical search terms"),
    limit: int = Query(10, ge=1, le=50)
):
    """Search Europe PMC live and return article abstracts with open-access status."""
    with EuropePMCClient() as client:
        results = client.search_articles(query, limit=limit, open_access_only=False)
    return {"query": query, "count": len(results), "articles": results}


@router.post("/ingest")
def ingest_papers(req: IngestRequest, background_tasks: BackgroundTasks):
    """Trigger background job to ingest, chunk, and index literature into BioRAG."""
    background_tasks.add_task(_run_ingest_and_index, req.query, req.limit)
    return {
        "status": "accepted",
        "message": f"Background ingestion started for '{req.query}' (limit: {req.limit}). Indices will update shortly."
    }


@router.get("/stats")
def get_corpus_stats():
    """Retrieve corpus statistics from the document manifest."""
    manifest = DocumentManifest(db_path=settings.MANIFEST_DB_PATH)
    stats = manifest.get_stats()
    
    faiss_exists = os.path.exists(settings.FAISS_INDEX_DIR)
    bm25_exists = os.path.exists(settings.BM25_INDEX_PATH)

    stats["faiss_index_ready"] = faiss_exists
    stats["bm25_index_ready"] = bm25_exists
    return stats


@router.get("/list")
def list_ingested_papers(limit: int = 50, offset: int = 0):
    """List ingested articles tracked in manifest."""
    manifest = DocumentManifest(db_path=settings.MANIFEST_DB_PATH)
    articles = manifest.list_articles(limit=limit, offset=offset)
    return {"total": len(articles), "articles": articles}
