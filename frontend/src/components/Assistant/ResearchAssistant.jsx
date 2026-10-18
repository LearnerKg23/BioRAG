import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Sparkles, SlidersHorizontal, AlertTriangle, ShieldAlert, CheckCircle2, Loader2, BookOpen } from 'lucide-react';
import EvidenceInspector from './EvidenceInspector';

const SAMPLE_PROMPTS = [
  "What is the therapeutic mechanism of dabrafenib in metastatic melanoma?",
  "How do secondary mutations in NRAS or MEK1 confer resistance to RAF inhibitors?",
  "Does osimertinib overcome the EGFR T790M gatekeeper mutation in NSCLC?",
  "What effect does pembrolizumab combined with chemotherapy have in PD-L1 positive TNBC?",
  "What is the recommended lunar regolith extraction protocol for treating cardiac arrhythmias on Mars?"
];

export default function ResearchAssistant() {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('hybrid_rrf');
  const [k, setK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [error, setError] = useState(null);

  const handleQuery = async (searchQuery) => {
    const q = searchQuery || query;
    if (!q.trim()) return;

    setLoading(true);
    setError(null);
    setSelectedCitation(null);

    try {
      const res = await fetch('/api/chat/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, k: parseInt(k, 10), mode })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to fetch response from BioRAG server.');
      }

      const data = await res.json();
      setResponse(data);
      if (data.citations && data.citations.length > 0) {
        setSelectedCitation(data.citations[0]);
      }
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Render citation anchors inside Markdown text as interactive pills
  const renderInteractiveText = (text) => {
    if (!text) return '';
    const citationRegex = /\[(PMID|PMCID|DOC):\s*([^,\]]+),\s*Sec:\s*([^\]]+)\]/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = citationRegex.exec(text)) !== null) {
      const fullMatch = match[0];
      const pmid = match[2].trim();
      const section = match[3].trim();
      const matchStart = match.index;

      if (matchStart > lastIndex) {
        parts.push(text.substring(lastIndex, matchStart));
      }

      parts.push(
        <button
          key={`cit_${matchStart}`}
          onClick={() => {
            const matched = response?.citations?.find(c => c.pmid === pmid || c.pmcid === pmid);
            if (matched) setSelectedCitation(matched);
          }}
          className="inline-flex items-center gap-1 mx-1 px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/25 border border-emerald-500/30 transition-all cursor-pointer"
          title={`Click to inspect passage for PMID ${pmid}`}
        >
          <span>[{pmid}]</span>
          <span className="text-[10px] text-emerald-400/80 font-normal">{section}</span>
        </button>
      );

      lastIndex = matchStart + fullMatch.length;
    }

    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return parts;
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-6rem)]">
      {/* Left Panel: Query, Settings & Answer Generation */}
      <div className="lg:col-span-7 flex flex-col h-full space-y-4">
        {/* Search & Prompt Controls */}
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl space-y-3">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleQuery();
            }}
            className="flex items-center gap-2"
          >
            <div className="relative flex-1">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask a question about diseases, biomarkers, genes, pathways, or treatments..."
                className="w-full pl-4 pr-10 py-3 rounded-xl bg-slate-950 border border-slate-800 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-sm text-slate-100 placeholder:text-slate-500 outline-none transition-all shadow-inner"
              />
              <Sparkles className="w-4 h-4 text-emerald-500 absolute right-3.5 top-3.5 pointer-events-none" />
            </div>

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-5 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-medium text-sm flex items-center gap-2 shadow-lg shadow-emerald-600/30 transition-all shrink-0 cursor-pointer"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              <span>Ask BioRAG</span>
            </button>
          </form>

          {/* Quick Sample Queries */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
            <span className="text-slate-500 font-medium shrink-0">Try:</span>
            {SAMPLE_PROMPTS.map((prompt, i) => (
              <button
                key={i}
                type="button"
                onClick={() => {
                  setQuery(prompt);
                  handleQuery(prompt);
                }}
                className="shrink-0 px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-300 hover:text-emerald-300 border border-slate-700/60 transition-colors cursor-pointer"
              >
                {prompt.slice(0, 42)}...
              </button>
            ))}
          </div>

          {/* Retrieval Settings Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-slate-800/80 text-xs text-slate-400">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5">
                <SlidersHorizontal className="w-3.5 h-3.5 text-emerald-400" />
                <span className="font-medium text-slate-300">Retrieval:</span>
              </div>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-slate-200 outline-none focus:border-emerald-500"
              >
                <option value="hybrid_rrf">Hybrid RRF (FAISS + BM25)</option>
                <option value="faiss_mmr">FAISS (MMR Diverse)</option>
                <option value="faiss_cosine">FAISS (Cosine)</option>
                <option value="bm25_only">BM25 (Sparse Keyword)</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span>Top-K Passages:</span>
              <input
                type="range"
                min="1"
                max="10"
                value={k}
                onChange={(e) => setK(e.target.value)}
                className="w-20 accent-emerald-500 cursor-pointer"
              />
              <span className="font-mono text-emerald-400 font-bold">{k}</span>
            </div>
          </div>
        </div>

        {/* Answer Display Card */}
        <div className="flex-1 rounded-2xl bg-slate-900/40 border border-slate-800 p-6 overflow-y-auto shadow-xl space-y-4">
          {error && (
            <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 text-sm flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div>
                <strong className="block font-semibold">Error</strong>
                <p className="text-xs text-red-300/90 mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {loading && (
            <div className="h-64 flex flex-col items-center justify-center space-y-3 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
              <p className="text-sm font-medium">Retrieving scientific literature & synthesizing evidence...</p>
            </div>
          )}

          {!loading && !response && !error && (
            <div className="h-64 flex flex-col items-center justify-center text-center text-slate-500 space-y-2">
              <BookOpen className="w-10 h-10 stroke-[1.2] text-slate-600" />
              <p className="text-sm">Enter a biomedical query or select a sample prompt to begin analysis.</p>
            </div>
          )}

          {!loading && response && (
            <div className="space-y-4">
              {/* Status & Confidence Banner */}
              <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
                <div className="flex items-center gap-2">
                  {response.has_sufficient_evidence ? (
                    <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Grounded Evidence Found
                    </span>
                  ) : (
                    <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                      <ShieldAlert className="w-3.5 h-3.5" />
                      Abstained: Insufficient Literature
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
                  <span>Confidence:</span>
                  <div className="w-20 bg-slate-800 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full ${
                        response.confidence_score > 0.7
                          ? 'bg-emerald-500'
                          : response.confidence_score > 0.4
                          ? 'bg-amber-500'
                          : 'bg-red-500'
                      }`}
                      style={{ width: `${Math.round(response.confidence_score * 100)}%` }}
                    />
                  </div>
                  <span className="font-bold text-slate-200">
                    {Math.round(response.confidence_score * 100)}%
                  </span>
                </div>
              </div>

              {/* Contradiction Alert Card if found */}
              {response.conflicts_detected && response.conflicts_detected.length > 0 && (
                <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-500/40 text-amber-200 space-y-2">
                  <div className="flex items-center gap-2 text-sm font-bold text-amber-300">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Cross-Study Divergence Detected</span>
                  </div>
                  <p className="text-xs text-amber-200/90 leading-relaxed">
                    The literature presents differing findings across reported studies. Review the comparison below:
                  </p>
                  {response.conflicts_detected.map((conf, ci) => (
                    <div key={ci} className="p-2.5 rounded-lg bg-amber-950/50 border border-amber-500/20 text-xs">
                      <span className="font-mono text-amber-400 font-bold block mb-1">Observation:</span>
                      <p>{conf.potential_reason}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Main Answer Content */}
              <div className="prose prose-invert max-w-none text-slate-200 text-sm leading-relaxed space-y-3 font-sans">
                {renderInteractiveText(response.answer)}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right Panel: Evidence Inspector */}
      <div className="lg:col-span-5 h-full">
        <EvidenceInspector
          citations={response?.citations || []}
          selectedCitation={selectedCitation}
          onSelectCitation={(c) => setSelectedCitation(c)}
        />
      </div>
    </div>
  );
}
