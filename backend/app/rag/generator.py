import os
import re
import logging
from typing import List, Optional, AsyncIterator, Tuple
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq

from ..models.chunk import DocumentChunk
from ..models.response import BioRAGResponse, CitationItem, ContradictionItem
from .prompts import BIOMEDICAL_SYSTEM_PROMPT, format_evidence_context

logger = logging.getLogger(__name__)

# Pattern to extract citation anchors: [PMID: 12345, Sec: Results]
CITATION_REGEX = re.compile(r"\[(?:PMID|PMCID|DOC):\s*([^,\]]+),\s*Sec:\s*([^\]]+)\]", re.IGNORECASE)
ABSTENTION_MARKER = "[ABSTAIN: INSUFFICIENT_EVIDENCE]"


class BioRAGGenerator:
    """Answers biomedical questions using LLaMA 3 via Groq API, enforcing strict evidence grounding."""

    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    FAST_MODEL = "llama-3.1-8b-instant"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.05,
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model_name = model_name or self.DEFAULT_MODEL
        self.temperature = temperature
        self._llm: Optional[ChatGroq] = None

        if self.api_key:
            try:
                self._llm = ChatGroq(
                    api_key=self.api_key,
                    model_name=self.model_name,
                    temperature=self.temperature,
                )
                logger.info(f"Initialized ChatGroq with model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Could not initialize ChatGroq: {e}. Generator will operate in mock mode.")
        else:
            logger.info("No GROQ_API_KEY found; operating in deterministic fallback mode.")

    def generate(self, query: str, chunks: List[DocumentChunk], retrieval_mode: Optional[str] = None) -> BioRAGResponse:
        """Generate structured answer with verified citations and contradiction analysis."""
        context_str = format_evidence_context(chunks)

        user_content = (
            f"Here is the retrieved scientific literature context:\n\n"
            f"{context_str}\n\n"
            f"Research Question: {query}\n\n"
            f"Please synthesize an evidence-grounded answer following all rules."
        )

        raw_answer = ""
        if self._llm is not None:
            messages = [
                SystemMessage(content=BIOMEDICAL_SYSTEM_PROMPT),
                HumanMessage(content=user_content),
            ]
            response = self._llm.invoke(messages)
            raw_answer = str(response.content)
        else:
            raw_answer = self._generate_mock_answer(query, chunks)

        return self._build_response(query, raw_answer, chunks, retrieval_mode=retrieval_mode)

    async def astream_generate(
        self, query: str, chunks: List[DocumentChunk]
    ) -> AsyncIterator[str]:
        """Asynchronously stream generation tokens for real-time frontend display."""
        context_str = format_evidence_context(chunks)
        user_content = (
            f"Here is the retrieved scientific literature context:\n\n"
            f"{context_str}\n\n"
            f"Research Question: {query}\n\n"
            f"Please synthesize an evidence-grounded answer following all rules."
        )

        if self._llm is not None:
            messages = [
                SystemMessage(content=BIOMEDICAL_SYSTEM_PROMPT),
                HumanMessage(content=user_content),
            ]
            async for chunk in self._llm.astream(messages):
                yield chunk.content
        else:
            mock = self._generate_mock_answer(query, chunks)
            for word in mock.split(" "):
                yield word + " "

    def _build_response(
        self,
        query: str,
        raw_text: str,
        chunks: List[DocumentChunk],
        retrieval_mode: Optional[str] = None
    ) -> BioRAGResponse:
        """Parse raw generated text into structured BioRAGResponse."""
        has_sufficient = not raw_text.startswith(ABSTENTION_MARKER)
        abstain_reason = None
        clean_answer = raw_text

        if not has_sufficient:
            abstain_reason = raw_text.replace(ABSTENTION_MARKER, "").strip()
            clean_answer = raw_text

        # 1. Extract Citation Items
        citations: List[CitationItem] = []
        chunk_map = {c.chunk_id: c for c in chunks}
        # Also build a lookup by pmid/pmcid
        pmid_map = {}
        for c in chunks:
            if c.pmid:
                pmid_map[c.pmid.strip()] = c
            if c.pmcid:
                pmid_map[c.pmcid.strip().upper()] = c

        matches = CITATION_REGEX.findall(clean_answer)
        seen_chunks = set()
        for pmid_match, sec_match in matches:
            pmid_clean = pmid_match.strip()
            sec_clean = sec_match.strip()
            matched_chunk = pmid_map.get(pmid_clean) or pmid_map.get(pmid_clean.upper())

            if matched_chunk and matched_chunk.chunk_id not in seen_chunks:
                seen_chunks.add(matched_chunk.chunk_id)
                citations.append(
                    CitationItem(
                        pmid=matched_chunk.pmid,
                        pmcid=matched_chunk.pmcid,
                        title=matched_chunk.paper_title,
                        section=sec_clean or matched_chunk.section_name,
                        chunk_id=matched_chunk.chunk_id,
                        doi=matched_chunk.doi,
                        supporting_text=matched_chunk.raw_content[:200] + "...",
                    )
                )

        # If LLM didn't attach parsed anchors but returned chunks, attach top retrieved chunks as citations
        if not citations and chunks and has_sufficient:
            for c in chunks[:3]:
                citations.append(
                    CitationItem(
                        pmid=c.pmid,
                        pmcid=c.pmcid,
                        title=c.paper_title,
                        section=c.section_name,
                        chunk_id=c.chunk_id,
                        doi=c.doi,
                        supporting_text=c.raw_content[:200] + "...",
                    )
                )

        # 2. Extract Contradictions
        conflicts: List[ContradictionItem] = []
        if "### Conflicting or Divergent Findings" in clean_answer:
            parts = clean_answer.split("### Conflicting or Divergent Findings")
            conflict_text = parts[1].strip() if len(parts) > 1 else ""
            if conflict_text:
                conflicts.append(
                    ContradictionItem(
                        topic=query,
                        study_a_claim="See detailed cross-study comparison in section.",
                        study_b_claim="Reported differences detailed in section.",
                        potential_reason=conflict_text[:300],
                    )
                )

        # 3. Calculate Confidence Score
        confidence = 0.0
        if has_sufficient:
            base_score = 0.5
            citation_boost = min(0.4, len(citations) * 0.1)
            chunk_relevance_boost = min(0.1, len(chunks) * 0.02)
            confidence = round(base_score + citation_boost + chunk_relevance_boost, 2)
        else:
            confidence = 0.1

        return BioRAGResponse(
            query=query,
            answer=clean_answer,
            citations=citations,
            conflicts_detected=conflicts,
            confidence_score=confidence,
            has_sufficient_evidence=has_sufficient,
            abstention_reason=abstain_reason,
            retrieval_mode=retrieval_mode,
            total_chunks_retrieved=len(chunks),
        )

    def _generate_mock_answer(self, query: str, chunks: List[DocumentChunk]) -> str:
        """Deterministic fallback answer generator for automated testing without API keys."""
        if not chunks:
            return f"{ABSTENTION_MARKER} The literature corpus contains no relevant evidence regarding '{query}'."

        first = chunks[0]
        pmid_tag = f"[PMID: {first.pmid or first.pmcid or first.document_id}, Sec: {first.section_name}]"
        
        answer_parts = [
            f"Based on the retrieved scientific literature, {first.raw_content[:150]}... {pmid_tag}."
        ]

        if len(chunks) > 1:
            second = chunks[1]
            sec_pmid_tag = f"[PMID: {second.pmid or second.pmcid or second.document_id}, Sec: {second.section_name}]"
            answer_parts.append(
                f"Additionally, subsequent analysis confirmed {second.raw_content[:120]}... {sec_pmid_tag}."
            )

        return " ".join(answer_parts)
