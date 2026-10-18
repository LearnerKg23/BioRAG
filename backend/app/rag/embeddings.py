import logging
from typing import Optional, List
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)


class MockBiomedicalEmbeddings(Embeddings):
    """Deterministic lightweight embedding fallback for rapid testing and low-memory environments."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _embed_text(self, text: str) -> List[float]:
        import hashlib
        import math
        # Generate pseudo-semantic deterministic vector based on token hashes
        tokens = text.lower().split()
        vec = [0.0] * self.dimension
        if not tokens:
            return vec

        for i, t in enumerate(tokens):
            h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
            for d in range(self.dimension):
                # Modulated deterministic feature
                weight = math.sin((h + d * 31) % 1000)
                vec[d] += weight

        # L2 Normalize
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_text(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed_text(text)


class EmbeddingFactory:
    """Provides unified access to HuggingFace biomedical and general embedding models."""

    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    BIOMEDICAL_MODEL = "NeuML/pubmedbert-base-embeddings"

    @classmethod
    def get_embeddings(
        cls,
        model_name: Optional[str] = None,
        use_mock: bool = False,
        device: str = "cpu"
    ) -> Embeddings:
        """Create and return a LangChain-compatible Embeddings instance."""
        if use_mock:
            logger.info("Using lightweight MockBiomedicalEmbeddings")
            return MockBiomedicalEmbeddings()

        target_model = model_name or cls.DEFAULT_MODEL
        logger.info(f"Loading embedding model: {target_model} on device: {device}")

        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            return HuggingFaceEmbeddings(
                model_name=target_model,
                model_kwargs={"device": device},
                encode_kwargs={"normalize_embeddings": True}
            )
        except Exception as e:
            logger.warning(f"Failed to load HuggingFaceEmbeddings ({e}), falling back to deterministic embedding.")
            return MockBiomedicalEmbeddings()
