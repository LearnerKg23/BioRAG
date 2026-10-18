import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ResearchAssistant from './components/Assistant/ResearchAssistant';
import BenchmarkDashboard from './components/Dashboard/BenchmarkDashboard';
import CorpusManager from './components/Papers/CorpusManager';

export default function App() {
  const [activeTab, setActiveTab] = useState('assistant');
  const [stats, setStats] = useState(null);

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/papers/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Background radial gradient glow */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl" />
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-teal-500/5 rounded-full blur-3xl" />
      </div>

      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} stats={stats} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6 relative z-10">
        {activeTab === 'assistant' && <ResearchAssistant />}
        {activeTab === 'benchmark' && <BenchmarkDashboard />}
        {activeTab === 'corpus' && <CorpusManager stats={stats} onRefreshStats={fetchStats} />}
      </main>

      <footer className="border-t border-slate-900 bg-slate-950/80 py-4 text-center text-xs text-slate-500 relative z-10">
        <p>BioRAG — Research Support & Literature Information Retrieval System • Powered by FAISS, BM25, and LLaMA 3</p>
      </footer>
    </div>
  );
}
