import React from 'react';
import { BookOpen, ExternalLink, Tag, Hash, FileText } from 'lucide-react';

export default function EvidenceInspector({ citations, selectedCitation, onSelectCitation }) {
  if (!citations || citations.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center text-slate-500 border border-slate-800/80 rounded-2xl bg-slate-900/30">
        <BookOpen className="w-12 h-12 stroke-[1.2] text-slate-600 mb-3" />
        <h3 className="text-sm font-semibold text-slate-300">Evidence Inspector</h3>
        <p className="text-xs text-slate-500 max-w-xs mt-1">
          When you ask a biomedical question, retrieved scientific passages and verified citation anchors will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full border border-slate-800 rounded-2xl bg-slate-900/40 overflow-hidden shadow-xl">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-800 bg-slate-900/80 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-semibold text-slate-200">
            Retrieved Scientific Evidence ({citations.length})
          </h3>
        </div>
        <span className="text-xs text-slate-400 font-mono">
          Click citation pill to jump
        </span>
      </div>

      {/* Citations List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {citations.map((c, idx) => {
          const isSelected = selectedCitation && (
            selectedCitation.chunk_id === c.chunk_id ||
            selectedCitation.pmid === c.pmid
          );

          return (
            <div
              key={c.chunk_id || idx}
              onClick={() => onSelectCitation(c)}
              className={`p-4 rounded-xl border transition-all cursor-pointer ${
                isSelected
                  ? 'border-emerald-500/80 bg-emerald-950/20 shadow-lg shadow-emerald-500/10 ring-1 ring-emerald-500/50'
                  : 'border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900'
              }`}
            >
              {/* Paper Meta Header */}
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className="text-xs font-semibold text-slate-200 line-clamp-2">
                  {c.title}
                </span>
                <span className="shrink-0 px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold tracking-wider bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                  {c.section || 'Passage'}
                </span>
              </div>

              {/* Identifiers & Links */}
              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mb-3 font-mono">
                {c.pmid && (
                  <span className="flex items-center gap-1 text-teal-400">
                    <Hash className="w-3 h-3" />
                    PMID: {c.pmid}
                  </span>
                )}
                {c.doi && (
                  <a
                    href={`https://doi.org/${c.doi}`}
                    target="_blank"
                    rel="noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="flex items-center gap-1 text-slate-400 hover:text-emerald-400 transition-colors"
                  >
                    <span>DOI</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>

              {/* Supporting Excerpt */}
              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs text-slate-300 leading-relaxed font-serif">
                "{c.supporting_text || c.text}"
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
