import React, { useState, useEffect } from 'react';
import { Search, Database, Download, CheckCircle, ExternalLink, Loader2, BookOpen } from 'lucide-react';

export default function CorpusManager({ stats, onRefreshStats }) {
  const [searchQuery, setSearchQuery] = useState('BRAF melanoma');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [ingestStatus, setIngestStatus] = useState(null);
  const [papersList, setPapersList] = useState([]);

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearching(true);
    setIngestStatus(null);
    try {
      const res = await fetch(`/api/papers/search?query=${encodeURIComponent(searchQuery)}&limit=10`);
      if (res.ok) {
        const data = await res.json();
        setSearchResults(data.articles || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  const handleIngestQuery = async () => {
    setIngesting(true);
    try {
      const res = await fetch('/api/papers/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, limit: 5 })
      });
      if (res.ok) {
        const data = await res.json();
        setIngestStatus(data.message);
        setTimeout(() => {
          if (onRefreshStats) onRefreshStats();
          fetchIngestedList();
        }, 4000);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIngesting(false);
    }
  };

  const fetchIngestedList = async () => {
    try {
      const res = await fetch('/api/papers/list?limit=50');
      if (res.ok) {
        const data = await res.json();
        setPapersList(data.articles || []);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    handleSearch();
    fetchIngestedList();
  }, []);

  return (
    <div className="space-y-6 pb-12">
      {/* Corpus Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
          <span className="text-xs text-slate-400 font-medium">Total Ingested Articles</span>
          <span className="text-2xl font-bold font-mono text-emerald-400 mt-1 block">
            {stats?.total_articles || 0}
          </span>
          <span className="text-[10px] text-slate-500">Tracked in SQLite Manifest</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
          <span className="text-xs text-slate-400 font-medium">Full-Text JATS Articles</span>
          <span className="text-2xl font-bold font-mono text-teal-400 mt-1 block">
            {stats?.fulltext_articles || 0}
          </span>
          <span className="text-[10px] text-teal-500/80">Structured XML Body</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
          <span className="text-xs text-slate-400 font-medium">Total Extracted Sections</span>
          <span className="text-2xl font-bold font-mono text-cyan-400 mt-1 block">
            {stats?.total_sections || 0}
          </span>
          <span className="text-[10px] text-cyan-500/80">Section-aware segments</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
          <span className="text-xs text-slate-400 font-medium">Indices Status</span>
          <div className="flex items-center gap-2 mt-2">
            <span className={`w-2.5 h-2.5 rounded-full ${stats?.faiss_index_ready ? 'bg-emerald-400' : 'bg-amber-400'}`} />
            <span className="text-xs font-mono text-slate-200">
              FAISS: {stats?.faiss_index_ready ? 'Ready' : 'Pending'} | BM25: {stats?.bm25_index_ready ? 'Ready' : 'Pending'}
            </span>
          </div>
        </div>
      </div>

      {/* Europe PMC Live Literature Search */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Database className="w-5 h-5 text-emerald-400" />
              <span>Europe PMC Live Ingestion & Search</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Query millions of open-access biomedical articles and ingest them directly into BioRAG's dual FAISS and BM25 indices.
            </p>
          </div>

          <button
            onClick={handleIngestQuery}
            disabled={ingesting}
            className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-medium text-xs flex items-center gap-2 shadow-lg shadow-emerald-600/30 transition-all cursor-pointer"
          >
            {ingesting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            <span>Ingest Top 5 Articles for Query</span>
          </button>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search Europe PMC by gene, disease, or PMID..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 focus:border-emerald-500 text-sm text-slate-100 outline-none"
            />
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
          </div>
          <button
            type="submit"
            disabled={searching}
            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold"
          >
            {searching ? 'Searching...' : 'Search'}
          </button>
        </form>

        {ingestStatus && (
          <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{ingestStatus}</span>
          </div>
        )}

        {/* Search Results List */}
        <div className="divide-y divide-slate-800/80">
          {searchResults.map((paper, idx) => (
            <div key={idx} className="py-4 space-y-1.5">
              <div className="flex items-start justify-between gap-4">
                <h4 className="text-sm font-semibold text-slate-200 hover:text-emerald-400 transition-colors">
                  {paper.title}
                </h4>
                {paper.isOpenAccess === 'Y' && (
                  <span className="shrink-0 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-teal-500/15 text-teal-300 border border-teal-500/30">
                    Open Access
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 font-mono">
                {paper.authorString || 'Authors not listed'} • {paper.journalTitle || 'Journal'} ({paper.pubYear || 'N/D'})
                {paper.pmcid && ` • ${paper.pmcid}`}
              </p>
              {paper.abstractText && (
                <p className="text-xs text-slate-300/90 line-clamp-2 leading-relaxed">
                  {paper.abstractText}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
