# Milestone 03: Dual-Indexing & Hybrid Retrieval Engine (FAISS + BM25 + MMR)

## Objective
Build a high-performance hybrid information retrieval (IR) engine. In biomedical literature, dense semantic search often misses exact alphanumeric gene mutations (e.g., *BRAF V600E* vs *BRAF V600K*) or drug acronyms, while pure keyword search fails on conceptual and semantic queries. BioRAG resolves this by fusing **FAISS dense vector search** (with **Maximal Marginal Relevance - MMR** to eliminate redundant snippets) and **BM25 sparse keyword retrieval** using **Reciprocal Rank Fusion (RRF)** and an optional **Cross-Encoder reranker**.

---

## Key Tasks & Technical Specifications

### 1. Dense Vector Indexing with FAISS & HuggingFace Embeddings
- Integrate `langchain_community.vectorstores.FAISS` and `langchain_huggingface.HuggingFaceEmbeddings`.
- Support multiple embedding backends:
  - `sentence-transformers/all-MiniLM-L6-v2` (Fast, general baseline).
  - `NeuML/pubmedbert-base-embeddings` or `pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb` (Domain-specific biomedical embeddings).
- Configure FAISS vector index (`IndexFlatIP` with normalized vectors for exact cosine similarity, or `IndexHNSWFlat` for scalable ANN).
- Persist vector index and chunk metadata mapping to disk (`data/indices/faiss/`).

### 2. Maximal Marginal Relevance (MMR) Retrieval
- Implement MMR search via FAISS retriever:
  $$\text{MMR} = \arg\max_{d_i \in R \setminus S} \left[ \lambda \cdot \text{Sim}_1(d_i, q) - (1 - \lambda) \cdot \max_{d_j \in S} \text{Sim}_2(d_i, d_j) \right]$$
- Configurable parameters:
  - `k`: Number of final returned documents (e.g., 5).
  - `fetch_k`: Initial candidate pool size (e.g., 20).
  - `lambda_mult` ($\lambda$): Diversity trade-off parameter (e.g., 0.7 balances relevance and diversity).
- Prevents retrieval of 5 nearly identical chunks from the same paper's introduction.

### 3. Sparse Keyword Indexing with BM25
- Integrate `langchain_community.retrievers.BM25Retriever`.
- Tokenize scientific queries preserving medical punctuation (hyphenated terms, alphanumeric mutation codes).
- Build and serialize the BM25 inverted index (`data/indices/bm25/`).

### 4. Hybrid Search via Reciprocal Rank Fusion (RRF)
- Integrate LangChain's `EnsembleRetriever` to fuse dense (FAISS MMR) and sparse (BM25) rankings:
  $$\text{RRF\_Score}(d) = \sum_{m \in \{\text{dense}, \text{sparse}\}} \frac{w_m}{k_{rrf} + \text{rank}_m(d)}$$
  where $k_{rrf} = 60$ (standard constant) and $w_m$ are tunable weights (default: $0.6$ dense, $0.4$ sparse).
- Support parameter toggles in the retriever to evaluate:
  - BM25-only
  - FAISS Cosine-only
  - FAISS MMR-only
  - Hybrid (BM25 + FAISS MMR)

### 5. Optional Cross-Encoder Reranking
- Add a two-stage retrieval pipeline using `sentence-transformers.CrossEncoder`:
  - Model: `cross-encoder/ms-marco-MiniLM-L-6-v2` or `BAAI/bge-reranker-large`.
  - Take the top 15 candidates from the hybrid ensemble and rescore query-chunk pairs with cross-attention to produce the final top $K=5$ context passages.

---

## Deliverables
- `backend/app/rag/embeddings.py`: Factory for HuggingFace and PubMedBERT embeddings.
- `backend/app/rag/vectorstore.py`: FAISS manager handling save, load, and similarity/MMR queries.
- `backend/app/rag/bm25.py`: BM25 index builder, serializer, and retriever.
- `backend/app/rag/hybrid_retriever.py`: `EnsembleRetriever` setup with RRF and optional Cross-Encoder.
- Unit & integration tests: `tests/test_retrieval.py` validating that known gene queries retrieve expected ground-truth chunks.

---

## Acceptance Criteria
- [ ] FAISS dense index generates and persists vector embeddings correctly.
- [ ] BM25 index accurately retrieves exact match queries containing biomedical codes (e.g., *V600E*).
- [ ] MMR retrieval produces demonstrably more diverse chunks than standard top-$K$ cosine search.
- [ ] Hybrid `EnsembleRetriever` successfully combines both scores and returns ranked `DocumentChunk` objects with source metadata.
- [ ] Fast retrieval latency (< 150ms for hybrid search across 10,000+ chunks).
