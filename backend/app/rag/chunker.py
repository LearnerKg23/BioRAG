import re
from typing import List, Optional
import tiktoken
from ..models.article import Article, ArticleSection
from ..models.chunk import DocumentChunk
from .cleaner import BiomedicalTextCleaner


class BaseChunker:
    """Base class for biomedical article chunkers."""

    def __init__(self, model_name: str = "cl100k_base"):
        try:
            self.tokenizer = tiktoken.get_encoding(model_name)
        except Exception:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text))


class BiomedicalSectionChunker(BaseChunker):
    """Section-aware chunker that preserves academic boundaries and attaches domain metadata.
    
    Prevents cross-section contamination (e.g. mixing Results into Methods).
    """

    def __init__(
        self,
        max_chunk_tokens: int = 512,
        min_chunk_tokens: int = 60,
        chunk_overlap: int = 50,
        add_context_header: bool = True,
    ):
        super().__init__()
        self.max_chunk_tokens = max_chunk_tokens
        self.min_chunk_tokens = min_chunk_tokens
        self.chunk_overlap = chunk_overlap
        self.add_context_header = add_context_header

    def chunk_article(self, article: Article) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        global_chunk_idx = 0

        # Collect all sections to process
        sections_to_process: List[ArticleSection] = []
        
        # If abstract exists and isn't already a section, add it
        has_abstract_sec = any(s.section_type == "abstract" for s in article.sections)
        if article.abstract and not has_abstract_sec:
            sections_to_process.append(
                ArticleSection(
                    title="Abstract",
                    section_type="abstract",
                    content=article.abstract,
                    order=-1
                )
            )
        sections_to_process.extend(article.sections)

        for sec in sections_to_process:
            clean_content = BiomedicalTextCleaner.clean(sec.content)
            if not clean_content.strip():
                continue

            sec_tokens = self.count_tokens(clean_content)

            # Case 1: Section is small enough to fit in a single chunk
            if sec_tokens <= self.max_chunk_tokens:
                header = f"[Paper: {article.metadata.title} | Section: {sec.title}]\n" if self.add_context_header else ""
                full_text = f"{header}{clean_content}"
                chunk_id = f"{article.id}_{sec.section_type}_chunk_{global_chunk_idx:02d}"

                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=article.id,
                        pmid=article.metadata.pmid,
                        pmcid=article.metadata.pmcid,
                        doi=article.metadata.doi,
                        paper_title=article.metadata.title,
                        journal=article.metadata.journal,
                        publication_year=article.metadata.publication_year,
                        section_name=sec.title,
                        section_type=sec.section_type,
                        chunk_index=global_chunk_idx,
                        token_count=self.count_tokens(full_text),
                        text=full_text,
                        raw_content=clean_content,
                    )
                )
                global_chunk_idx += 1
                continue

            # Case 2: Section exceeds max_chunk_tokens -> split into sub-chunks strictly within this section
            sub_chunks = self._split_section_text(clean_content)
            for sub_text in sub_chunks:
                header = f"[Paper: {article.metadata.title} | Section: {sec.title}]\n" if self.add_context_header else ""
                full_text = f"{header}{sub_text}"
                chunk_id = f"{article.id}_{sec.section_type}_chunk_{global_chunk_idx:02d}"

                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=article.id,
                        pmid=article.metadata.pmid,
                        pmcid=article.metadata.pmcid,
                        doi=article.metadata.doi,
                        paper_title=article.metadata.title,
                        journal=article.metadata.journal,
                        publication_year=article.metadata.publication_year,
                        section_name=sec.title,
                        section_type=sec.section_type,
                        chunk_index=global_chunk_idx,
                        token_count=self.count_tokens(full_text),
                        text=full_text,
                        raw_content=sub_text,
                    )
                )
                global_chunk_idx += 1

        return chunks

    def _split_section_text(self, text: str) -> List[str]:
        """Split a long section text along paragraphs and sentences with overlap."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: List[str] = []
        current_sentences: List[str] = []
        current_tokens = 0

        # Break into sentence units
        all_sentences: List[str] = []
        for p in paragraphs:
            # Split sentences respecting punctuation
            sents = re.split(r"(?<=[.!?])\s+", p)
            all_sentences.extend([s.strip() for s in sents if s.strip()])

        for sent in all_sentences:
            sent_tok = self.count_tokens(sent)
            if current_tokens + sent_tok > self.max_chunk_tokens and current_sentences:
                # Flush current chunk
                chunk_str = " ".join(current_sentences)
                chunks.append(chunk_str)

                # Keep overlap sentences
                overlap_sents = []
                overlap_toks = 0
                for s in reversed(current_sentences):
                    st = self.count_tokens(s)
                    if overlap_toks + st <= self.chunk_overlap:
                        overlap_sents.insert(0, s)
                        overlap_toks += st
                    else:
                        break

                current_sentences = list(overlap_sents)
                current_tokens = overlap_toks

            current_sentences.append(sent)
            current_tokens += sent_tok

        if current_sentences:
            chunks.append(" ".join(current_sentences))

        return chunks


class FixedSizeChunker(BaseChunker):
    """Standard sliding window chunker used as an ablation baseline in benchmark comparisons."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 100):
        super().__init__()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_article(self, article: Article) -> List[DocumentChunk]:
        full_text = BiomedicalTextCleaner.clean(article.full_text)
        tokens = self.tokenizer.encode(full_text)
        chunks: List[DocumentChunk] = []

        start = 0
        idx = 0
        while start < len(tokens):
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            header = f"[Paper: {article.metadata.title} | Baseline Fixed Chunk]\n"
            full_chunk_text = f"{header}{chunk_text}"
            chunk_id = f"{article.id}_fixed_chunk_{idx:02d}"

            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=article.id,
                    pmid=article.metadata.pmid,
                    pmcid=article.metadata.pmcid,
                    doi=article.metadata.doi,
                    paper_title=article.metadata.title,
                    journal=article.metadata.journal,
                    publication_year=article.metadata.publication_year,
                    section_name="FixedWindow",
                    section_type="other",
                    chunk_index=idx,
                    token_count=len(chunk_tokens),
                    text=full_chunk_text,
                    raw_content=chunk_text,
                )
            )
            idx += 1
            if end == len(tokens):
                break
            start += (self.chunk_size - self.chunk_overlap)

        return chunks
