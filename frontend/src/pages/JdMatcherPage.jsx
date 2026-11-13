import React, { useState, useEffect } from 'react';
import {
  Briefcase,
  Sparkles,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Lightbulb,
  Building2,
  FileText,
  RefreshCw,
  BarChart3,
  Calendar,
  History,
  Target,
} from 'lucide-react';
import { analyzeJobDescription, getJDHistory } from '../api/jd';
import { listResumes } from '../api/resume';

export default function JdMatcherPage() {
  const [jdText, setJdText] = useState('');
  const [roleTitle, setRoleTitle] = useState('Software Engineer');
  const [companyName, setCompanyName] = useState('');
  const [resumes, setResumes] = useState([]);
  const [selectedResumeId, setSelectedResumeId] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [historyList, setHistoryList] = useState([]);
  const [activeTab, setActiveTab] = useState('analyze'); // 'analyze' | 'history'
  const [error, setError] = useState(null);

  useEffect(() => {
    loadResumes();
    loadHistory();
  }, []);

  const loadResumes = async () => {
    try {
      const data = await listResumes();
      setResumes(data.resumes || []);
      if (data.resumes?.length > 0) {
        setSelectedResumeId(data.resumes[0].resume_id);
      }
    } catch {
      // Ignore
    }
  };

  const loadHistory = async () => {
    try {
      const data = await getJDHistory();
      setHistoryList(data.matches || []);
    } catch {
      // Ignore
    }
  };

  const handleAnalyze = async () => {
    if (!jdText.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeJobDescription({
        jd_text: jdText,
        role_title: roleTitle || 'Software Engineer',
        company_name: companyName || null,
        resume_id: selectedResumeId || null,
      });
      setResult(data);
      loadHistory();
    } catch (err) {
      setError(err.message || 'Failed to analyze Job Description.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2.5">
            <Briefcase className="w-7 h-7 text-indigo-600 dark:text-indigo-400" />
            Job Description Analyser & ATS Matcher
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Compare target Job Descriptions against your verified resume with transparent mathematical scoring.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl self-start">
          <button
            onClick={() => setActiveTab('analyze')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'analyze'
                ? 'bg-white dark:bg-slate-700 text-indigo-600 dark:text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Matcher
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

      {activeTab === 'analyze' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Input Form */}
          <div className="lg:col-span-1 space-y-5">
            <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                1. Job Details
              </h2>

              <div className="space-y-3 text-xs">
                <div>
                  <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1">
                    Role Title
                  </label>
                  <input
                    type="text"
                    value={roleTitle}
                    onChange={(e) => setRoleTitle(e.target.value)}
                    placeholder="e.g. Backend Engineer, Java Developer"
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1">
                    Hiring Company (Optional)
                  </label>
                  <input
                    type="text"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    placeholder="e.g. Microsoft, Oracle, FinTech Startup"
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                {/* Resume Selector */}
                <div>
                  <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1 flex items-center justify-between">
                    <span>Match Against Resume</span>
                    {resumes.length === 0 && (
                      <span className="text-[10px] text-amber-500">No resumes uploaded</span>
                    )}
                  </label>
                  <select
                    value={selectedResumeId}
                    onChange={(e) => setSelectedResumeId(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="">No Resume (General JD Breakdown)</option>
                    {resumes.map((r) => (
                      <option key={r.resume_id} value={r.resume_id}>
                        {r.filename} ({r.skills_count} skills)
                      </option>
                    ))}
                  </select>
                </div>

                {/* Paste Job Description */}
                <div>
                  <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1">
                    Paste Job Description Text
                  </label>
                  <textarea
                    rows={8}
                    value={jdText}
                    onChange={(e) => setJdText(e.target.value)}
                    placeholder="Paste the job requirements, qualifications, and role description here..."
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-xs font-mono"
                  />
                </div>
              </div>

              <button
                onClick={handleAnalyze}
                disabled={loading || !jdText.trim()}
                className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-md shadow-indigo-600/20 flex items-center justify-center gap-2 transition-all disabled:opacity-60"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                {loading ? 'Analyzing Requirements...' : 'Analyze & Match Skills'}
              </button>
            </div>
          </div>

          {/* Right Column: Match Analysis & Action Plan */}
          <div className="lg:col-span-2 space-y-5">
            {error && (
              <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs">
                {error}
              </div>
            )}

            {result ? (
              <div className="space-y-5">
                {/* Score Card Banner */}
                {result.skill_match && (
                  <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row items-center justify-between gap-6">
                    <div className="space-y-1 text-center md:text-left">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                          Transparent Skill Match Score
                        </span>
                        <Target className="w-4 h-4 text-indigo-500" />
                      </div>
                      <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                        {result.role_title} {result.company_name ? `@ ${result.company_name}` : ''}
                      </h3>
                      <p className="text-xs font-mono text-indigo-600 dark:text-indigo-400 pt-1">
                        {result.skill_match.score_formula}
                      </p>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="text-center p-3 rounded-xl bg-slate-50 dark:bg-slate-800">
                        <span className="block text-3xl font-black text-indigo-600 dark:text-indigo-400">
                          {result.skill_match.overall_match_score}%
                        </span>
                        <span className="text-[10px] font-bold text-slate-400 uppercase">Match</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Skills Breakdown Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Required Skills Card */}
                  <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      Required Skills ({result.required_skills?.length || 0})
                    </h4>

                    {result.skill_match ? (
                      <div className="space-y-2 text-xs">
                        {result.skill_match.matched_required_skills?.length > 0 && (
                          <div>
                            <span className="text-[10px] font-bold text-emerald-600 block mb-1">
                              Matched ({result.skill_match.matched_required_skills.length}):
                            </span>
                            <div className="flex flex-wrap gap-1">
                              {result.skill_match.matched_required_skills.map((s) => (
                                <span
                                  key={s}
                                  className="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800"
                                >
                                  {s}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {result.skill_match.missing_required_skills?.length > 0 && (
                          <div className="pt-2">
                            <span className="text-[10px] font-bold text-rose-600 block mb-1">
                              Critical Missing ({result.skill_match.missing_required_skills.length}):
                            </span>
                            <div className="flex flex-wrap gap-1">
                              {result.skill_match.missing_required_skills.map((s) => (
                                <span
                                  key={s}
                                  className="px-2 py-0.5 rounded text-[11px] font-medium bg-rose-50 dark:bg-rose-950 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800"
                                >
                                  {s}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {result.required_skills?.map((s) => (
                          <span
                            key={s}
                            className="px-2 py-1 rounded text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Preferred Skills Card */}
                  <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                      <Sparkles className="w-4 h-4 text-violet-500" />
                      Preferred / Bonus Skills ({result.preferred_skills?.length || 0})
                    </h4>

                    {result.skill_match ? (
                      <div className="space-y-2 text-xs">
                        {result.skill_match.matched_preferred_skills?.length > 0 && (
                          <div>
                            <span className="text-[10px] font-bold text-violet-600 block mb-1">
                              Matched ({result.skill_match.matched_preferred_skills.length}):
                            </span>
                            <div className="flex flex-wrap gap-1">
                              {result.skill_match.matched_preferred_skills.map((s) => (
                                <span
                                  key={s}
                                  className="px-2 py-0.5 rounded text-[11px] font-medium bg-violet-50 dark:bg-violet-950 text-violet-700 dark:text-violet-300 border border-violet-200 dark:border-violet-800"
                                >
                                  {s}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {result.skill_match.missing_preferred_skills?.length > 0 && (
                          <div className="pt-2">
                            <span className="text-[10px] font-bold text-slate-400 block mb-1">
                              Nice to Have ({result.skill_match.missing_preferred_skills.length}):
                            </span>
                            <div className="flex flex-wrap gap-1">
                              {result.skill_match.missing_preferred_skills.map((s) => (
                                <span
                                  key={s}
                                  className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                                >
                                  {s}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {result.preferred_skills?.map((s) => (
                          <span
                            key={s}
                            className="px-2 py-1 rounded text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Recommended Learning Topics */}
                {result.recommended_learning_topics?.length > 0 && (
                  <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                      <Lightbulb className="w-4 h-4 text-amber-500" />
                      Recommended Learning Topics
                    </h4>
                    <div className="space-y-1.5 text-xs text-slate-700 dark:text-slate-300">
                      {result.recommended_learning_topics.map((t, idx) => (
                        <div key={idx} className="p-2.5 rounded-xl bg-amber-50/40 dark:bg-amber-950/20 border border-amber-100 dark:border-amber-900/40 flex items-start gap-2">
                          <span className="font-bold text-amber-600">{idx + 1}.</span>
                          <span>{t}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Key Responsibilities */}
                {result.key_responsibilities?.length > 0 && (
                  <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Extracted Key Responsibilities
                    </h4>
                    <ul className="space-y-1 text-xs text-slate-600 dark:text-slate-300 list-disc list-inside">
                      {result.key_responsibilities.map((r, idx) => (
                        <li key={idx}>{r}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-12 text-center space-y-4">
                <Briefcase className="w-12 h-12 text-slate-300 mx-auto" />
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">
                    Paste a Job Posting on the Left
                  </h3>
                  <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
                    Select your resume profile and click Analyze to calculate match scores and identify exact skill gaps.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* History Tab */
        <div className="space-y-4">
          {historyList.length === 0 ? (
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-12 text-center">
              <History className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
                No Previous Job Matches
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                Analyze job descriptions to track match scores over time.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {historyList.map((m) => (
                <div
                  key={m.match_id}
                  className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-2 flex items-center justify-between"
                >
                  <div>
                    <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                      {m.role_title}
                    </h4>
                    <p className="text-xs text-slate-400">
                      {m.company_name || 'Organization'}
                    </p>
                  </div>
                  {m.overall_match_score != null && (
                    <div className="text-right">
                      <span className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
                        {m.overall_match_score}%
                      </span>
                      <span className="text-[10px] block text-slate-400">Skill Match</span>
                    </div>
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
