import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  Sparkles,
  Send,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Award,
  RefreshCw,
  History,
  Lightbulb,
  BarChart,
  User,
  Bot,
  ChevronRight,
} from 'lucide-react';
import {
  startMockInterview,
  submitMockAnswer,
  getMockSession,
  getMockHistory,
} from '../api/mockInterview';

export default function MockInterviewPage() {
  const [interviewType, setInterviewType] = useState('technical'); // 'technical' | 'hr'
  const [topic, setTopic] = useState('Java');
  const [difficulty, setDifficulty] = useState('medium');
  const [totalQuestions, setTotalQuestions] = useState(3);
  const [loading, setLoading] = useState(false);
  const [evaluating, setEvaluating] = useState(false);

  // Active Session state
  const [session, setSession] = useState(null); // Full session object
  const [studentInput, setStudentInput] = useState('');
  const [historyList, setHistoryList] = useState([]);
  const [activeTab, setActiveTab] = useState('session'); // 'session' | 'history'
  const [error, setError] = useState(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const data = await getMockHistory();
      setHistoryList(data.sessions || []);
    } catch {
      // Ignore
    }
  };

  const handleStart = async () => {
    setLoading(true);
    setError(null);
    try {
      const initData = await startMockInterview({
        interview_type: interviewType,
        topic,
        difficulty,
        total_questions: totalQuestions,
      });

      // Fetch full session details
      const full = await getMockSession(initData.session_id);
      setSession(full);
      setStudentInput('');
      loadHistory();
    } catch (err) {
      setError(err.message || 'Failed to start mock interview.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!studentInput.trim() || !session) return;
    setEvaluating(true);
    setError(null);
    try {
      await submitMockAnswer(session.session_id, studentInput.trim());
      const updated = await getMockSession(session.session_id);
      setSession(updated);
      setStudentInput('');
      loadHistory();
    } catch (err) {
      setError(err.message || 'Failed to evaluate answer.');
    } finally {
      setEvaluating(false);
    }
  };

  const loadPastSession = async (sessId) => {
    setLoading(true);
    try {
      const past = await getMockSession(sessId);
      setSession(past);
      setActiveTab('session');
    } catch {
      // Ignore
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2.5">
            <MessageSquare className="w-7 h-7 text-indigo-600 dark:text-indigo-400" />
            Interactive Mock Interview Room
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Turn-by-turn simulation scored across 5 criteria: Correctness, Relevance, Completeness, Clarity & Communication.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl self-start">
          <button
            onClick={() => setActiveTab('session')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'session'
                ? 'bg-white dark:bg-slate-700 text-indigo-600 dark:text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Live Interview
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'history'
                ? 'bg-white dark:bg-slate-700 text-indigo-600 dark:text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            History ({historyList.length})
          </button>
        </div>
      </div>

      {activeTab === 'session' ? (
        <div className="space-y-6">
          {/* Setup Bar (Visible when no active session or session completed) */}
          {(!session || session.status === 'completed') && (
            <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Start a New Mock Interview Session
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
                {/* Type */}
                <div>
                  <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1">
                    Interview Type
                  </label>
                  <select
                    value={interviewType}
                    onChange={(e) => setInterviewType(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
                  >
                    <option value="technical">Technical Round</option>
                    <option value="hr">HR & Behavioral Round</option>
                  </select>
                </div>

                {/* Topic */}
                <div>
                  <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1">
                    Topic / Specialization
                  </label>
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="e.g. Java, Python, DSA, OS"
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
                  />
                </div>

                {/* Difficulty */}
                <div>
                  <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1">
                    Target Level
                  </label>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
                  >
                    <option value="easy">Junior / Entry Level</option>
                    <option value="medium">Standard Campus Placement</option>
                    <option value="hard">Senior / Competitive</option>
                  </select>
                </div>

                {/* Questions Count */}
                <div>
                  <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1">
                    Length
                  </label>
                  <select
                    value={totalQuestions}
                    onChange={(e) => setTotalQuestions(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
                  >
                    <option value={2}>2 Questions (Quick Mock)</option>
                    <option value={3}>3 Questions (Standard)</option>
                    <option value={5}>5 Questions (Comprehensive)</option>
                  </select>
                </div>
              </div>

              <button
                onClick={handleStart}
                disabled={loading}
                className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-md shadow-indigo-600/20 flex items-center justify-center gap-2 transition-all disabled:opacity-60"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                {loading ? 'Initializing Interviewer...' : 'Launch Mock Interview'}
              </button>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs">
              {error}
            </div>
          )}

          {/* Active Interview Room */}
          {session && (
            <div className="space-y-6">
              {/* Session Status Header */}
              <div className="flex items-center justify-between p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-md text-[11px] font-bold uppercase bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
                    {session.interview_type}
                  </span>
                  <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    {session.topic} ({session.difficulty})
                  </span>
                </div>

                <div className="flex items-center gap-3 text-xs">
                  <span className="text-slate-500">
                    Progress: <strong>{session.completed_questions}/{session.total_questions}</strong>
                  </span>
                  {session.average_score != null && (
                    <span className="px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950 text-emerald-600 font-bold">
                      Avg Score: {session.average_score}/10
                    </span>
                  )}
                </div>
              </div>

              {/* Turns History Conversation */}
              <div className="space-y-6">
                {session.turns?.map((turn, idx) => (
                  <div key={idx} className="space-y-4">
                    {/* Interviewer Question Bubble */}
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center shrink-0">
                        <Bot className="w-4 h-4" />
                      </div>
                      <div className="flex-1 p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-1">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-500">
                          Interviewer • Question {turn.turn_number}
                        </span>
                        <p className="text-sm font-bold text-slate-900 dark:text-white leading-relaxed">
                          {turn.question}
                        </p>
                      </div>
                    </div>

                    {/* Student Answer Bubble */}
                    {turn.student_answer && (
                      <div className="flex items-start gap-3 justify-end pl-10">
                        <div className="flex-1 p-4 rounded-2xl bg-indigo-600 text-white shadow-md shadow-indigo-600/20 space-y-1 max-w-2xl">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-200">
                            Your Answer
                          </span>
                          <p className="text-xs leading-relaxed whitespace-pre-line">
                            {turn.student_answer}
                          </p>
                        </div>
                        <div className="w-8 h-8 rounded-xl bg-slate-700 text-white flex items-center justify-center shrink-0">
                          <User className="w-4 h-4" />
                        </div>
                      </div>
                    )}

                    {/* 5-Criteria Evaluation Card */}
                    {turn.scores && (
                      <div className="ml-11 p-5 rounded-2xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-4">
                        <div className="flex items-center justify-between border-b border-slate-200/60 dark:border-slate-800 pb-3">
                          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                            <BarChart className="w-4 h-4 text-indigo-500" />
                            5-Criteria Interview Rubric Evaluation
                          </span>
                          <span className="text-sm font-black text-indigo-600 dark:text-indigo-400">
                            Overall: {turn.scores.overall_score}/10
                          </span>
                        </div>

                        {/* Scores grid */}
                        <div className="grid grid-cols-5 gap-2 text-center text-xs">
                          <div className="p-2 rounded-xl bg-white dark:bg-slate-800 shadow-sm">
                            <span className="block text-base font-bold text-slate-900 dark:text-white">
                              {turn.scores.correctness}/10
                            </span>
                            <span className="text-[10px] text-slate-400">Correctness</span>
                          </div>
                          <div className="p-2 rounded-xl bg-white dark:bg-slate-800 shadow-sm">
                            <span className="block text-base font-bold text-slate-900 dark:text-white">
                              {turn.scores.relevance}/10
                            </span>
                            <span className="text-[10px] text-slate-400">Relevance</span>
                          </div>
                          <div className="p-2 rounded-xl bg-white dark:bg-slate-800 shadow-sm">
                            <span className="block text-base font-bold text-slate-900 dark:text-white">
                              {turn.scores.completeness}/10
                            </span>
                            <span className="text-[10px] text-slate-400">Completeness</span>
                          </div>
                          <div className="p-2 rounded-xl bg-white dark:bg-slate-800 shadow-sm">
                            <span className="block text-base font-bold text-slate-900 dark:text-white">
                              {turn.scores.clarity}/10
                            </span>
                            <span className="text-[10px] text-slate-400">Clarity</span>
                          </div>
                          <div className="p-2 rounded-xl bg-white dark:bg-slate-800 shadow-sm">
                            <span className="block text-base font-bold text-slate-900 dark:text-white">
                              {turn.scores.communication}/10
                            </span>
                            <span className="text-[10px] text-slate-400">Communication</span>
                          </div>
                        </div>

                        {/* Actionable Feedback */}
                        {turn.feedback && (
                          <div className="text-xs text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800/40 p-3.5 rounded-xl border border-slate-100 dark:border-slate-800 leading-relaxed">
                            <strong className="block text-slate-900 dark:text-white mb-1">
                              Interviewer Feedback:
                            </strong>
                            {turn.feedback}
                          </div>
                        )}

                        {/* Improved Model Answer */}
                        {turn.improved_answer && (
                          <div className="text-xs text-indigo-900 dark:text-indigo-200 bg-indigo-50/50 dark:bg-indigo-950/20 p-3.5 rounded-xl border border-indigo-100 dark:border-indigo-900/40 leading-relaxed">
                            <strong className="block text-indigo-700 dark:text-indigo-300 mb-1 flex items-center gap-1.5">
                              <Lightbulb className="w-3.5 h-3.5" />
                              Model High-Scoring Response:
                            </strong>
                            {turn.improved_answer}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Active Answer Input (if session still in progress) */}
              {session.status === 'in_progress' ? (
                <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300">
                    Your Response to Question {session.completed_questions + 1}:
                  </label>
                  <textarea
                    rows={4}
                    value={studentInput}
                    onChange={(e) => setStudentInput(e.target.value)}
                    placeholder="Type your response as you would speak in an interview. Structure your thoughts clearly..."
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-xs"
                  />
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] text-slate-400">
                      Evaluated on Correctness, Relevance, Completeness, Clarity, and Communication.
                    </span>
                    <button
                      onClick={handleSubmitAnswer}
                      disabled={evaluating || !studentInput.trim()}
                      className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-md shadow-indigo-600/20 flex items-center gap-2 transition-all disabled:opacity-50"
                    >
                      {evaluating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                      {evaluating ? 'Evaluating Response...' : 'Submit Answer'}
                    </button>
                  </div>
                </div>
              ) : (
                /* Completed Session Summary Card */
                session.final_summary && (
                  <div className="p-6 rounded-2xl bg-gradient-to-tr from-indigo-500/10 via-purple-500/10 to-transparent border border-indigo-200 dark:border-indigo-900/60 space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Award className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
                        <h3 className="text-base font-bold text-slate-900 dark:text-white">
                          Interview Session Completed: {session.final_summary.overall_performance}
                        </h3>
                      </div>
                      <span className="text-lg font-black text-indigo-600 dark:text-indigo-400">
                        Score: {session.final_summary.average_score}/10
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <div className="p-3.5 rounded-xl bg-white/80 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 space-y-1.5">
                        <span className="font-bold text-emerald-600 block">Observed Strengths:</span>
                        <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-300">
                          {session.final_summary.strengths_observed?.map((s, idx) => (
                            <li key={idx}>{s}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="p-3.5 rounded-xl bg-white/80 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 space-y-1.5">
                        <span className="font-bold text-amber-600 block">Areas to Polish:</span>
                        <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-300">
                          {session.final_summary.areas_to_improve?.map((a, idx) => (
                            <li key={idx}>{a}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )
              )}
            </div>
          )}
        </div>
      ) : (
        /* History Tab */
        <div className="space-y-4">
          {historyList.length === 0 ? (
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-12 text-center">
              <History className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
                No Mock Interview Records Found
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                Complete an interview session to review feedback and track performance.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {historyList.map((h) => (
                <div
                  key={h.session_id}
                  onClick={() => loadPastSession(h.session_id)}
                  className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3 cursor-pointer hover:border-indigo-500 transition-all flex items-center justify-between"
                >
                  <div className="space-y-1">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
                      {h.interview_type} • {h.topic}
                    </span>
                    <h4 className="text-sm font-bold text-slate-900 dark:text-white capitalize">
                      {h.difficulty} Difficulty
                    </h4>
                    <p className="text-xs text-slate-400">
                      {h.completed_questions}/{h.total_questions} questions answered
                    </p>
                  </div>
                  {h.average_score != null ? (
                    <div className="text-right">
                      <span className="text-xl font-bold text-emerald-600">
                        {h.average_score}/10
                      </span>
                      <span className="text-[10px] block text-slate-400">Avg Score</span>
                    </div>
                  ) : (
                    <span className="text-xs text-amber-500 font-semibold">In Progress</span>
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
