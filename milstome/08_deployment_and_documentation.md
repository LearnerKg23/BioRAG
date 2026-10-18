# Milestone 08: System Hardening, Documentation & Deployment

## Objective
Finalize the BioRAG project with comprehensive automated testing, containerization via Docker, detailed scientific documentation, and an empirical evaluation report analyzing retrieval trade-offs, performance gains, and system limitations.

---

## Key Tasks & Technical Specifications

### 1. Automated Testing Suite & Code Quality
- Build a thorough test suite using `pytest`:
  - **Unit Tests**:
    - Section-aware regex chunker boundary integrity.
    - Biomedical entity preservation (ensuring symbols like *TP53* and *V600E* are unmutated).
    - BM25 and FAISS index persistence, serialization, and retrieval logic.
    - MMR diversity score calculations.
    - RRF rank fusion formula verification.
  - **Integration Tests**:
    - End-to-end RAG query flow with mocked Groq responses.
    - Europe PMC API parsing and error handling for malformed XML.
    - SSE streaming endpoint test.
    - Benchmark runner execution on sample QA pairs.
- Code style: Linting and formatting with `ruff` to maintain clean, production-grade Python code.

### 2. Containerization & Orchestration
- **Backend Dockerfile**:
  - Python 3.11 slim base image, non-root user, optimized multi-stage build.
  - Pre-downloaded HuggingFace embedding weights or mounted volume for fast cold starts.
- **Frontend Dockerfile**:
  - Multi-stage build: Node.js build stage $\rightarrow$ Nginx Alpine runtime serving static assets with reverse proxy to FastAPI.
- **Docker Compose (`docker-compose.yml`)**:
  - One-command orchestration bringing up `backend` on port `8000` and `frontend` on port `3000`, with mounted volumes for `data/` persistence.

### 3. Empirical Evaluation Report (`BENCHMARK_REPORT.md`)
- Draft an academic-grade evaluation report documenting:
  - **Methodology**: Explanation of dataset, queries, ground-truth annotation, and metric definitions (`Recall@K`, `MRR`, `nDCG`, `Faithfulness`).
  - **Quantitative Results Table**: Side-by-side comparison of:
    - BM25 vs. FAISS (Cosine) vs. FAISS (MMR) vs. Hybrid (BM25 + FAISS) vs. Hybrid + Reranker.
    - Fixed 256 vs Fixed 512 vs Section-Aware Chunking.
    - MiniLM vs. PubMedBERT embeddings.
  - **Discussion & Key Findings**:
    - Why hybrid retrieval outperforms dense-only search on scientific acronyms and gene symbols.
    - Why section-aware chunking reduces hallucination rates compared to arbitrary token window splits.
    - Latency vs. accuracy trade-offs of cross-encoder reranking.
  - **Error Analysis & Limitations**:
    - Analysis of failed queries (e.g., negative results buried in supplementary materials, complex tables).
    - Explicit disclaimer that BioRAG is an academic research-support tool, not a clinical diagnostic system.

### 4. Master Documentation & Setup Guide (`README.md`)
- System architecture diagram (Mermaid flow).
- Quickstart guide:
  - Prerequisites (Python, Node.js, Groq API Key).
  - One-line setup with Docker Compose.
  - Manual local development instructions (backend + frontend).
- API Reference and sample curl commands.
- Live demo screenshots and video walkthrough.

---

## Deliverables
- `tests/`: Complete unit and integration test suite with high coverage.
- `Dockerfile` & `docker-compose.yml`: Tested container configs.
- `docs/BENCHMARK_REPORT.md`: Comprehensive evaluation analysis.
- `README.md`: Polished, professional documentation.

---

## Acceptance Criteria
- [ ] All unit and integration tests pass with `pytest`.
- [ ] Application successfully builds and runs via `docker-compose up`.
- [ ] Empirical evaluation report is complete with reproducible numbers and analysis.
- [ ] README provides clear, unambiguous instructions for any engineer or researcher to run BioRAG locally.
