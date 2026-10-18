import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.logging import setup_logging
from .api.routes_chat import router as chat_router
from .api.routes_papers import router as papers_router
from .api.routes_retrieval import router as retrieval_router
from .api.routes_benchmark import router as benchmark_router

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    # Ensure data directory hierarchy exists on startup
    os.makedirs(settings.FAISS_INDEX_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(settings.BM25_INDEX_PATH), exist_ok=True)
    os.makedirs(settings.RAW_PAPERS_DIR, exist_ok=True)
    os.makedirs(settings.BENCHMARK_RESULTS_DIR, exist_ok=True)
    manifest_dir = os.path.dirname(settings.MANIFEST_DB_PATH)
    if manifest_dir:
        os.makedirs(manifest_dir, exist_ok=True)
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="BioRAG: Evidence-Based Biomedical Research Assistant using Retrieval-Augmented Generation.",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(chat_router)
app.include_router(papers_router)
app.include_router(retrieval_router)
app.include_router(benchmark_router)


@app.get("/", tags=["system"])
def root_info():
    """BioRAG System Information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs_url": "/docs",
        "description": "Evidence-Based Biomedical Research Assistant using Hybrid RAG."
    }


@app.get("/api/health", tags=["system"])
def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "groq_configured": bool(settings.GROQ_API_KEY),
        "embedding_model": settings.EMBEDDING_MODEL_NAME
    }
