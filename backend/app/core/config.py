import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings and environment configurations for BioRAG."""
    APP_NAME: str = "BioRAG"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Redirect model caches to D: drive on Windows if present, or honor existing env
    if os.name == 'nt' and os.path.exists('D:\\'):
        os.environ.setdefault("HF_HOME", "D:/hf_cache")
        os.environ.setdefault("TORCH_HOME", "D:/torch_cache")
        os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", "D:/hf_cache")

    # LLM Settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    DEFAULT_LLM_MODEL: str = "llama-3.3-70b-versatile"
    FAST_LLM_MODEL: str = "llama-3.1-8b-instant"
    
    # Vector & Retrieval Settings
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    FAISS_INDEX_DIR: str = "data/indices/faiss"
    BM25_INDEX_PATH: str = "data/indices/bm25/bm25.pkl"
    MANIFEST_DB_PATH: str = "data/metadata.db"
    RAW_PAPERS_DIR: str = "data/raw/papers"
    BENCHMARKS_DIR: str = "data/benchmarks"
    BENCHMARK_RESULTS_DIR: str = "data/benchmarks/results"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
