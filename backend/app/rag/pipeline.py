import logging
from typing import Optional, List, AsyncIterator
from ..models.chunk import DocumentChunk
from ..models.response import BioRAGResponse
from .vectorstore import FAISSIndexManager
from .bm25 import BM25IndexManager
from .hybrid_retriever import BioHybridRetriever, RetrievalMode
from .generator import BioRAGGenerator

logger = logging.getLogger(__name__)


class BioRAGPipeline:
    """Unified end-to-end Biomedical RAG pipeline connecting ingestion indices, hybrid retrieval, and grounded generation."""

    def __init__(
        self,
        faiss_manager: Optional[FAISSIndexManager] = None,
        bm25_manager: Optional[BM25IndexManager] = None,
        generator: Optional[BioRAGGenerator] = None,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4,
    ):
        self.faiss_manager = faiss_manager or FAISSIndexManager()
        self.bm25_manager = bm25_manager or BM25IndexManager()
        self.generator = generator or BioRAGGenerator()

        self.retriever = BioHybridRetriever(
            faiss_manager=self.faiss_manager,
            bm25_manager=self.bm25_manager,
            dense_weight=dense_weight,
            sparse_weight=sparse_weight,
        )

    def answer_question(
        self,
        query: str,
        k: int = 5,
        mode: RetrievalMode = RetrievalMode.HYBRID_RRF,
    ) -> BioRAGResponse:
        """Execute full RAG pipeline: Retrieve relevant passages and generate evidence-grounded answer."""
        logger.info(f"BioRAG pipeline querying: '{query}' [Mode: {mode}, Top-K: {k}]")
        
        # 1. Retrieve evidence chunks
        chunks = self.retriever.retrieve(query=query, k=k, mode=mode)
        
        # 2. Synthesize answer with citations and confidence scoring
        response = self.generator.generate(query=query, chunks=chunks, retrieval_mode=str(mode))
        return response

    async def astream_answer(
        self,
        query: str,
        k: int = 5,
        mode: RetrievalMode = RetrievalMode.HYBRID_RRF,
    ) -> AsyncIterator[str]:
        """Stream generated answer tokens while attaching source context."""
        chunks = self.retriever.retrieve(query=query, k=k, mode=mode)
        async for token in self.generator.astream_generate(query=query, chunks=chunks):
            yield token
