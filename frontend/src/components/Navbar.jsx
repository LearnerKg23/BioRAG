import React from 'react';
import { Dna, BarChart3, Database, Sparkles, Activity } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, stats }) {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Dna className="w-6 h-6 text-slate-950 font-bold" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent">
                BioRAG
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Evidence-Based Biomedical Research Assistant
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-slate-950/60 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('assistant')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'assistant'
                ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>Assistant</span>
          </button>

          <button
            onClick={() => setActiveTab('benchmark')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'benchmark'
                ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Benchmarks & IR</span>
          </button>

          <button
            onClick={() => setActiveTab('corpus')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'corpus'
                ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Database className="w-4 h-4" />
            <span>Literature Corpus</span>
          </button>
        </nav>

        {/* System Stats Indicator */}
        <div className="hidden md:flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-800/60 border border-slate-700/50 text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-400 pulse-badge" />
            <span className="text-slate-300">
              Corpus: <strong className="text-emerald-400">{stats?.total_articles || 0}</strong> papers
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
