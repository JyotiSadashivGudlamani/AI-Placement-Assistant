import React, { useState, useEffect } from 'react';
import {
  BrainCircuit,
  Timer,
  CheckCircle2,
  XCircle,
  HelpCircle,
  RefreshCw,
  Sparkles,
  Award,
  ChevronRight,
  History,
} from 'lucide-react';
import {
  getAptitudeCategories,
  generateAptitudeQuiz,
  submitAptitudeQuiz,
  getAptitudeHistory,
} from '../api/aptitude';

export default function AptitudePage() {
  const [categories, setCategories] = useState([
    { id: 'all', label: 'All Aptitude Topics' },
    { id: 'quantitative', label: 'Quantitative Aptitude' },
    { id: 'logical', label: 'Logical Reasoning' },
    { id: 'verbal', label: 'Verbal Ability' },
  ]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [questionCount, setQuestionCount] = useState(5);
  const [difficulty, setDifficulty] = useState('medium');
  const [loading, setLoading] = useState(false);

  // Quiz active state
  const [quizState, setQuizState] = useState('idle'); // 'idle' | 'testing' | 'result' | 'history'
  const [quiz, setQuiz] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState({}); // { [question_id]: "A" }
  const [secondsElapsed, setSecondsElapsed] = useState(0);
  const [quizResult, setQuizResult] = useState(null);
  const [historyList, setHistoryList] = useState([]);

  useEffect(() => {
    loadCategories();
    loadHistory();
  }, []);

  // Timer effect
  useEffect(() => {
    let timer;
    if (quizState === 'testing') {
      timer = setInterval(() => {
        setSecondsElapsed((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [quizState]);

  const loadCategories = async () => {
    try {
      const data = await getAptitudeCategories();
      if (data.categories) setCategories(data.categories);
    } catch {
      // Use fallback
    }
  };

  const loadHistory = async () => {
    try {
      const data = await getAptitudeHistory();
      setHistoryList(data.history || []);
    } catch {
      // Ignore
    }
  };

  const handleStartQuiz = async () => {
    setLoading(true);
    try {
      const data = await generateAptitudeQuiz({
        category: selectedCategory,
        count: questionCount,
        difficulty,
      });
      setQuiz(data);
      setCurrentIndex(0);
      setUserAnswers({});
      setSecondsElapsed(0);
      setQuizState('testing');
    } catch {
      // Ignore
    } finally {
      setLoading(false);
    }
  };

  const handleSelectOption = (qid, optKey) => {
    setUserAnswers((prev) => ({
      ...prev,
      [qid]: optKey,
    }));
  };

  const handleSubmitQuiz = async () => {
    if (!quiz) return;
    setLoading(true);
    try {
      const answersList = quiz.questions.map((q) => ({
        question_id: q.question_id,
        selected_option: userAnswers[q.question_id] || null,
      }));

      const res = await submitAptitudeQuiz({
        category: quiz.category,
        answers: answersList,
        time_taken_seconds: secondsElapsed,
      });
      setQuizResult(res);
      setQuizState('result');
      loadHistory();
    } catch {
      // Ignore
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60);
    const rem = secs % 60;
    return `${mins.toString().padStart(2, '0')}:${rem.toString().padStart(2, '0')}`;
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2.5">
            <BrainCircuit className="w-7 h-7 text-indigo-600 dark:text-indigo-400" />
            Aptitude Practice & Assessment
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Quantitative aptitude, logical reasoning, and verbal tests with time tracking and step-by-step solutions.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl self-start">
          <button
            onClick={() => setQuizState('idle')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              quizState !== 'history'
                ? 'bg-white dark:bg-slate-700 text-indigo-600 dark:text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Practice Tests
          </button>
          <button
            onClick={() => setQuizState('history')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
              quizState === 'history'
                ? 'bg-white dark:bg-slate-700 text-indigo-600 dark:text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            History ({historyList.length})
          </button>
        </div>
      </div>

      {/* VIEW 1: Idle Configuration Screen */}
      {quizState === 'idle' && (
        <div className="max-w-xl mx-auto bg-white dark:bg-slate-900 p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div className="text-center space-y-2">
            <div className="w-12 h-12 bg-indigo-50 dark:bg-indigo-950/60 rounded-xl flex items-center justify-center mx-auto text-indigo-600 dark:text-indigo-400">
              <BrainCircuit className="w-6 h-6" />
            </div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">
              Configure Placement Aptitude Quiz
            </h2>
            <p className="text-xs text-slate-500">
              Choose your focus topic and test length to start practice with automatic scoring.
            </p>
          </div>

          <div className="space-y-4 text-xs">
            {/* Category selection */}
            <div>
              <label className="block font-bold text-slate-700 dark:text-slate-300 mb-2">
                Subject Category
              </label>
              <div className="grid grid-cols-2 gap-2">
                {categories.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => setSelectedCategory(c.id)}
                    className={`p-3 rounded-xl border text-left font-medium transition-all ${
                      selectedCategory === c.id
                        ? 'border-indigo-600 bg-indigo-50/50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-400 shadow-sm'
                        : 'border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300'
                    }`}
                  >
                    {c.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Questions count */}
            <div>
              <label className="block font-bold text-slate-700 dark:text-slate-300 mb-2">
                Number of Questions
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[3, 5, 10].map((cnt) => (
                  <button
                    key={cnt}
                    onClick={() => setQuestionCount(cnt)}
                    className={`py-2 rounded-xl border text-center font-semibold transition-all ${
                      questionCount === cnt
                        ? 'border-indigo-600 bg-indigo-600 text-white shadow-sm'
                        : 'border-slate-200 dark:border-slate-700 hover:bg-slate-50 text-slate-700 dark:text-slate-300'
                    }`}
                  >
                    {cnt} Questions
                  </button>
                ))}
              </div>
            </div>

            {/* Difficulty */}
            <div>
              <label className="block font-bold text-slate-700 dark:text-slate-300 mb-2">
                Difficulty Level
              </label>
              <div className="grid grid-cols-3 gap-2">
                {['easy', 'medium', 'hard'].map((lvl) => (
                  <button
                    key={lvl}
                    onClick={() => setDifficulty(lvl)}
                    className={`py-2 rounded-xl capitalize font-medium transition-all ${
                      difficulty === lvl
                        ? 'bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 border border-indigo-300 dark:border-indigo-800'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    {lvl}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <button
            onClick={handleStartQuiz}
            disabled={loading}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-md shadow-indigo-600/20 flex items-center justify-center gap-2 transition-all disabled:opacity-60"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            {loading ? 'Generating Quiz...' : 'Start Aptitude Test'}
          </button>
        </div>
      )}

      {/* VIEW 2: Active Testing Mode */}
      {quizState === 'testing' && quiz && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 space-y-6">
          {/* Test Top Bar */}
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Question {currentIndex + 1} of {quiz.questions.length}
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
                {quiz.questions[currentIndex].subtopic}
              </span>
            </div>

            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-400 font-mono text-xs font-bold">
              <Timer className="w-4 h-4" />
              <span>{formatTime(secondsElapsed)}</span>
            </div>
          </div>

          {/* Question Text */}
          <div className="space-y-4">
            <h2 className="text-base font-bold text-slate-900 dark:text-white leading-relaxed">
              {quiz.questions[currentIndex].question_text}
            </h2>

            {/* Options List */}
            <div className="space-y-2.5">
              {quiz.questions[currentIndex].options.map((opt) => {
                const qid = quiz.questions[currentIndex].question_id;
                const isSelected = userAnswers[qid] === opt.key;
                return (
                  <button
                    key={opt.key}
                    onClick={() => handleSelectOption(qid, opt.key)}
                    className={`w-full p-4 rounded-xl border text-left flex items-start gap-3 transition-all ${
                      isSelected
                        ? 'border-indigo-600 bg-indigo-50/60 dark:bg-indigo-950/40 text-indigo-900 dark:text-white shadow-sm'
                        : 'border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/60 text-slate-700 dark:text-slate-300'
                    }`}
                  >
                    <span
                      className={`w-6 h-6 rounded-lg text-xs font-bold flex items-center justify-center shrink-0 ${
                        isSelected
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                      }`}
                    >
                      {opt.key}
                    </span>
                    <span className="text-xs font-medium pt-0.5">{opt.text}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Test Navigation Footer */}
          <div className="flex items-center justify-between border-t border-slate-100 dark:border-slate-800 pt-4">
            <button
              onClick={() => setCurrentIndex((prev) => Math.max(prev - 1, 0))}
              disabled={currentIndex === 0}
              className="px-4 py-2 text-xs font-semibold rounded-xl border border-slate-200 dark:border-slate-700 disabled:opacity-40"
            >
              Previous
            </button>

            <div className="flex items-center gap-1.5">
              {quiz.questions.map((q, idx) => {
                const isAnswered = !!userAnswers[q.question_id];
                const isCurrent = idx === currentIndex;
                return (
                  <button
                    key={q.question_id}
                    onClick={() => setCurrentIndex(idx)}
                    className={`w-7 h-7 rounded-lg text-xs font-bold transition-all ${
                      isCurrent
                        ? 'ring-2 ring-indigo-600 bg-indigo-600 text-white'
                        : isAnswered
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                    }`}
                  >
                    {idx + 1}
                  </button>
                );
              })}
            </div>

            {currentIndex < quiz.questions.length - 1 ? (
              <button
                onClick={() => setCurrentIndex((prev) => prev + 1)}
                className="px-4 py-2 text-xs font-semibold rounded-xl bg-indigo-600 text-white hover:bg-indigo-700"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleSubmitQuiz}
                disabled={loading}
                className="px-5 py-2 text-xs font-semibold rounded-xl bg-emerald-600 text-white hover:bg-emerald-700 shadow-md shadow-emerald-600/20"
              >
                {loading ? 'Evaluating...' : 'Submit Test'}
              </button>
            )}
          </div>
        </div>
      )}

      {/* VIEW 3: Results & Step-by-Step Explanations */}
      {quizState === 'result' && quizResult && (
        <div className="space-y-6">
          {/* Result Card */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="space-y-1 text-center md:text-left">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Aptitude Assessment Report
              </span>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                {quizResult.score_percentage >= 70
                  ? 'Excellent Problem-Solving Accuracy!'
                  : quizResult.score_percentage >= 40
                  ? 'Good Effort - Review Weak Concepts'
                  : 'Needs Practice & Formula Review'}
              </h2>
              <p className="text-xs text-slate-500">
                Completed in {formatTime(quizResult.time_taken_seconds)} • {quizResult.category_label}
              </p>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-center p-3 rounded-xl bg-slate-50 dark:bg-slate-800">
                <span className="block text-2xl font-black text-indigo-600 dark:text-indigo-400">
                  {quizResult.score_percentage}%
                </span>
                <span className="text-[10px] font-bold text-slate-400 uppercase">Score</span>
              </div>
              <div className="text-center p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600">
                <span className="block text-2xl font-black">{quizResult.correct_count}</span>
                <span className="text-[10px] font-bold uppercase">Correct</span>
              </div>
              <div className="text-center p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-600">
                <span className="block text-2xl font-black">{quizResult.wrong_count}</span>
                <span className="text-[10px] font-bold uppercase">Wrong</span>
              </div>
            </div>

            <button
              onClick={() => setQuizState('idle')}
              className="px-5 py-2.5 bg-indigo-600 text-white text-xs font-semibold rounded-xl hover:bg-indigo-700 shadow-md shadow-indigo-600/20"
            >
              Take Another Test
            </button>
          </div>

          {/* Detailed Question by Question Solution Review */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-indigo-500" />
              Step-by-Step Solutions & Mathematical Explanations
            </h3>

            {quizResult.results.map((item, idx) => (
              <div
                key={item.question_id}
                className={`p-5 rounded-2xl border bg-white dark:bg-slate-900 shadow-sm space-y-3 ${
                  item.is_correct
                    ? 'border-emerald-200 dark:border-emerald-900/60'
                    : 'border-rose-200 dark:border-rose-900/60'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-400">
                    Question {idx + 1}
                  </span>
                  <div className="flex items-center gap-2">
                    {item.is_correct ? (
                      <span className="px-2.5 py-0.5 rounded-md text-[11px] font-bold bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Correct
                      </span>
                    ) : (
                      <span className="px-2.5 py-0.5 rounded-md text-[11px] font-bold bg-rose-100 dark:bg-rose-950 text-rose-700 dark:text-rose-300 flex items-center gap-1">
                        <XCircle className="w-3.5 h-3.5" /> Incorrect
                      </span>
                    )}
                  </div>
                </div>

                <h4 className="text-sm font-bold text-slate-900 dark:text-white leading-relaxed">
                  {item.question_text}
                </h4>

                <div className="flex items-center gap-4 text-xs">
                  <span>
                    Your Answer:{' '}
                    <strong className={item.is_correct ? 'text-emerald-600' : 'text-rose-600'}>
                      {item.selected_option || 'None'}
                    </strong>
                  </span>
                  <span>
                    Correct Answer: <strong className="text-emerald-600">{item.correct_option}</strong>
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300 whitespace-pre-line leading-relaxed">
                  <strong className="block text-indigo-600 dark:text-indigo-400 mb-1">
                    Mathematical / Logical Derivation:
                  </strong>
                  {item.explanation}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* VIEW 4: Past Attempts History */}
      {quizState === 'history' && (
        <div className="space-y-4">
          {historyList.length === 0 ? (
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-12 text-center">
              <History className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
                No Past Attempts Recorded
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                Complete practice tests to build your performance history.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {historyList.map((h) => (
                <div
                  key={h.attempt_id}
                  className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3 flex items-center justify-between"
                >
                  <div className="space-y-1">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
                      {h.category_label || h.category}
                    </span>
                    <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                      Score: {h.score_percentage}%
                    </h4>
                    <p className="text-xs text-slate-400">
                      {h.correct_count}/{h.total_questions} correct • {formatTime(h.time_taken_seconds || 0)}
                    </p>
                  </div>
                  <Award
                    className={`w-8 h-8 ${
                      h.score_percentage >= 70 ? 'text-amber-500' : 'text-slate-300'
                    }`}
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
