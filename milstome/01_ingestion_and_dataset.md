# Milestone 01: Biomedical Literature Ingestion & Dataset Preparation

## Objective
Build a robust, automated ingestion engine capable of querying biomedical literature repositories (primarily **Europe PMC** via REST and BioC APIs), downloading eligible open-access full-text articles and abstracts, parsing structured **JATS XML** format, extracting comprehensive metadata, and persisting articles locally in a structured directory.

---

## Key Tasks & Technical Specifications

### 1. Europe PMC API Client Implementation
- Build an asynchronous/synchronous Python client (`EuropePMCClient`) to interface with Europe PMC REST API:
  - Query endpoints: `/search` (supporting PubMed search syntax: query terms, Boolean operators, publication date ranges, `OPEN_ACCESS:y` filters).
  - Full-text endpoints: Fetch articles by `pmcid` or `ext_id` in JATS XML and BioC formats.
- Implement rate limiting (complying with Europe PMC guidelines: max 3 requests/sec), exponential backoff retries, and pagination support (`cursorMark` / `pageSize`).

### 2. JATS XML & BioC Parsing
- Develop `JATSArticleParser` using `lxml.etree` to reliably parse biomedical article structures:
  - **Metadata Extraction**:
    - Title, Abstract, Journal name, Volume/Issue, Publication Date (year, month).
    - Author names and affiliations.
    - Identifiers: PMID, PMCID, DOI.
    - Mesh terms, Keywords.
  - **Structured Body Parsing**:
    - Parse hierarchical sections (`<sec>`, `<title>`, `<p>`).
    - Capture section titles (e.g., "Introduction", "Materials and Methods", "Results", "Discussion").
    - Preserve figure/table captions and references while stripping noise (inline citation tags, tracking tags).

### 3. Fallback PDF Extraction
- Integrate `PyMuPDF` (`fitz`) as a secondary fallback parser for articles where full-text JATS XML is unavailable, extracting text blocks and identifying major headings using font-size heuristics.

### 4. Raw Storage & Document Manifest
- Save raw XML and parsed structured JSON documents in `data/raw/papers/`.
- Maintain a local SQLite/JSON manifest (`data/metadata.db` or `manifest.json`) tracking:
  - Document ID, PMID, PMCID, Title, Ingestion Timestamp, File Path, Section Count, Full-text availability flag (`has_fulltext: bool`).

---

## Deliverables
- `backend/app/ingestion/europe_pmc.py`: Client for Europe PMC search and retrieval.
- `backend/app/ingestion/xml_parser.py`: JATS XML parser extracting sections and metadata.
- `backend/app/ingestion/pdf_parser.py`: Fallback PDF text and section extractor.
- `backend/app/ingestion/manifest.py`: SQLite metadata tracker for ingested papers.
- CLI script: `python -m backend.app.ingestion.fetch_cli --query "BRAF melanoma resistance" --limit 50`.

---

## Acceptance Criteria
- [ ] Successfully query Europe PMC API and fetch top $N$ papers for complex biomedical queries.
- [ ] Correctly parse JATS XML into structured Python models (`Article`, `Section`, `Metadata`).
- [ ] Section boundaries are extracted with corresponding section titles intact.
- [ ] Metadata fields (`pmid`, `pmcid`, `doi`, `title`, `authors`, `year`) are 100% extracted when present in source XML.
- [ ] Manifest accurately records ingested files and prevents duplicate downloads.
