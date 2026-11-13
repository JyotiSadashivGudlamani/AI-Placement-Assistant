import React, { useState } from 'react';
import { BookOpen, FileText, ChevronDown, ChevronUp } from 'lucide-react';

export default function CitationCard({ citation }) {
  const [expanded, setExpanded] = useState(false);

  const percentSimilarity = citation.similarity
    ? Math.round(citation.similarity * 100)
    : null;

  return (
    <div className="rounded-xl border border-indigo-200 dark:border-indigo-900/60 bg-indigo-50/70 dark:bg-indigo-950/40 p-2.5 text-xs transition-all shadow-2xs">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <FileText className="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0" />
          <span className="font-semibold text-slate-800 dark:text-slate-200 truncate">
            {citation.filename}
          </span>
          <span className="inline-flex items-center px-1.5 py-0.5 rounded-md text-[10px] font-bold bg-indigo-100 dark:bg-indigo-900/80 text-indigo-700 dark:text-indigo-300">
            Page {citation.page_number}
          </span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {percentSimilarity !== null && (
            <span className="text-[10px] font-mono font-medium text-indigo-600 dark:text-indigo-400">
              {percentSimilarity}% match
            </span>
          )}
          {citation.excerpt && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-0.5 text-indigo-500 hover:text-indigo-700 dark:hover:text-indigo-300 cursor-pointer"
              title={expanded ? 'Hide excerpt' : 'View excerpt'}
            >
              {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          )}
        </div>
      </div>

      {expanded && citation.excerpt && (
        <div className="mt-2 pt-2 border-t border-indigo-100 dark:border-indigo-900/40 text-[11px] text-slate-600 dark:text-slate-400 italic font-serif leading-relaxed">
          "{citation.excerpt}"
        </div>
      )}
    </div>
  );
}
