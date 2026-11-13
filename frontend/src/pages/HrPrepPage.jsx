import React, { useState, useEffect } from 'react';
import {
  Users2,
  Sparkles,
  Bookmark,
  CheckCircle,
  AlertTriangle,
  HelpCircle,
  Trash2,
  ChevronRight,
  Send,
  Building2,
  Briefcase,
  User,
} from 'lucide-react';
import {
  getHRCategories,
  generateHRGuidance,
  saveHRDraft,
  getSavedHRDrafts,
  deleteSavedHRDraft,
} from '../api/hr';

const DEFAULT_CATEGORIES = [
  { id: 'self_introduction', label: 'Self-Introduction' },
  { id: 'strengths_weaknesses', label: 'Strengths & Weaknesses' },
  { id: 'career_goals', label: 'Career Goals' },
  { id: 'teamwork', label: 'Teamwork & Conflict' },
  { id: 'problem_solving', label: 'Problem Solving' },
  { id: 'why_hire_you', label: 'Why Should We Hire You?' },
  { id: 'company_motivation', label: 'Company Motivation' },
];

export default function HrPrepPage() {
  const [categories, setCategories] = useState(DEFAULT_CATEGORIES);
  const [activeCategory, setActiveCategory] = useState('self_introduction');
  const [targetCompany, setTargetCompany] = useState('');
  const [targetRole, setTargetRole] = useState('Software Engineer');
  const [studentBackground, setStudentBackground] = useState('');
  const [loading, setLoading] = useState(false);
  const [guidance, setGuidance] = useState(null);
  const [savedDrafts, setSavedDrafts] = useState([]);
  const [activeTab, setActiveTab] = useState('generate'); // 'generate' | 'saved'
  const [isSaved, setIsSaved] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCategories();
    loadSavedDrafts();
  }, []);

  const loadCategories = async () => {
    try {
      const data = await getHRCategories();
      if (data.categories) setCategories(data.categories);
    } catch {
      // Use fallback
    }
  };

  const loadSavedDrafts = async () => {
    try {
      const data = await getSavedHRDrafts();
      setSavedDrafts(data.drafts || []);
    } catch {
      // Ignore
    }
  };

  const handleGenerate = async (cat = activeCategory) => {
    setLoading(true);
    setError(null);
    setIsSaved(false);
    try {
      const data = await generateHRGuidance({
        category: cat,
        target_company: targetCompany.trim() || null,
        target_role: targetRole.trim() || 'Software Engineer',
        student_background: studentBackground.trim() || null,
      });
      setGuidance(data);
    } catch (err) {
      setError(err.message || 'Failed to generate HR guidance.');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!guidance) return;
    try {
      await saveHRDraft({
        draft_id: guidance.draft_id,
        category: guidance.category,
        question: guidance.question,
        draft_answer: guidance.draft_answer,
        target_company: targetCompany || null,
      });
      setIsSaved(true);
      loadSavedDrafts();
    } catch {
      // Ignore
    }
  };

  const handleDelete = async (draftId) => {
    try {
      await deleteSavedHRDraft(draftId);
      setSavedDrafts((prev) => prev.filter((d) => d.draft_id !== draftId));
    } catch {
      // Ignore
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2.5">
            <Users2 className="w-7 h-7 text-indigo-600 dark:text-indigo-400" />
            HR & Behavioral Interview Preparation
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Personalized behavioral frameworks (STAR, Present-Past-Future) grounded strictly in your real qualifications.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl self-start">
          <button
            onClick={() => setActiveTab('generate')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'generate'
                ? 'bg-white dark:bg-slate-700 text-indigo-600 dark:text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Draft Generator
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
            Saved Responses ({savedDrafts.length})
          </button>
        </div>
      </div>

      {activeTab === 'generate' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Form & Categories */}
          <div className="lg:col-span-1 space-y-5">
            {/* Category Tabs */}
            <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                1. HR Question Category
              </h2>
              <div className="flex flex-col gap-1">
                {categories.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => {
                      setActiveCategory(c.id);
                      handleGenerate(c.id);
                    }}
                    className={`text-left px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all flex items-center justify-between ${
                      activeCategory === c.id
                        ? 'bg-indigo-600 text-white font-semibold shadow-sm shadow-indigo-600/30'
                        : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                    }`}
                  >
                    <span>{c.label}</span>
                    {activeCategory === c.id && <ChevronRight className="w-3.5 h-3.5" />}
                  </button>
                ))}
              </div>
            </div>

            {/* Context Inputs */}
            <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                2. Personalization & Target
              </h2>

              <div className="space-y-3 text-xs">
                <div>
                  <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1 flex items-center gap-1.5">
                    <Building2 className="w-3.5 h-3.5 text-indigo-500" />
                    Target Company (Optional)
                  </label>
                  <input
                    type="text"
                    value={targetCompany}
                    onChange={(e) => setTargetCompany(e.target.value)}
                    placeholder="e.g. Google, Amazon, Infosys"
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1 flex items-center gap-1.5">
                    <Briefcase className="w-3.5 h-3.5 text-indigo-500" />
                    Target Role
                  </label>
                  <input
                    type="text"
                    value={targetRole}
                    onChange={(e) => setTargetRole(e.target.value)}
                    placeholder="e.g. Software Engineer"
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1 flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5 text-indigo-500" />
                    Your Background & Projects
                  </label>
                  <textarea
                    rows={3}
                    value={studentBackground}
                    onChange={(e) => setStudentBackground(e.target.value)}
                    placeholder="e.g. B.Tech CS graduate, built an e-commerce backend in FastAPI, familiar with SQL & Docker..."
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-xs"
                  />
                  <p className="text-[10px] text-slate-400 mt-1 italic">
                    Grounded rule: The AI will only use facts provided here and never invent fake qualifications.
                  </p>
                </div>
              </div>

              <button
                onClick={() => handleGenerate()}
                disabled={loading}
                className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-md shadow-indigo-600/20 flex items-center justify-center gap-2 transition-all disabled:opacity-60"
              >
                <Sparkles className="w-4 h-4" />
                {loading ? 'Crafting Response...' : 'Generate Guidance & Draft'}
              </button>
            </div>
          </div>

          {/* Right Column: Guidance & Personalized Draft */}
          <div className="lg:col-span-2 space-y-5">
            {error && (
              <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs">
                {error}
              </div>
            )}

            {guidance ? (
              <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 space-y-6">
                {/* Header */}
                <div className="flex items-start justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-4">
                  <div>
                    <span className="px-2.5 py-0.5 rounded-md text-[11px] font-bold bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800 mb-2 inline-block">
                      {guidance.framework}
                    </span>
                    <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                      "{guidance.question}"
                    </h2>
                  </div>

                  <button
                    onClick={handleSave}
                    className={`px-3 py-1.5 rounded-xl border text-xs font-medium flex items-center gap-1.5 transition-all shrink-0 ${
                      isSaved
                        ? 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-300 text-emerald-600 dark:text-emerald-400'
                        : 'border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300'
                    }`}
                  >
                    <Bookmark className="w-4 h-4" />
                    <span>{isSaved ? 'Saved' : 'Save Draft'}</span>
                  </button>
                </div>

                {/* Draft Answer */}
                <div className="space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                    <CheckCircle className="w-4 h-4 text-emerald-500" />
                    Personalized Draft Response
                  </h3>
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 text-sm text-slate-800 dark:text-slate-200 leading-relaxed whitespace-pre-line">
                    {guidance.draft_answer}
                  </div>
                </div>

                {/* Step-by-Step Structure */}
                {guidance.sample_structure?.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Response Structure ({guidance.framework})
                    </h3>
                    <div className="space-y-2">
                      {guidance.sample_structure.map((step, idx) => (
                        <div
                          key={idx}
                          className="p-2.5 rounded-xl bg-indigo-50/40 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/40 text-xs text-slate-700 dark:text-slate-300"
                        >
                          {step}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Do's and Don'ts */}
                {guidance.dos_and_donts?.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-amber-500" />
                      Interviewer Tips & Pitfalls to Avoid
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                      {guidance.dos_and_donts.map((tip, idx) => {
                        const isDo = tip.startsWith('DO');
                        return (
                          <div
                            key={idx}
                            className={`p-2.5 rounded-xl border ${
                              isDo
                                ? 'bg-emerald-50/40 dark:bg-emerald-950/20 border-emerald-200/60 text-emerald-800 dark:text-emerald-300'
                                : 'bg-rose-50/40 dark:bg-rose-950/20 border-rose-200/60 text-rose-800 dark:text-rose-300'
                            }`}
                          >
                            {tip}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Follow-up Questions */}
                {guidance.follow_up_questions?.length > 0 && (
                  <div className="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                      <HelpCircle className="w-4 h-4 text-violet-500" />
                      Anticipated Follow-up Questions
                    </h3>
                    <ul className="space-y-1.5 text-xs text-slate-700 dark:text-slate-300">
                      {guidance.follow_up_questions.map((fu, idx) => (
                        <li key={idx} className="flex items-start gap-2 bg-slate-50 dark:bg-slate-800/40 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800">
                          <span className="font-bold text-indigo-500">Q{idx + 1}:</span>
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
                  <Users2 className="w-7 h-7" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">
                    Select an HR Question Category
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-md mx-auto">
                    Choose a category on the left (e.g. Self-Introduction, Career Goals, Why Hire You) to generate structured STAR responses.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Saved Responses Tab */
        <div className="space-y-4">
          {savedDrafts.length === 0 ? (
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-12 text-center">
              <Bookmark className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
                No Saved HR Responses Yet
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                Save your customized drafts to review and practice before interviews.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {savedDrafts.map((sd) => (
                <div
                  key={sd.draft_id}
                  className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3 flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
                        {sd.category}
                      </span>
                      <button
                        onClick={() => handleDelete(sd.draft_id)}
                        className="text-slate-400 hover:text-rose-500 p-1"
                        title="Delete draft"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                    <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                      {sd.question}
                    </h4>
                    <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed whitespace-pre-line line-clamp-4">
                      {sd.draft_answer}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
