import React, { useState } from 'react';
import { User, Sparkles, BookOpen, Cpu, ChevronRight, CornerDownRight, CheckCircle2 } from 'lucide-react';
import CitationCard from './CitationCard';

export default function ChatBubble({ message, onActionClick }) {
  const isUser = message.role === 'user';
  const [showTrace, setShowTrace] = useState(false);

  const getToolDisplayName = (toolName) => {
    switch (toolName) {
      case 'rag_qa':
        return 'Document RAG Search';
      case 'resume_analysis':
        return 'Resume ATS Analyser';
      case 'job_description_analysis':
        return 'Job Description Matcher';
      case 'technical_prep':
        return 'Technical Interview Engine';
      case 'hr_prep':
        return 'HR Behavioral STAR Coach';
      case 'aptitude':
        return 'Aptitude Practice Generator';
      case 'mock_interview_evaluation':
        return 'Interview Answer Evaluator';
      case 'general_chat':
        return 'Agent Assistant';
      case 'fallback':
        return 'Scope Guardrail';
      default:
        return toolName || 'LangGraph Agent';
    }
  };

  // Basic markdown-friendly renderer (handles bolding, lists, and linebreaks cleanly)
  const renderFormattedText = (text) => {
    if (!text) return null;

    const lines = text.split('\n');
    return lines.map((line, index) => {
      // Heading format: # Heading, ## Heading, ### Heading
      if (line.startsWith('# ')) {
        return (
          <h3 key={index} className="text-base font-bold my-2 text-slate-900 dark:text-white">
            {line.replace('# ', '')}
          </h3>
        );
      }
      if (line.startsWith('## ') || line.startsWith('### ')) {
        return (
          <h4 key={index} className="text-sm font-bold my-1.5 text-slate-800 dark:text-slate-100">
            {line.replace(/^###?\s+/, '')}
          </h4>
        );
      }

      // Bullet format
      if (line.trim().startsWith('* ') || line.trim().startsWith('- ')) {
        const bulletContent = line.trim().replace(/^[\*\-]\s+/, '');
        return (
          <div key={index} className="flex items-start gap-2 my-1 pl-2">
            <span className="text-indigo-500 font-bold leading-5">•</span>
            <span className="flex-1">{parseInlineStyles(bulletContent)}</span>
          </div>
        );
      }

      // Code blocks (triple backticks)
      if (line.trim().startsWith('```')) {
        return null; // simple line handler
      }

      // Empty line / paragraph break
      if (!line.trim()) {
        return <div key={index} className="h-2" />;
      }

      return (
        <p key={index} className="my-1 leading-relaxed">
          {parseInlineStyles(line)}
        </p>
      );
    });
  };

  // Helper to parse **bold** and `code` inline
  const parseInlineStyles = (content) => {
    const parts = content.split(/(\*\*.*?\*\*|`.*?`)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={i} className="font-semibold text-slate-900 dark:text-slate-100">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code
            key={i}
            className="px-1.5 py-0.5 mx-0.5 rounded-md font-mono text-xs bg-slate-100 dark:bg-slate-800 text-indigo-600 dark:text-indigo-400 border border-slate-200 dark:border-slate-700"
          >
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  return (
    <div className={`flex gap-3 mb-6 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div
        className={`w-9 h-9 rounded-2xl flex items-center justify-center shrink-0 shadow-xs ${
          isUser
            ? 'bg-indigo-600 text-white'
            : 'bg-gradient-to-tr from-slate-900 to-indigo-900 text-indigo-400 dark:from-indigo-950 dark:to-slate-800 border border-indigo-500/20'
        }`}
      >
        {isUser ? <User className="w-5 h-5" /> : <Sparkles className="w-5 h-5" />}
      </div>

      {/* Bubble Container */}
      <div className={`max-w-[85%] sm:max-w-[78%] space-y-2.5`}>
        {/* Tool Badge / Metadata Banner */}
        {!isUser && message.toolUsed && (
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full font-semibold bg-indigo-50 dark:bg-indigo-950/70 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800/60 shadow-2xs">
              <Cpu className="w-3.5 h-3.5" />
              LangGraph: {getToolDisplayName(message.toolUsed)}
            </span>
            {message.intentConfidence && (
              <span className="text-[11px] text-slate-400">
                Confidence: {Math.round(message.intentConfidence * 100)}%
              </span>
            )}
            {message.executionPath && message.executionPath.length > 0 && (
              <button
                type="button"
                onClick={() => setShowTrace(!showTrace)}
                className="text-[11px] text-indigo-500 hover:text-indigo-600 underline cursor-pointer ml-auto"
              >
                {showTrace ? 'Hide Trace' : `Trace (${message.executionPath.length} steps)`}
              </button>
            )}
          </div>
        )}

        {/* Execution Trace Collapsible Drawer */}
        {!isUser && showTrace && message.executionPath && message.executionPath.length > 0 && (
          <div className="p-3 bg-slate-100 dark:bg-slate-900/90 rounded-xl border border-slate-200 dark:border-slate-800 text-xs font-mono space-y-1">
            <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-1">
              StateGraph Execution Trace
            </div>
            {message.executionPath.map((step, idx) => (
              <div key={idx} className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                <ChevronRight className="w-3 h-3 text-indigo-500 shrink-0" />
                <span>{step}</span>
              </div>
            ))}
          </div>
        )}

        {/* Main Bubble Content */}
        <div
          className={`px-5 py-3.5 rounded-2xl text-sm shadow-xs transition-colors ${
            isUser
              ? 'bg-indigo-600 text-white rounded-tr-xs'
              : 'bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-800 rounded-tl-xs'
          }`}
        >
          <div className="leading-relaxed">{renderFormattedText(message.content)}</div>
        </div>

        {/* Citations block for Assistant responses */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="space-y-1.5 pt-1 pl-1">
            <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              <BookOpen className="w-3.5 h-3.5 text-indigo-500" />
              <span>Verified Document Sources ({message.citations.length})</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {message.citations.map((citation, idx) => (
                <CitationCard key={citation.chunk_id || idx} citation={citation} />
              ))}
            </div>
          </div>
        )}

        {/* Suggested Follow-up Actions */}
        {!isUser && message.suggestedActions && message.suggestedActions.length > 0 && (
          <div className="pt-1.5 pl-1 flex flex-wrap gap-2">
            {message.suggestedActions.map((actionText, actIdx) => (
              <button
                key={actIdx}
                type="button"
                onClick={() => onActionClick && onActionClick(actionText)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 hover:bg-indigo-50 dark:bg-slate-800 dark:hover:bg-indigo-950/60 text-slate-700 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 border border-slate-200 dark:border-slate-700/80 transition-colors cursor-pointer"
              >
                <CornerDownRight className="w-3 h-3 text-indigo-500" />
                {actionText}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
