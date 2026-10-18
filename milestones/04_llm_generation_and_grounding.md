# Milestone 04: LLM Generation, Evidence Grounding & Abstention System

## Objective
Implement the context-grounded answer generation engine using **Groq API (LLaMA 3)** and **LangChain LCEL**. Unlike a generic chatbot, BioRAG must produce evidence-supported answers where every claim is directly tied to a passage citation, identify conflicting conclusions across multiple papers, distinguish reported findings from model interpretations, and reliably abstain when retrieved literature is insufficient.

---

## Key Tasks & Technical Specifications

### 1. Groq API Integration (LLaMA 3)
- Integrate `langchain_groq.ChatGroq`:
  - Primary model: `llama-3.3-70b-versatile` (high reasoning, nuanced scientific synthesis).
  - Fast baseline model: `llama-3.1-8b-instant` (ultra-low latency for quick queries).
- Configuration:
  - Low temperature ($0.0$ to $0.1$) to prioritize factual accuracy over creative variation.
  - Streaming support via async iterators (`astream`).

### 2. Evidence Grounding & Prompt Architecture
- Construct prompt templates enforcing strict biomedical research standards:
  - **Context Grounding Rule**: Answer ONLY based on the provided `<evidence_passages>`. Do not use outside medical knowledge.
  - **In-Text Citation Format**: Attach citation badges `[PMID: {pmid}, Sec: {section_name}]` directly behind each claim.
  - **Section Hierarchy Awareness**: Prefer evidence from *Results* and *Methods* over speculative hypotheses in *Discussion*.
  - **Separation of Evidence vs. Synthesis**: Distinguish direct experimental findings from general authorial conclusions.

### 3. Multi-Paper Synthesis & Contradiction Detection
- When retrieved passages from Paper A and Paper B present diverging or conflicting conclusions (e.g., Paper A finds a biomarker statistically significant, Paper B finds no correlation):
  - The model must explicitly identify the conflict under a designated `### Conflicting or Divergent Findings` section.
  - Compare study conditions (e.g., patient cohort size, cell line type, dosage, methodology differences) explaining the potential discrepancy.

### 4. Abstention & Insufficiency Mechanism
- If the retrieved passages do not contain verifiable evidence to address the user's specific biomedical question:
  - The model must NOT hallucinate or extrapolate.
  - It must trigger an abstention response:
    > *"Based on the retrieved biomedical literature, there is insufficient evidence to determine [question topic]. The available papers discuss [related topic], but do not report on [missing variable]."*
  - Implement a programmatic relevance check (e.g., minimum cross-encoder score threshold or LLM self-evaluation check) to trigger abstention before generation.

### 5. Structured Response & Confidence Scoring
- Return a structured response model (`BioRAGResponse`):
  ```json
  {
    "query": "Does metformin inhibit mTOR in triple-negative breast cancer?",
    "answer": "Metformin has been demonstrated to inhibit mTOR phosphorylation via AMPK activation in MDA-MB-231 cells [PMID: 32019283, Sec: Results]...",
    "citations": [
      {
        "pmid": "32019283",
        "title": "Metformin Regulation of mTOR in TNBC",
        "section": "Results",
        "chunk_id": "PMC7012345_sec_results_chunk_01",
        "doi": "10.1016/j.canlet.2020...",
        "supporting_text": "Phosphorylation of mTOR at Ser2448 was suppressed by 64% after 24h metformin treatment..."
      }
    ],
    "conflicts_detected": [],
    "confidence_score": 0.92,
    "has_sufficient_evidence": true
  }
  ```

---

## Deliverables
- `backend/app/rag/prompts.py`: Biomedical synthesis prompt templates with citation and conflict guidelines.
- `backend/app/rag/chain.py`: LangChain LCEL RAG chain connecting Hybrid Retriever $\rightarrow$ Prompt $\rightarrow$ Groq LLM $\rightarrow$ Output Parser.
- `backend/app/rag/citation_tracker.py`: Utility to parse generated citation tokens and map them back to retrieved `DocumentChunk` objects.
- Unit tests: `tests/test_generation.py` testing abstention behavior on unanswerable test questions.

---

## Acceptance Criteria
- [ ] 100% of generated claims in the final answer include valid citation anchors linking to provided chunks.
- [ ] Conflicting findings across distinct PMIDs are explicitly flagged and summarized.
- [ ] Abstention is reliably triggered when unanswerable/out-of-scope biomedical questions are submitted.
- [ ] Groq LLaMA 3 response generation begins streaming in under 600ms.
