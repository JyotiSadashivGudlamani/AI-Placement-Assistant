import React, { useState, useEffect } from 'react';
import {
  FileText,
  Upload,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  Globe,
  Link2,
  Mail,
  Phone,
  GraduationCap,
  FolderGit2,
  Sparkles,
  RefreshCw,
  FileCheck,
} from 'lucide-react';
import { analyzeResume, listResumes, getResumeById } from '../api/resume';

export default function ResumeAnalyzerPage() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [recentResumes, setRecentResumes] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadRecentResumes();
  }, []);

  const loadRecentResumes = async () => {
    try {
      const data = await listResumes();
      setRecentResumes(data.resumes || []);
      if (data.resumes?.length > 0 && !analysis) {
        // Load the most recent one automatically
        loadResume(data.resumes[0].resume_id);
      }
    } catch {
      // Ignore
    }
  };

  const loadResume = async (resumeId) => {
    setLoading(true);
    try {
      const profile = await getResumeById(resumeId);
      setAnalysis(profile);
    } catch {
      // Ignore
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
      handleUpload(selected);
    }
  };

  const handleUpload = async (fileToUpload = file) => {
    if (!fileToUpload) return;
    setLoading(true);
    setError(null);
    try {
      const result = await analyzeResume(fileToUpload);
      setAnalysis(result);
      loadRecentResumes();
    } catch (err) {
      setError(err.message || 'Failed to analyze resume.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2.5">
            <FileText className="w-7 h-7 text-indigo-600 dark:text-indigo-400" />
            Resume Analyser & ATS Health Scanner
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Extract verified technical skills, education, and projects from PDF/DOCX with zero hallucination.
          </p>
        </div>

        {/* Upload Button */}
        <label className="cursor-pointer px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-md shadow-indigo-600/20 inline-flex items-center gap-2 transition-all self-start">
          <Upload className="w-4 h-4" />
          <span>Upload New Resume</span>
          <input
            type="file"
            accept=".pdf,.docx"
            onChange={handleFileChange}
            className="hidden"
          />
        </label>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs">
          {error}
        </div>
      )}

      {loading && (
        <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
          <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto mb-3" />
          <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
            Parsing Resume Sections & Performing ATS Audit...
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Extracting skills, projects, and contact info deterministically.
          </p>
        </div>
      )}

      {!loading && analysis && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Candidate Overview & Skills */}
          <div className="lg:col-span-1 space-y-5">
            {/* Candidate Card */}
            <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white flex items-center justify-center font-bold text-lg shadow-md shadow-indigo-500/20">
                  {analysis.contact_info?.name
                    ? analysis.contact_info.name.charAt(0)
                    : 'C'}
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900 dark:text-white">
                    {analysis.contact_info?.name || 'Candidate Profile'}
                  </h2>
                  <p className="text-xs text-slate-400">{analysis.filename}</p>
                </div>
              </div>

              {/* Contact Information */}
              <div className="space-y-2 text-xs pt-2 border-t border-slate-100 dark:border-slate-800">
                {analysis.contact_info?.email && (
                  <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
                    <Mail className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                    <span className="truncate">{analysis.contact_info.email}</span>
                  </div>
                )}
                {analysis.contact_info?.phone && (
                  <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
                    <Phone className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                    <span>{analysis.contact_info.phone}</span>
                  </div>
                )}
                {analysis.contact_info?.github && (
                  <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
                    <Globe className="w-3.5 h-3.5 text-slate-700 dark:text-slate-300 shrink-0" />
                    <span className="truncate">{analysis.contact_info.github}</span>
                  </div>
                )}
                {analysis.contact_info?.linkedin && (
                  <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
                    <Link2 className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                    <span className="truncate">{analysis.contact_info.linkedin}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Extracted Skills Inventory */}
            <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Verified Technical Skills
                </h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
                  {analysis.skills?.all_skills?.length || 0} Skills
                </span>
              </div>

              <div className="space-y-3">
                {analysis.skills?.languages?.length > 0 && (
                  <div>
                    <span className="text-[11px] font-semibold text-slate-500 block mb-1.5">
                      Languages:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {analysis.skills.languages.map((s) => (
                        <span
                          key={s}
                          className="px-2.5 py-1 rounded-lg text-xs font-medium bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {analysis.skills?.frameworks_and_libraries?.length > 0 && (
                  <div>
                    <span className="text-[11px] font-semibold text-slate-500 block mb-1.5">
                      Frameworks & Libs:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {analysis.skills.frameworks_and_libraries.map((s) => (
                        <span
                          key={s}
                          className="px-2.5 py-1 rounded-lg text-xs font-medium bg-violet-50 dark:bg-violet-950/60 text-violet-700 dark:text-violet-300 border border-violet-200 dark:border-violet-800"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {analysis.skills?.databases?.length > 0 && (
                  <div>
                    <span className="text-[11px] font-semibold text-slate-500 block mb-1.5">
                      Databases:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {analysis.skills.databases.map((s) => (
                        <span
                          key={s}
                          className="px-2.5 py-1 rounded-lg text-xs font-medium bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {analysis.skills?.tools_and_platforms?.length > 0 && (
                  <div>
                    <span className="text-[11px] font-semibold text-slate-500 block mb-1.5">
                      Tools & Cloud:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {analysis.skills.tools_and_platforms.map((s) => (
                        <span
                          key={s}
                          className="px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Previously Analyzed Resumes Selector */}
            {recentResumes.length > 1 && (
              <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
                  Switch Resume Profile
                </span>
                <div className="space-y-1">
                  {recentResumes.map((r) => (
                    <button
                      key={r.resume_id}
                      onClick={() => loadResume(r.resume_id)}
                      className={`w-full text-left px-3 py-1.5 rounded-lg text-xs flex items-center justify-between ${
                        analysis.resume_id === r.resume_id
                          ? 'bg-indigo-50 dark:bg-indigo-950 text-indigo-600 font-bold'
                          : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50'
                      }`}
                    >
                      <span className="truncate">{r.filename}</span>
                      <span className="text-[10px] text-slate-400">{r.skills_count} skills</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Health Audit, Education, Projects */}
          <div className="lg:col-span-2 space-y-5">
            {/* Strengths Audit */}
            <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                Resume Strengths & Confirmed Assets
              </h3>
              <div className="space-y-2">
                {analysis.strengths?.map((str, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200/60 dark:border-emerald-900/40 text-xs text-emerald-800 dark:text-emerald-300 flex items-start gap-2.5"
                  >
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                    <span>{str}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Missing Information Gaps */}
            {analysis.missing_information?.length > 0 && (
              <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  Identified Gaps & Missing Information
                </h3>
                <div className="space-y-2">
                  {analysis.missing_information.map((gap, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40 text-xs text-amber-800 dark:text-amber-300 flex items-start gap-2.5"
                    >
                      <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                      <span>{gap}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actionable Improvement Suggestions */}
            {analysis.improvement_suggestions?.length > 0 && (
              <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Lightbulb className="w-4 h-4 text-indigo-500" />
                  Actionable ATS Improvement Suggestions
                </h3>
                <div className="space-y-2">
                  {analysis.improvement_suggestions.map((sug, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-indigo-50/40 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/40 text-xs text-slate-700 dark:text-slate-300 flex items-start gap-2.5"
                    >
                      <Sparkles className="w-4 h-4 text-indigo-500 shrink-0 mt-0.5" />
                      <span>{sug}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Projects & Internships Extracted */}
            {analysis.projects?.length > 0 && (
              <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <FolderGit2 className="w-4 h-4 text-indigo-500" />
                  Detected Projects & Key Systems
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {analysis.projects.map((proj, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 space-y-2"
                    >
                      <h4 className="text-xs font-bold text-slate-900 dark:text-white">
                        {proj.title}
                      </h4>
                      {proj.technologies?.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {proj.technologies.map((t) => (
                            <span
                              key={t}
                              className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300"
                            >
                              {t}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {!loading && !analysis && (
        <div className="p-16 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 space-y-4">
          <FileText className="w-12 h-12 text-slate-300 mx-auto" />
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              No Resume Uploaded Yet
            </h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
              Upload your PDF or DOCX resume to extract skills, detect missing information, and optimize for campus placement ATS screeners.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
