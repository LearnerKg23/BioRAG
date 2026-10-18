# Milestone 02: Preprocessing & Custom Section-Aware Chunking Pipeline

## Objective
Design and implement a domain-aware chunking and text preprocessing pipeline. Analogous to clause-aware chunking in legal documents, biomedical papers must be chunked respecting academic section boundaries (`Abstract`, `Introduction`, `Methods`, `Results`, `Discussion`, `Conclusion`) rather than arbitrary character splits. This preserves scientific context, prevents cross-section pollution (e.g., blending speculative discussion with empirical results), and attaches rich citation metadata to every chunk.

---

## Key Tasks & Technical Specifications

### 1. Biomedical Text Cleaning & Entity Preservation
- Text normalization tailored for biomedical literature:
  - Normalize Greek characters and scientific symbols ($\alpha$, $\beta$, $\mu\text{g}$, $\pm$).
  - Clean ligature artifacts (`ﬁ` $\rightarrow$ `fi`, `ﬂ` $\rightarrow$ `fl`) and trailing citation markers (`[1, 2]`, `(Smith et al., 2020)`).
  - **Preserve Critical Biomedical Entities**: Ensure gene names (e.g., *TP53*, *BRCA1*), mutation notations (e.g., *p.V600E*, *c.1799T>A*), cell lines (*HEK293*, *Jurkat*), dosages, and chemical formulas are untouched by lowercase transformations or aggressive tokenizers.

### 2. Custom Section-Aware Regex Chunker (`BiomedicalSectionChunker`)
- Develop a regex-driven section segmentation pipeline:
  ```python
  SECTION_PATTERNS = {
      "abstract": r"(?i)^(abstract|summary)",
      "introduction": r"(?i)^(introduction|background)",
      "methods": r"(?i)^(methods|materials and methods|methodology|experimental procedures)",
      "results": r"(?i)^(results|findings)",
      "discussion": r"(?i)^(discussion)",
      "conclusion": r"(?i)^(conclusion|concluding remarks)",
  }
  ```
- **Chunking Logic within Sections**:
  - If a section is short ($\le 500$ tokens), keep it as an atomic chunk.
  - If a section exceeds the maximum token budget (e.g., $512$ tokens), split along paragraph and sentence boundaries using `scispaCy` or `nltk.sent_tokenize`.
  - Maintain a configurable overlap (e.g., $10$–$15\%$) strictly *within* the same section—never across different sections.
  - Embed contextual header prefixes into the chunk text:
    ```text
    [Paper: {Title} | Section: {Section_Name}]
    {Actual Chunk Text}
    ```

### 3. Chunk Metadata Schema
- Every chunk must be an instance of a standardized `DocumentChunk` object:
  ```json
  {
    "chunk_id": "PMC10928374_sec_results_chunk_02",
    "document_id": "PMC10928374",
    "pmid": "38451234",
    "pmcid": "PMC10928374",
    "doi": "10.1038/s41586-024-07123-x",
    "paper_title": "Mechanisms of BRAF Inhibitor Resistance in Melanoma",
    "journal": "Nature",
    "publication_year": 2024,
    "section_name": "Results",
    "section_type": "results",
    "chunk_index": 2,
    "token_count": 384,
    "text": "..."
  }
  ```

### 4. Ablation Chunking Strategies (For Benchmarking in M5)
- Support multiple chunking strategies to enable quantitative IR comparison:
  1. **Fixed-Size Sliding Window**: 256 tokens (50 token overlap).
  2. **Fixed-Size Sliding Window**: 512 tokens (100 token overlap).
  3. **Section-Aware Semantic Chunking**: Variable-length, bounded by scientific sections (Baseline).

---

## Deliverables
- `backend/app/rag/cleaner.py`: Biomedical text cleaner and symbol normalizer.
- `backend/app/rag/chunker.py`: Custom `BiomedicalSectionChunker` and fixed-size chunkers.
- `backend/app/models/chunk.py`: Pydantic schema for `DocumentChunk` and metadata.
- Unit tests: `tests/test_chunker.py` verifying that sections do not bleed across boundaries and entity names are preserved.

---

## Acceptance Criteria
- [ ] Section boundaries (`Abstract`, `Methods`, `Results`, `Discussion`) are never merged into a single chunk.
- [ ] Gene symbols (e.g., *EGFR*, *KRAS*) and mutation patterns (e.g., *T790M*) remain intact without text distortion.
- [ ] Every chunk contains complete document and section metadata.
- [ ] Configurable chunk size and overlap parameters function correctly for comparative experimentation.
