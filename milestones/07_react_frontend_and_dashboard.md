# Milestone 07: Interactive React.js Research UI & Experiment Dashboard

## Objective
Build a modern, intuitive, and responsive frontend using **React.js**, **Tailwind CSS**, and **Lucide Icons**. The frontend must deliver two core user experiences:
1. **The Biomedical Research Assistant**: A split-screen workspace where researchers ask complex scientific questions, view streaming answers, inspect source-grounded citation highlights, and review detected cross-paper contradictions.
2. **The Experiment & Benchmarking Dashboard**: An interactive visual analytics suite displaying IR metrics (`Recall@K`, `MRR`, `nDCG`), RAGAS faithfulness scores, and ablation charts.

---

## Key Tasks & Technical Specifications

### 1. Technology & Foundation Setup
- Initialize modern React app using **Vite + Tailwind CSS**:
  - State management & network caching via `@tanstack/react-query`.
  - Iconography via `lucide-react`.
  - Markdown and scientific text rendering via `react-markdown` and `rehype-katex` (for formulas/chemical notation).
  - Data charts via `recharts`.

### 2. Research Assistant Workspace (Split-Screen Layout)
- **Left Panel: Conversational Query & Synthesis Stream**
  - Search input with pre-populated biomedical sample prompts (e.g., *"Mechanisms of resistance to EGFR inhibitors in lung cancer"*, *"Role of STING pathway in immunotherapy"*).
  - Real-time streaming response rendered with Markdown styling.
  - **Clickable In-Text Citation Badges**: `[PMID: 38451234, Results]`.
  - **Special Visual Callouts**:
    - *Contradiction Alert Box*: Highlighted amber card when divergent findings are detected between studies.
    - *Abstention Banner*: Informational notice when retrieved literature lacks sufficient evidence.
    - *Confidence Score Meter*: Visual indicator of answer certainty based on passage relevance.
- **Right Panel: Evidence & Source Inspector**
  - Displays retrieved passages ranked by relevance.
  - Clicking any citation badge in the answer automatically focuses, scrolls to, and highlights the corresponding chunk in the Evidence Inspector.
  - Displays full document metadata: Title, Journal, Year, DOI link, PMCID, and Section Badge (e.g., `RESULTS`, `METHODS`).

### 3. Literature Management Panel (Europe PMC Search & Ingest)
- Modal or dedicated view to search Europe PMC live directly from the UI.
- Displays article title, abstract snippet, authors, open-access badge, and an *"Ingest into BioRAG"* button.
- Real-time progress bar tracking ingestion, parsing, chunking, and FAISS/BM25 indexing.

### 4. Experiment & Benchmarking Dashboard
- **Metric Visualizations (Powered by Recharts)**:
  - **Recall@K Comparison Curve**: Compares `bm25`, `faiss_cosine`, `faiss_mmr`, and `hybrid_rrf` across $K = [1, 3, 5, 10]$.
  - **MRR & nDCG Ranked Bar Charts**: Highlights retrieval ranking quality improvements from hybrid fusion and reranking.
  - **Faithfulness vs. Latency Scatter Plot**: Displays the trade-off between model accuracy and response time across different LLMs and chunk sizes.
- **Run History & Parameter Comparison Table**:
  - Filter and inspect past benchmark runs.
  - View per-question metric breakdowns to spot difficult biomedical queries.
- **Live Retrieval Strategy Playground**:
  - Allows the user to enter a query and view retrieved chunks side-by-side using BM25 vs FAISS vs Hybrid.

---

## Deliverables
- `frontend/src/components/Assistant/`: Chatbox, MessageItem, CitationBadge, EvidenceInspector.
- `frontend/src/components/Dashboard/`: MetricSummaryCards, RecallChart, MRRBarChart, RunTable.
- `frontend/src/components/Papers/`: PMCArticleSearch, IngestionModal.
- `frontend/src/hooks/useChatStream.js`: Custom hook managing EventSource / SSE connection.
- Responsive, polished UI with clean typography and scientific aesthetics.

---

## Acceptance Criteria
- [ ] User can submit a question and receive streaming answers with interactive citation badges.
- [ ] Clicking a citation badge immediately highlights and reveals the corresponding evidence passage in the side panel.
- [ ] Contradictions and abstention states are clearly rendered with appropriate visual distinction.
- [ ] Benchmarking dashboard visualizes Recall@K, MRR, nDCG, and RAGAS scores with interactive charts.
- [ ] Europe PMC paper search and live ingestion trigger operate seamlessly from the frontend.
