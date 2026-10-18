import os
import re
import pickle
import logging
from typing import List, Optional, Tuple, Callable
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_community.retrievers import BM25Retriever
from pydantic import Field

from ..models.chunk import DocumentChunk

logger = logging.getLogger(__name__)


def biomedical_tokenizer(text: str) -> List[str]:
    """Tokenize biomedical text preserving alphanumeric gene and mutation codes."""
    # Split on whitespace and non-alphanumeric characters, except hyphens inside words
    tokens = re.findall(r"\b[A-Za-z0-9_\-\.]+\b", text.lower())
    return tokens


class BM25IndexManager:
    """Manages creation, serialization, and retrieval for the BM25 sparse keyword index."""

    DEFAULT_INDEX_PATH = "data/indices/bm25/bm25.pkl"

    def __init__(
        self,
        index_path: str = DEFAULT_INDEX_PATH,
        preprocess_func: Optional[Callable[[str], List[str]]] = None
    ):
        self.index_path = index_path
        self.preprocess_func = preprocess_func or biomedical_tokenizer
        self.retriever: Optional[BM25Retriever] = None
        self.docs: List[Document] = []

    def build_from_chunks(self, chunks: List[DocumentChunk], k: int = 5) -> BM25Retriever:
        """Construct BM25 index from DocumentChunks."""
        if not chunks:
            raise ValueError("Cannot build BM25 index from empty chunk list.")

        self.docs = [
            Document(
                page_content=c.text,
                metadata=c.to_metadata_dict()
            )
            for c in chunks
        ]

        logger.info(f"Building BM25 sparse index with {len(self.docs)} documents...")
        self.retriever = BM25Retriever.from_documents(
            self.docs,
            preprocess_func=self.preprocess_func,
            k=k
        )
        return self.retriever

    def save(self, target_path: Optional[str] = None):
        """Persist BM25 index to disk via pickle."""
        if self.retriever is None or not self.docs:
            raise ValueError("No active BM25 index to save.")
        out_path = target_path or self.index_path
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        payload = {
            "docs": self.docs,
            "k": getattr(self.retriever, "k", 5)
        }
        with open(out_path, "wb") as f:
            pickle.dump(payload, f)
        logger.info(f"Saved BM25 index to {out_path}")

    def load(self, source_path: Optional[str] = None) -> bool:
        """Load persisted BM25 index from disk."""
        in_path = source_path or self.index_path
        if not os.path.exists(in_path):
            logger.warning(f"BM25 index file does not exist: {in_path}")
            return False

        try:
            with open(in_path, "rb") as f:
                payload = pickle.load(f)

            self.docs = payload.get("docs", [])
            k = payload.get("k", 5)
            self.retriever = BM25Retriever.from_documents(
                self.docs,
                preprocess_func=self.preprocess_func,
                k=k
            )
            logger.info(f"Loaded BM25 index from {in_path} ({len(self.docs)} docs)")
            return True
        except Exception as e:
            logger.error(f"Failed to load BM25 index from {in_path}: {e}")
            return False

    def as_retriever(self, k: int = 5) -> BaseRetriever:
        """Returns BM25 retriever instance."""
        if self.retriever is None:
            raise ValueError("BM25 retriever is not initialized or loaded.")
        self.retriever.k = k
        return self.retriever
