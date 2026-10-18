import os
import logging
from typing import List, Optional, Tuple, Any
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStoreRetriever

from ..models.chunk import DocumentChunk
from .embeddings import EmbeddingFactory

logger = logging.getLogger(__name__)


class FAISSIndexManager:
    """Manages creation, serialization, and retrieval for the FAISS dense vector store."""

    DEFAULT_INDEX_DIR = "data/indices/faiss"

    def __init__(
        self,
        index_dir: str = DEFAULT_INDEX_DIR,
        embeddings: Optional[Embeddings] = None
    ):
        self.index_dir = index_dir
        self.embeddings = embeddings or EmbeddingFactory.get_embeddings()
        self.vectorstore: Optional[FAISS] = None

    def build_from_chunks(self, chunks: List[DocumentChunk]) -> FAISS:
        """Construct FAISS index from a list of DocumentChunks."""
        if not chunks:
            raise ValueError("Cannot build FAISS index from empty chunk list.")

        docs = [
            Document(
                page_content=c.text,
                metadata=c.to_metadata_dict()
            )
            for c in chunks
        ]

        logger.info(f"Building FAISS vector index with {len(docs)} documents...")
        self.vectorstore = FAISS.from_documents(docs, self.embeddings)
        return self.vectorstore

    def save(self, target_dir: Optional[str] = None):
        """Persist vector index to disk."""
        if self.vectorstore is None:
            raise ValueError("No active vectorstore to save.")
        out_dir = target_dir or self.index_dir
        os.makedirs(out_dir, exist_ok=True)
        self.vectorstore.save_local(out_dir)
        logger.info(f"Saved FAISS index to {out_dir}")

    def load(self, source_dir: Optional[str] = None) -> bool:
        """Load persisted FAISS index from disk."""
        in_dir = source_dir or self.index_dir
        if not os.path.exists(in_dir):
            logger.warning(f"FAISS index directory does not exist: {in_dir}")
            return False

        try:
            self.vectorstore = FAISS.load_local(
                in_dir,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info(f"Loaded FAISS index from {in_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to load FAISS index from {in_dir}: {e}")
            return False

    def as_similarity_retriever(self, k: int = 5) -> VectorStoreRetriever:
        """Returns standard cosine similarity retriever."""
        if self.vectorstore is None:
            raise ValueError("Vectorstore is not initialized or loaded.")
        return self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )

    def as_mmr_retriever(
        self,
        k: int = 5,
        fetch_k: int = 20,
        lambda_mult: float = 0.7
    ) -> VectorStoreRetriever:
        """Returns Maximal Marginal Relevance (MMR) retriever to reduce redundant excerpts."""
        if self.vectorstore is None:
            raise ValueError("Vectorstore is not initialized or loaded.")
        return self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": k, "fetch_k": fetch_k, "lambda_mult": lambda_mult}
        )
