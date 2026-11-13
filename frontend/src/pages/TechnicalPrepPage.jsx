import React, { useState, useEffect } from 'react';
import {
  Code2,
  BookOpen,
  CheckCircle2,
  Bookmark,
  BookmarkCheck,
  Copy,
  ChevronRight,
  Sparkles,
  Trash2,
  RefreshCw,
  HelpCircle,
} from 'lucide-react';
import {
  getTechnicalTopics,
  generateTechnicalQuestion,
  saveTechnicalQuestion,
  getSavedTechnicalQuestions,
  deleteSavedTechnicalQuestion,
} from '../api/technical';

export default function TechnicalPrepPage() {
  const [topics, setTopics] = useState([
    'Java', 'Python', 'C and C++', 'OOP', 'DSA', 'DBMS', 'SQL',
    'Operating Systems', 'Computer Networks', 'AI and ML', 'LLM and RAG'
  ]);
  const [selectedTopic, setSelectedTopic] = useState('Java');
  const [difficulty, setDifficulty] = useState('medium');
  const [loading, setLoading] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [savedQuestions, setSavedQuestions] = useState([]);
  const [activeTab, setActiveTab] = useState('practice'); // 'practice' | 'saved'
  const [isSaved, setIsSaved] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadTopics();
    loadSaved();
  }, []);

  const loadTopics = async () => {
    try {
      const data = await getTechnicalTopics();
      if (data.topics) setTopics(data.topics);
    } catch {
      // Fallback to default list
    }
  };

  const loadSaved = async () => {
    try {
      const data = await getSavedTechnicalQuestions();
      setSavedQuestions(data.questions || []);
    } catch {
      // Ignore
    }
  };

  const handleGenerate = async (topicToUse = selectedTopic, diffToUse = difficulty) => {
    setLoading(true);
    setError(null);
    setIsSaved(false);
    try {
      const data = await generateTechnicalQuestion({
        topic: topicToUse,
        difficulty: diffToUse,
        include_code: true,
      });
      setCurrentQuestion(data);
    } catch (err) {
      setError(err.message || 'Failed to generate technical question.');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!currentQuestion) return;
    try {
      await saveTechnicalQuestion({
        question_id: currentQuestion.question_id,
        topic: currentQuestion.topic,
        difficulty: currentQuestion.difficulty,
        question: currentQuestion.question,
        answer: currentQuestion.answer,
        explanation: currentQuestion.explanation,
        code_example: currentQuestion.code_example,
        follow_up_questions: currentQuestion.follow_up_questions || [],
      });
      setIsSaved(true);
      loadSaved();
    } catch {
      // Ignore
    }
  };

  const handleDeleteSaved = async (qid) => {
    try {
      await deleteSavedTechnicalQuestion(qid);
      setSavedQuestions((prev) => prev.filter((q) => q.question_id !== qid));
    } catch {
      // Ignore
    }
  };

  const copyCode = (codeText) => {
    navigator.clipboard.writeText(codeText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Header & Tab Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2.5">
            <Code2 className="w-7 h-7 text-indigo-600 dark:text-indigo-400" />
            Technical Interview Preparation
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Master 11 core CS placement topics with in-depth answers, syntactically verified code, and follow-ups.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl self-start">
          <button
            onClick={() => setActiveTab('practice')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'practice'
                ? 'bg-white dark:bg-slate-700 text-indigo-600 dark:text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Practice Mode
          </button>
          <button
            onClick={() => setActiveTab('saved')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'saved'
                ? 'bg-white dark:bg-slate-700 text-indigo-600 dark:text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            <Bookmark className="w-3.5 h-3.5" />
            Bookmarked ({savedQuestions.length})
          </button>
        </div>
      </div>

      {activeTab === 'practice' ? (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Control Column: Topic & Difficulty Selectors */}
          <div className="lg:col-span-1 space-y-5">
            <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                1. Select Topic
              </h2>
              <div className="flex flex-col gap-1 max-h-[340px] overflow-y-auto pr-1">
                {topics.map((t) => (
                  <button
                    key={t}
                    onClick={() => {
                      setSelectedTopic(t);
                      handleGenerate(t, difficulty);
                    }}
                    className={`text-left px-3.5 py-2 rounded-xl text-xs font-medium transition-all flex items-center justify-between ${
                      selectedTopic === t
                        ? 'bg-indigo-600 text-white font-semibold shadow-sm shadow-indigo-600/30'
                        : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                    }`}
                  >
                    <span>{t}</span>
                    {selectedTopic === t && <ChevronRight className="w-3.5 h-3.5" />}
                  </button>
                ))}
              </div>

              <div className="pt-3 border-t border-slate-100 dark:border-slate-800">
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                  2. Difficulty
                </h2>
                <div className="grid grid-cols-3 gap-1.5">
                  {['easy', 'medium', 'hard'].map((lvl) => (
                    <button
                      key={lvl}
                      onClick={() => setDifficulty(lvl)}
                      className={`py-1.5 capitalize text-xs rounded-lg font-medium transition-all ${
                        difficulty === lvl
                          ? 'bg-indigo-100 dark:bg-indigo-950/70 text-indigo-700 dark:text-indigo-300 border border-indigo-300 dark:border-indigo-800'
                          : 'bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-400 hover:bg-slate-100'
                      }`}
                    >
                      {lvl}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={() => handleGenerate()}
                disabled={loading}
                className="w-full mt-3 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-md shadow-indigo-600/20 flex items-center justify-center gap-2 transition-all disabled:opacity-60"
              >
                {loading ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Sparkles className="w-4 h-4" />
                )}
                {loading ? 'Generating Question...' : 'Next Question'}
              </button>
            </div>
          </div>

          {/* Right Question Presentation Panel */}
          <div className="lg:col-span-3 space-y-5">
            {error && (
              <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs">
                {error}
              </div>
            )}

            {currentQuestion ? (
              <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 space-y-6">
                {/* Question Header */}
                <div className="flex items-start justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-2.5 py-0.5 rounded-md text-[11px] font-bold bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800">
                        {currentQuestion.topic}
                      </span>
                      <span className="px-2.5 py-0.5 rounded-md text-[11px] font-bold capitalize bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                        {currentQuestion.difficulty}
                      </span>
                      {currentQuestion.subtopic && (
                        <span className="text-xs text-slate-400">
                          • {currentQuestion.subtopic}
                        </span>
                      )}
                    </div>
                    <h2 className="text-lg font-bold text-slate-900 dark:text-white leading-relaxed">
                      {currentQuestion.question}
                    </h2>
                  </div>

                  <button
                    onClick={handleSave}
                    className={`p-2 rounded-xl border text-xs font-medium flex items-center gap-1.5 transition-all shrink-0 ${
                      isSaved
                        ? 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-300 text-emerald-600 dark:text-emerald-400'
                        : 'border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300'
                    }`}
                    title={isSaved ? 'Saved to Bookmarks' : 'Bookmark Question'}
                  >
                    {isSaved ? <BookmarkCheck className="w-4 h-4" /> : <Bookmark className="w-4 h-4" />}
                    <span className="hidden sm:inline">{isSaved ? 'Bookmarked' : 'Bookmark'}</span>
                  </button>
                </div>

                {/* Direct Answer Summary */}
                <div className="space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    Direct Interview Answer
                  </h3>
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 text-sm text-slate-800 dark:text-slate-200 leading-relaxed whitespace-pre-line">
                    {currentQuestion.answer}
                  </div>
                </div>

                {/* Deep Technical Explanation */}
                {currentQuestion.explanation && (
                  <div className="space-y-2">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                      <BookOpen className="w-4 h-4 text-indigo-500" />
                      In-Depth Technical Explanation & Trade-offs
                    </h3>
                    <div className="p-4 rounded-xl bg-indigo-50/40 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/40 text-sm text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-line">
                      {currentQuestion.explanation}
                    </div>
                  </div>
                )}

                {/* Code Example Block */}
                {currentQuestion.code_example && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                        <Code2 className="w-4 h-4 text-violet-500" />
                        Code Example ({currentQuestion.code_language || 'Code'})
                      </h3>
                      <button
                        onClick={() => copyCode(currentQuestion.code_example)}
                        className="text-xs text-slate-500 hover:text-indigo-600 flex items-center gap-1 transition-colors"
                      >
                        <Copy className="w-3.5 h-3.5" />
                        {copied ? 'Copied!' : 'Copy Code'}
                      </button>
                    </div>
                    <pre className="p-4 rounded-xl bg-slate-900 text-slate-100 text-xs font-mono overflow-x-auto leading-relaxed border border-slate-800">
                      <code>{currentQuestion.code_example}</code>
                    </pre>
                  </div>
                )}

                {/* Follow-up Questions */}
                {currentQuestion.follow_up_questions?.length > 0 && (
                  <div className="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                      <HelpCircle className="w-4 h-4 text-amber-500" />
                      Likely Follow-up Interview Questions
                    </h3>
                    <ul className="space-y-1.5">
                      {currentQuestion.follow_up_questions.map((fu, idx) => (
                        <li
                          key={idx}
                          className="text-xs text-slate-700 dark:text-slate-300 flex items-start gap-2 bg-slate-50 dark:bg-slate-800/30 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800"
                        >
                          <span className="font-bold text-indigo-500 shrink-0">Q{idx + 1}:</span>
                          <span>{fu}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-12 text-center space-y-4">
                <div className="w-14 h-14 bg-indigo-50 dark:bg-indigo-950/60 rounded-2xl flex items-center justify-center mx-auto text-indigo-600 dark:text-indigo-400">
                  <Code2 className="w-7 h-7" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">
                    Start Your Technical Interview Session
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-md mx-auto">
                    Select any topic on the left (e.g. Java, Python, DSA, OS) and click Next Question to generate technical questions with code examples.
                  </p>
                </div>
                <button
                  onClick={() => handleGenerate()}
                  disabled={loading}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-md shadow-indigo-600/20 inline-flex items-center gap-2 transition-all"
                >
                  <Sparkles className="w-4 h-4" />
                  Generate First Question
                </button>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Saved Questions Tab */
        <div className="space-y-4">
          {savedQuestions.length === 0 ? (
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-12 text-center">
              <Bookmark className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
                No Bookmarked Questions Yet
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                Bookmark important questions during practice mode to review them later here.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {savedQuestions.map((sq) => (
                <div
                  key={sq.question_id}
                  className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3 flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
                        {sq.topic}
                      </span>
                      <button
                        onClick={() => handleDeleteSaved(sq.question_id)}
                        className="text-slate-400 hover:text-rose-500 p-1"
                        title="Delete question"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                    <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                      {sq.question}
                    </h4>
                    <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-3 leading-relaxed">
                      {sq.answer}
                    </p>
                  </div>

                  {sq.code_example && (
                    <pre className="p-2.5 rounded-lg bg-slate-900 text-slate-200 text-[11px] font-mono overflow-hidden max-h-24">
                      <code>{sq.code_example}</code>
                    </pre>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
