import math
from typing import List, Set, Sequence, Any


class IRMetrics:
    """Standard quantitative Information Retrieval evaluation metrics for benchmarking retrieval pipelines."""

    @staticmethod
    def precision_at_k(retrieved_ids: Sequence[str], relevant_ids: Set[str], k: int) -> float:
        """Calculate Precision@K: Fraction of top-K retrieved items that are relevant."""
        if k <= 0:
            return 0.0
        top_k = retrieved_ids[:k]
        if not top_k:
            return 0.0
        relevant_retrieved = sum(1 for doc_id in top_k if doc_id in relevant_ids)
        return relevant_retrieved / len(top_k)

    @staticmethod
    def recall_at_k(retrieved_ids: Sequence[str], relevant_ids: Set[str], k: int) -> float:
        """Calculate Recall@K: Fraction of total relevant items retrieved in top-K."""
        if not relevant_ids or k <= 0:
            return 0.0
        top_k = retrieved_ids[:k]
        relevant_retrieved = sum(1 for doc_id in top_k if doc_id in relevant_ids)
        return relevant_retrieved / len(relevant_ids)

    @staticmethod
    def reciprocal_rank(retrieved_ids: Sequence[str], relevant_ids: Set[str]) -> float:
        """Calculate Reciprocal Rank (RR): 1 / rank of the first relevant document."""
        if not relevant_ids:
            return 0.0
        for rank, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in relevant_ids:
                return 1.0 / rank
        return 0.0

    @staticmethod
    def ndcg_at_k(retrieved_ids: Sequence[str], relevant_ids: Set[str], k: int) -> float:
        """Calculate Normalized Discounted Cumulative Gain (nDCG@K) for binary relevance."""
        if not relevant_ids or k <= 0:
            return 0.0

        top_k = retrieved_ids[:k]
        dcg = 0.0
        for rank, doc_id in enumerate(top_k, start=1):
            rel = 1.0 if doc_id in relevant_ids else 0.0
            if rel > 0:
                dcg += rel / math.log2(rank + 1)

        # Ideal DCG (all relevant docs ranked at top)
        ideal_k = min(len(relevant_ids), k)
        idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_k + 1))

        if idcg == 0.0:
            return 0.0
        return dcg / idcg

    @classmethod
    def evaluate_query(
        cls,
        retrieved_ids: Sequence[str],
        relevant_ids: Set[str],
        k_values: Sequence[int] = (1, 3, 5, 10)
    ) -> dict:
        """Compute complete metric suite for a single query."""
        results = {
            "reciprocal_rank": cls.reciprocal_rank(retrieved_ids, relevant_ids)
        }
        for k in k_values:
            results[f"recall@{k}"] = round(cls.recall_at_k(retrieved_ids, relevant_ids, k), 4)
            results[f"precision@{k}"] = round(cls.precision_at_k(retrieved_ids, relevant_ids, k), 4)
            results[f"ndcg@{k}"] = round(cls.ndcg_at_k(retrieved_ids, relevant_ids, k), 4)
        return results
