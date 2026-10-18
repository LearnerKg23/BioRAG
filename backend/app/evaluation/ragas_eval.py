import re
from typing import List, Dict, Any, Optional


class RagasEvaluator:
    """Evaluates RAG generation quality: Faithfulness, Answer Relevance, and Context Precision."""

    @staticmethod
    def calculate_faithfulness(answer: str, context_passages: List[str]) -> float:
        """Measure what percentage of substantive statements in the answer are grounded in context."""
        if not answer or not context_passages:
            return 0.0

        # Extract sentences from answer
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer) if len(s.strip()) > 15]
        if not sentences:
            return 1.0

        combined_context = " ".join(context_passages).lower()
        supported_count = 0

        for sent in sentences:
            # Extract key informative words (> 3 chars)
            words = [w.lower() for w in re.findall(r"\b[A-Za-z0-9_\-]+\b", sent) if len(w) > 3]
            if not words:
                continue

            # Check word overlap in context
            matched = sum(1 for w in words if w in combined_context)
            ratio = matched / len(words)
            if ratio >= 0.5:  # At least 50% keyword grounding
                supported_count += 1

        return round(supported_count / len(sentences), 4)

    @staticmethod
    def calculate_answer_relevance(query: str, answer: str) -> float:
        """Measure semantic relevance of the synthesized answer to the input query."""
        query_terms = set(re.findall(r"\b[A-Za-z0-9_\-]+\b", query.lower()))
        answer_terms = set(re.findall(r"\b[A-Za-z0-9_\-]+\b", answer.lower()))

        if not query_terms:
            return 1.0

        overlap = query_terms.intersection(answer_terms)
        return round(len(overlap) / len(query_terms), 4)

    @staticmethod
    def calculate_context_precision(ground_truth_keywords: List[str], context_passages: List[str]) -> float:
        """Measure proportion of retrieved passages containing relevant ground truth keywords."""
        if not ground_truth_keywords or not context_passages:
            return 0.0

        relevant_passages = 0
        for p in context_passages:
            p_lower = p.lower()
            if any(k.lower() in p_lower for k in ground_truth_keywords):
                relevant_passages += 1

        return round(relevant_passages / len(context_passages), 4)
