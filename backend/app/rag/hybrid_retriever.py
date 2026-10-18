import logging
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.documents import Document

from ..models.chunk import DocumentChunk
from .vectorstore import FAISSIndexManager
from .bm25 import BM25IndexManager

logger = logging.getLogger(__name__)


class RetrievalMode(str, Enum):
    HYBRID_RRF = "hybrid_rrf"
    FAISS_MMR = "faiss_mmr"
    FAISS_COSINE = "faiss_cosine"
    BM25_ONLY = "bm25_only"


class BioHybridRetriever:
    """Hybrid retrieval engine combining FAISS dense vector search (with MMR) and BM25 sparse keyword search."""

    def __init__(
        self,
        faiss_manager: FAISSIndexManager,
        bm25_manager: BM25IndexManager,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4,
        rrf_constant: int = 60,
    ):
        self.faiss_manager = faiss_manager
        self.bm25_manager = bm25_manager
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.rrf_constant = rrf_constant

    def retrieve(
        self,
        query: str,
        k: int = 5,
        mode: RetrievalMode = RetrievalMode.HYBRID_RRF,
        fetch_k: int = 20,
        lambda_mult: float = 0.7,
    ) -> List[DocumentChunk]:
        """Execute retrieval using specified strategy and return top K DocumentChunks."""
        if mode == RetrievalMode.BM25_ONLY:
            retriever = self.bm25_manager.as_retriever(k=k)
            docs = retriever.invoke(query)
            return self._docs_to_chunks(docs[:k])

        elif mode == RetrievalMode.FAISS_COSINE:
            retriever = self.faiss_manager.as_similarity_retriever(k=k)
            docs = retriever.invoke(query)
            return self._docs_to_chunks(docs[:k])

        elif mode == RetrievalMode.FAISS_MMR:
            retriever = self.faiss_manager.as_mmr_retriever(k=k, fetch_k=fetch_k, lambda_mult=lambda_mult)
            docs = retriever.invoke(query)
            return self._docs_to_chunks(docs[:k])

        elif mode == RetrievalMode.HYBRID_RRF:
            # 1. Retrieve candidates from dense FAISS (with MMR for diversity)
            dense_retriever = self.faiss_manager.as_mmr_retriever(
                k=fetch_k, fetch_k=fetch_k * 2, lambda_mult=lambda_mult
            )
            dense_docs = dense_retriever.invoke(query)

            # 2. Retrieve candidates from sparse BM25
            sparse_retriever = self.bm25_manager.as_retriever(k=fetch_k)
            sparse_docs = sparse_retriever.invoke(query)

            # 3. Apply Reciprocal Rank Fusion (RRF)
            fused_docs = self._apply_rrf(dense_docs, sparse_docs, k=k)
            return self._docs_to_chunks(fused_docs)

        else:
            raise ValueError(f"Unknown retrieval mode: {mode}")

    def _apply_rrf(
        self,
        dense_docs: List[Document],
        sparse_docs: List[Document],
        k: int = 5
    ) -> List[Document]:
        """Compute Reciprocal Rank Fusion over dense and sparse ranked document lists."""
        rrf_scores: Dict[str, float] = {}
        doc_store: Dict[str, Document] = {}

        # Process dense ranking
        for rank, doc in enumerate(dense_docs, start=1):
            chunk_id = doc.metadata.get("chunk_id", doc.page_content[:50])
            doc_store[chunk_id] = doc
            score = self.dense_weight / (self.rrf_constant + rank)
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + score

        # Process sparse ranking
        for rank, doc in enumerate(sparse_docs, start=1):
            chunk_id = doc.metadata.get("chunk_id", doc.page_content[:50])
            doc_store[chunk_id] = doc
            score = self.sparse_weight / (self.rrf_constant + rank)
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + score

        # Sort by final RRF score descending
        sorted_chunk_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        ranked_docs: List[Document] = []
        for cid in sorted_chunk_ids[:k]:
            doc = doc_store[cid]
            # Attach computed RRF score into metadata
            doc.metadata["rrf_score"] = round(rrf_scores[cid], 5)
            ranked_docs.append(doc)

        return ranked_docs

    def _docs_to_chunks(self, docs: List[Document]) -> List[DocumentChunk]:
        """Map LangChain Document objects back to domain DocumentChunk models."""
        chunks: List[DocumentChunk] = []
        for idx, doc in enumerate(docs):
            meta = doc.metadata
            chunks.append(
                DocumentChunk(
                    chunk_id=meta.get("chunk_id", f"retrieved_chunk_{idx}"),
                    document_id=meta.get("document_id", "UNKNOWN"),
                    pmid=meta.get("pmid") or None,
                    pmcid=meta.get("pmcid") or None,
                    doi=meta.get("doi") or None,
                    paper_title=meta.get("paper_title", "Untitled Document"),
                    journal=meta.get("journal") or None,
                    publication_year=meta.get("publication_year") or None,
                    section_name=meta.get("section_name", "Content"),
                    section_type=meta.get("section_type", "other"),
                    chunk_index=meta.get("chunk_index", idx),
                    token_count=meta.get("token_count", 0),
                    text=doc.page_content,
                    raw_content=doc.page_content,
                )
            )
        return chunks
