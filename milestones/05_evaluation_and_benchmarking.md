# Milestone 05: Quantitative Evaluation & IR Benchmarking Suite

## Objective
Establish a reproducible, scientific evaluation and benchmarking framework. BioRAG is not merely a conversational UI; its primary technical objective is to quantitatively measure and compare how different retrieval strategies, chunk sizes, embedding models, and ranking methods impact information retrieval (IR) quality, generation faithfulness, and citation accuracy.

---

## Key Tasks & Technical Specifications

### 1. Benchmark Dataset Construction
- **Curated Biomedical QA Benchmark**:
  - Build a curated evaluation set ($N = 50$ to $100$ questions) across key biomedical domains:
    - Target discovery & gene function (e.g., *“What is the role of STING activation in checkpoint inhibitor resistance?”*).
    - Drug-disease interactions and mechanisms of action.
    - Contradictory clinical trials or experimental outcomes.
    - Unanswerable control questions to test the abstention trigger.
  - For each test item, define:
    ```json
    {
      "question_id": "bio_eval_014",
      "question": "Does KRAS G12C mutation confer sensitivity to sotorasib in NSCLC?",
      "ground_truth_pmids": ["32958437", "34091698"],
      "relevant_chunk_ids": ["PMC7584912_sec_results_chunk_01"],
      "ground_truth_answer": "...",
      "is_answerable": true
    }
    ```
- **Automated Synthetic Testset Generation**:
  - Utilize `ragas.testset.synthesizer` to automatically generate additional multi-hop and reasoning queries directly from ingested paper corpora.

### 2. Information Retrieval (IR) Metrics Suite
- Implement classic Information Retrieval metrics using `ranx` or custom NumPy IR modules:
  - **Recall@K** ($K \in [1, 3, 5, 10]$): Fraction of relevant ground-truth chunks retrieved in top $K$.
  - **Mean Reciprocal Rank (MRR@K)**: Measures rank position of the first relevant retrieved document:
    $$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
  - **Normalized Discounted Cumulative Gain (nDCG@K)**: Evaluates ranked order quality with graded relevance penalties:
    $$\text{DCG@K} = \sum_{i=1}^{K} \frac{2^{\text{rel}_i} - 1}{\log_2(i + 1)}$$
  - **Precision@K**: Proportion of top $K$ retrieved chunks that are truly relevant.

### 3. Generation Quality & Faithfulness Metrics (RAGAS)
- Integrate **RAGAS** (`ragas.metrics`):
  - **Faithfulness**: Proportion of claims in the generated answer that can be inferred directly from the retrieved context (measuring hallucination).
  - **Answer Relevance**: Semantic similarity and relevance of the answer to the initial question.
  - **Context Precision**: Signal-to-noise ratio of the retrieved passages.
  - **Context Recall**: Whether all ground-truth facts are present in retrieved contexts.
  - **Abstention Accuracy**: Accuracy in refusing to answer when given unanswerable test queries.

### 4. Systematic Ablation Experiment Runner
- Create an automated experiment orchestrator (`BenchmarkRunner`) that executes across configurable permutations:
  
  | Experiment Dimension | Configurations Tested |
  | :--- | :--- |
  | **Retrieval Mode** | `bm25_only`, `faiss_cosine`, `faiss_mmr`, `hybrid_rrf`, `hybrid_rrf_reranker` |
  | **Embedding Model** | `all-MiniLM-L6-v2` vs `PubMedBERT-base-embeddings` |
  | **Chunking Strategy** | `fixed_256`, `fixed_512`, `section_aware` |
  | **Top-K Retrieval** | $K = 3, 5, 10$ |

- Compute latency (retrieval time, generation time, total TTFT) for every configuration.
- Output timestamped JSON manifests and CSV reports in `data/benchmarks/results/run_{timestamp}.json`.

---

## Deliverables
- `backend/app/evaluation/benchmark_dataset.json`: Gold-standard biomedical QA dataset with ground-truth chunk labels.
- `backend/app/evaluation/ir_metrics.py`: Pure Python/NumPy calculations for Recall@K, MRR@K, nDCG@K.
- `backend/app/evaluation/ragas_evaluator.py`: RAGAS pipeline integration with Groq.
- `backend/app/evaluation/experiment_runner.py`: CLI and automated runner executing multi-configuration ablation matrices.
- Pre-computed baseline benchmark report comparing BM25 vs FAISS vs Hybrid.

---

## Acceptance Criteria
- [ ] Evaluation suite runs end-to-end on test queries without human intervention.
- [ ] Quantitative metrics (`Recall@K`, `MRR`, `nDCG`, `Faithfulness`) are accurately computed and logged.
- [ ] Hybrid (BM25 + FAISS MMR) demonstrates quantifiable improvement in Recall and MRR over single-retriever baselines.
- [ ] Abstention accuracy is systematically evaluated on unanswerable control queries.
- [ ] Benchmark results are serialized in structured JSON consumable by the frontend dashboard.
