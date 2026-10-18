# Milestone 06: FastAPI Backend & Streaming Service

## Objective
Develop a production-grade, asynchronous **FastAPI** backend that exposes clean REST endpoints and real-time Server-Sent Events (SSE) streaming. The backend connects the ingestion pipeline, hybrid vector store, Groq generation chain, and benchmarking engine to the frontend user interface.

---

## Key Tasks & Technical Specifications

### 1. Application Architecture & Configuration
- Set up FastAPI app structure with modular routers:
  ```text
  backend/app/
  ├── api/
  │   ├── routes_chat.py         # RAG query & SSE streaming
  │   ├── routes_papers.py       # Europe PMC search & ingestion
  │   ├── routes_retrieval.py    # Raw passage search & inspection
  │   └── routes_benchmark.py    # Evaluation runs & metric results
  ├── core/
  │   ├── config.py              # Pydantic BaseSettings (GROQ_API_KEY, paths, index settings)
  │   └── logging.py             # Structured JSON logger
  └── main.py                    # FastAPI entrypoint & middleware (CORS, timing headers)
  ```
- Environment variable management using `.env` (`GROQ_API_KEY`, `EMBEDDING_MODEL_NAME`, `DATA_DIR`).

### 2. API Endpoints Specification

#### A. Document & Literature Ingestion (`/api/papers`)
- `GET /api/papers/search?query=...&limit=10`: Search Europe PMC live and return list of matching papers with open-access status.
- `POST /api/papers/ingest`: Ingest, parse JATS XML, chunk, and index selected papers asynchronously.
- `GET /api/papers/stats`: Return total indexed papers, chunk counts, section breakdown, and vector index status.

#### B. RAG Query & Streaming (`/api/chat`)
- `POST /api/chat/query`: Execute standard RAG query returning full structured answer, confidence score, and citation objects.
- `GET /api/chat/stream?query=...&retriever_mode=...`: Server-Sent Events (SSE) endpoint:
  - First event: Emits retrieved source passages and metadata (`event: sources`).
  - Next events: Stream LLaMA 3 generated tokens in real time (`event: token`).
  - Final event: Emits detected contradictions and confidence score (`event: done`).

#### C. Retrieval Inspection (`/api/retrieval`)
- `POST /api/retrieval/inspect`: Run raw hybrid retrieval for a query without calling the LLM. Returns ranked list of chunks, dense scores, BM25 scores, RRF scores, and section tags. Enables researchers to inspect why specific chunks were selected.

#### D. Benchmark & Experimentation (`/api/benchmark`)
- `GET /api/benchmark/runs`: List historical evaluation runs and summary statistics.
- `GET /api/benchmark/runs/{run_id}`: Retrieve detailed metrics (Recall@K, MRR, nDCG, RAGAS scores) and per-question breakdowns.
- `POST /api/benchmark/execute`: Trigger a new ablation benchmark run in the background.

### 3. Asynchronous Execution & Background Workers
- Use FastAPI `BackgroundTasks` to handle paper downloads, embedding calculation, and FAISS/BM25 index re-building without blocking the event loop.
- Implement file locks to ensure vector indices are safely read and updated concurrently.

---

## Deliverables
- `backend/app/main.py`: Configured FastAPI application with CORS and error handlers.
- `backend/app/api/`: Implemented router files for chat, papers, retrieval, and benchmarking.
- `backend/app/models/schemas.py`: Pydantic request/response schemas.
- `backend/requirements.txt`: Clean dependency list with pinned versions.
- Interactive Swagger docs at `/docs` with sample requests.

---

## Acceptance Criteria
- [ ] Endpoints adhere to OpenAPI standards and validate inputs via Pydantic v2.
- [ ] `/api/chat/stream` streams responses smoothly via SSE without dropped connections.
- [ ] Background indexing completes successfully without interrupting query handling.
- [ ] Error handling captures Groq API rate limits or network failures with appropriate HTTP status codes and user-friendly error messages.
