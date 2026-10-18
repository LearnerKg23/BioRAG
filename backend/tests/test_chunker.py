import pytest
from backend.app.rag.cleaner import BiomedicalTextCleaner
from backend.app.rag.chunker import BiomedicalSectionChunker, FixedSizeChunker
from backend.app.models.article import Article, ArticleMetadata, ArticleSection


def test_text_cleaner_entity_preservation():
    dirty_text = "Mutations in BRAF (e.g. V600E [1, 2]) and EGFR (T790M [3-5]) confer resistance. Dosage: 50 µg/mL ± 5 at 37°C."
    cleaned = BiomedicalTextCleaner.clean(dirty_text)

    # Citation markers stripped
    assert "[1, 2]" not in cleaned
    assert "[3-5]" not in cleaned

    # Scientific entities and symbols preserved
    assert "BRAF" in cleaned
    assert "V600E" in cleaned
    assert "EGFR" in cleaned
    assert "T790M" in cleaned
    assert "50 μg/mL" in cleaned
    assert "± 5" in cleaned


def test_section_aware_chunking_boundaries():
    meta = ArticleMetadata(
        pmid="12345678",
        pmcid="PMC9999999",
        doi="10.1038/test",
        title="Genomic Landscape of BRAF-Mutant Cancers",
    )
    sections = [
        ArticleSection(
            title="Introduction",
            section_type="introduction",
            content="BRAF V600 mutations occur in roughly 50% of melanomas and drive hyperactive MAPK signaling.",
            order=0
        ),
        ArticleSection(
            title="Materials and Methods",
            section_type="methods",
            content="Genomic DNA was sequenced using Illumina NovaSeq 6000 with a targeted 500-gene pan-cancer panel.",
            order=1
        ),
        ArticleSection(
            title="Results",
            section_type="results",
            content="We identified co-occurring PTEN loss in 32% of patients with rapid disease progression.",
            order=2
        ),
        ArticleSection(
            title="Discussion",
            section_type="discussion",
            content="Our observations support dual inhibition strategies targeting both MAPK and PI3K pathways.",
            order=3
        )
    ]
    article = Article(id="PMC9999999", metadata=meta, abstract="", sections=sections)

    chunker = BiomedicalSectionChunker(max_chunk_tokens=512)
    chunks = chunker.chunk_article(article)

    assert len(chunks) == 4
    section_types = [c.section_type for c in chunks]
    assert section_types == ["introduction", "methods", "results", "discussion"]

    # Verify no cross-boundary leakage
    results_chunk = next(c for c in chunks if c.section_type == "results")
    assert "PTEN loss" in results_chunk.text
    assert "NovaSeq" not in results_chunk.text
    assert "hyperactive MAPK" not in results_chunk.text

    # Verify metadata preservation
    assert results_chunk.document_id == "PMC9999999"
    assert results_chunk.paper_title == meta.title
    assert results_chunk.section_name == "Results"
    assert results_chunk.chunk_id.startswith("PMC9999999_results_chunk_")


def test_fixed_size_chunker():
    meta = ArticleMetadata(title="Sample Paper")
    sections = [
        ArticleSection(title="Body", section_type="other", content="Sentence one. " * 100, order=0)
    ]
    article = Article(id="DOC01", metadata=meta, abstract="", sections=sections)

    chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20)
    chunks = chunker.chunk_article(article)

    assert len(chunks) > 1
    assert all(c.section_name == "FixedWindow" for c in chunks)
    assert all(c.document_id == "DOC01" for c in chunks)
