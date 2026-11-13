import React, { useState } from 'react';
import { Send, SlidersHorizontal, Loader2 } from 'lucide-react';

export default function ChatInput({ onSendMessage, disabled = false, loading = false }) {
  const [question, setQuestion] = useState('');
  const [topK, setTopK] = useState(4);
  const [category, setCategory] = useState('');
  const [retrievalMode, setRetrievalMode] = useState('agent');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!question.trim() || disabled || loading) return;

    onSendMessage({
      question: question.trim(),
      topK,
      category: category || null,
      retrievalMode,
    });
    setQuestion('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 p-4 transition-colors">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto space-y-2.5">
        {/* Retrieval Parameters Row */}
        <div className="flex flex-wrap items-center justify-between text-xs text-slate-500 dark:text-slate-400 gap-2 px-1">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1 font-medium">
              <SlidersHorizontal className="w-3.5 h-3.5 text-indigo-500" />
              Scope:
            </span>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="px-2 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 focus:outline-hidden"
            >
              <option value="">All Documents</option>
              <option value="placement">Placement Notes</option>
              <option value="resume">Resume / CV</option>
              <option value="java">Java & OOP</option>
              <option value="python">Python & AI</option>
            </select>

            <span className="hidden sm:inline-block text-slate-300 dark:text-slate-700">|</span>

            <span className="font-medium hidden sm:inline">Engine:</span>
            <select
              value={retrievalMode}
              onChange={(e) => setRetrievalMode(e.target.value)}
              className="px-2 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium focus:outline-hidden"
            >
              <option value="agent">🤖 LangGraph Agent (Multi-Tool Router)</option>
              <option value="hybrid_rerank">⚡ Hybrid + Rerank (Advanced RAG)</option>
              <option value="hybrid">🔀 Hybrid (Vector + BM25)</option>
              <option value="vector">🎯 Dense Vector Search</option>
              <option value="bm25">🔍 BM25 Lexical Search</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="font-medium">Top-K Chunks:</span>
            <div className="flex items-center gap-1">
              {[2, 4, 6].map((k) => (
                <button
                  type="button"
                  key={k}
                  onClick={() => setTopK(k)}
                  className={`px-2 py-0.5 rounded-md text-[11px] font-semibold transition-all cursor-pointer ${
                    topK === k
                      ? 'bg-indigo-600 text-white shadow-2xs'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200'
                  }`}
                >
                  {k}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Input & Send Button Container */}
        <div className="relative flex items-center bg-slate-50 dark:bg-slate-800/80 rounded-2xl border border-slate-200 dark:border-slate-700/80 focus-within:border-indigo-500 dark:focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 transition-all shadow-xs">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a technical concept, interview question, or query about your resume..."
            rows={2}
            disabled={disabled || loading}
            className="w-full px-4 py-3 bg-transparent text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-hidden resize-none"
          />

          <button
            type="submit"
            disabled={!question.trim() || disabled || loading}
            className={`absolute right-3.5 p-2 rounded-xl text-white transition-all shadow-sm ${
              !question.trim() || disabled || loading
                ? 'bg-slate-300 dark:bg-slate-700 cursor-not-allowed text-slate-400'
                : 'bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 cursor-pointer shadow-indigo-600/30'
            }`}
            title="Send query to RAG assistant"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          </button>
        </div>

        <p className="text-[11px] text-center text-slate-400 dark:text-slate-500">
          Answers are strictly grounded in indexed ChromaDB chunks using Llama 3.2:3b. Press Enter to send.
        </p>
      </form>
    </div>
  );
}
