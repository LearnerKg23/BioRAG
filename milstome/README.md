# BioRAG: Project Milestones Roadmap

**BioRAG — An Evidence-Based Biomedical Research Assistant Using Retrieval-Augmented Generation (RAG)**  
*Tech Stack: React.js, FastAPI, Python, LangChain, FAISS, BM25, Groq API (LLaMA 3), HuggingFace Embeddings, RAGAS*

---

## Roadmap Executive Summary

```mermaid
gantt
    title BioRAG Development Timeline
    dateFormat  YYYY-MM-DD
    section Phase 1: Ingestion & Indexing
    M1: Data Ingestion & Europe PMC API      :m1, 2026-10-19, 4d
    M2: Section-Aware Chunking Pipeline      :m2, after m1, 4d
    M3: Dual Indexing & Hybrid Retrieval     :m3, after m2, 5d
    section Phase 2: Generation & Reasoning
    M4: LLM Generation, Grounding & Citations:m4, after m3, 5d
    section Phase 3: Benchmarking & Backend
    M5: Quantitative Evaluation & IR Metrics :m5, after m4, 5d
    M6: FastAPI Backend & Streaming API      :m6, after m5, 4d
    section Phase 4: Frontend & Finalization
    M7: React Frontend & Experiment Dashboard:m7, after m6, 6d
    M8: Hardening, Benchmarking Report & Docs:m8, after m7, 3d
```

---

## Milestone Breakdown

| Milestone | Title | Focus Area | Deliverables |
| :--- | :--- | :--- | :--- |
| [**Milestone 01**](./01_ingestion_and_dataset.md) | **Biomedical Literature Ingestion** | Europe PMC API, JATS XML Parsing, Document Caching | Automated search & fetch client, metadata extractor, structured article storage. |
| [**Milestone 02**](./02_preprocessing_and_chunking.md) | **Section-Aware Chunking Pipeline** | Regex Header Detection, Entity Preservation, Chunk Metadata | Custom section-aware chunker, entity-safe tokenization, chunking ablation testbed. |
| [**Milestone 03**](./03_hybrid_retrieval_and_indexing.md) | **Hybrid Retrieval Engine** | FAISS, BM25, MMR, Reciprocal Rank Fusion (RRF) | Dense PubMedBERT index, sparse BM25 index, MMR deduplication, ensemble retriever. |
| [**Milestone 04**](./04_llm_generation_and_grounding.md) | **LLM Generation & Evidence Grounding** | Groq LLaMA 3, Citation Anchors, Conflict Detection | LangChain LCEL chains, passage-level citations, cross-paper contradiction detection, abstention logic. |
| [**Milestone 05**](./05_evaluation_and_benchmarking.md) | **Quantitative Evaluation & IR Suite** | IR Metrics (`Recall@K`, `MRR`, `nDCG`), RAGAS | Benchmark runner, synthetic testset generation, multi-configuration ablation comparison. |
| [**Milestone 06**](./06_fastapi_backend.md) | **FastAPI Backend & Streaming Service** | Async API, SSE Streaming, Job Queue | REST endpoints for search, chat streaming, and benchmark executions. |
| [**Milestone 07**](./07_react_frontend_and_dashboard.md) | **React UI & Experiment Dashboard** | Interactive Assistant, Evidence Viewer, Metric Charts | Dual-pane assistant with citation jump-to-source, visual benchmark dashboard (Recharts). |
| [**Milestone 08**](./08_deployment_and_documentation.md) | **System Hardening & Final Documentation** | Dockerization, Benchmark Report, Comprehensive Guide | End-to-end integration tests, Docker Compose, research-grade evaluation paper/README. |

---

## Architectural Principles
1. **Traceability Above All:** Every generated statement must tie back to an exact `[PMID, Section, ChunkID]`. No orphan claims.
2. **Hybrid Retrieval Superiority:** Scientific queries rely heavily on exact gene/mutation identifiers (`TP53`, `EGFR T790M`). BM25 ensures precision; FAISS semantic vectors ensure recall.
3. **Graceful Abstention:** When the retrieved literature does not answer the question or confidence is low, the model must explicitly state insufficient evidence rather than hallucinating.
4. **Reproducible Experimentation:** All retrieval parameters (chunk size, dense/sparse weights, rerankers) are benchmarked with standard IR metrics (`Recall@K`, `MRR`, `nDCG`) and RAGAS.
