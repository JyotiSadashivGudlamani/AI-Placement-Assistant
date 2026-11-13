import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  MessageSquare,
  Cpu,
  Brain,
  Video,
  Sparkles,
  ArrowRight,
  TrendingUp,
  Target,
  Award,
  CheckCircle2,
  Clock,
  Compass,
  Zap,
} from 'lucide-react';
import { getDashboardAnalytics } from '../api/analytics';
import { getHealthStatus } from '../api/health';
import { useAuth } from '../context/AuthContext';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function DashboardPage() {
  const { user, isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState(null);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetchData();
  }, [isAuthenticated]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [analyticsData, healthData] = await Promise.allSettled([
        getDashboardAnalytics(),
        getHealthStatus(),
      ]);

      if (analyticsData.status === 'fulfilled') {
        setAnalytics(analyticsData.value);
      }
      if (healthData.status === 'fulfilled') {
        setHealth(healthData.value);
      }
    } catch (err) {
      console.error('Failed to load dashboard analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading placement dashboard & student analytics..." size="lg" />;
  }

  const aptStats = analytics?.aptitude_stats || { total_tests: 0, average_score: 0, best_score: 0, categories: {} };
  const mockStats = analytics?.mock_interview_stats || { total_interviews: 0, average_overall: 0, criteria_averages: {} };
  const recentActivity = analytics?.recent_activity || [];
  const topicProgress = analytics?.topic_wise_progress || [];
  const recommendations = analytics?.recommended_next_topics || [];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Welcome Hero */}
      <div className="bg-gradient-to-r from-indigo-900 via-slate-900 to-slate-900 rounded-3xl p-8 text-white relative overflow-hidden border border-indigo-950 shadow-lg">
        <div className="relative z-10 max-w-2xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-400/30">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Placement Readiness Platform • Phase 7 Analytics</span>
          </div>
          <h2 className="text-3xl font-extrabold tracking-tight">
            {isAuthenticated ? `Welcome back, ${user.full_name}!` : 'Prepare for Campus Placements with Agentic AI'}
          </h2>
          <p className="text-sm text-slate-300 leading-relaxed">
            Track your personalized preparation progress, practice mock interviews evaluated on 5 core criteria,
            and review grounded document citations using Llama 3.2:3b and ChromaDB.
          </p>
          <div className="pt-2 flex flex-wrap gap-3">
            <Link
              to="/chat"
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-all shadow-md shadow-indigo-600/30 inline-flex items-center gap-2 cursor-pointer"
            >
              Start AI Agent Chat <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/documents"
              className="px-5 py-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 transition-all inline-flex items-center gap-2 cursor-pointer"
            >
              Upload Syllabus & Notes
            </Link>
          </div>
        </div>
      </div>

      {/* Top 4 Core Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Uploaded Documents */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs flex items-center gap-4">
          <div className="p-3.5 rounded-2xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 shrink-0">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">Indexed Documents</p>
            <h4 className="text-2xl font-extrabold text-slate-900 dark:text-white mt-0.5">
              {analytics?.total_uploaded_documents || 0}
            </h4>
            <span className="text-[11px] text-slate-400">Ownership isolated</span>
          </div>
        </div>

        {/* Questions Asked */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs flex items-center gap-4">
          <div className="p-3.5 rounded-2xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 shrink-0">
            <MessageSquare className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">Questions Solved</p>
            <h4 className="text-2xl font-extrabold text-slate-900 dark:text-white mt-0.5">
              {analytics?.total_questions_asked || 0}
            </h4>
            <span className="text-[11px] text-slate-400">RAG & Agent Turns</span>
          </div>
        </div>

        {/* Technical Questions */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs flex items-center gap-4">
          <div className="p-3.5 rounded-2xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 shrink-0">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">Technical Prep Items</p>
            <h4 className="text-2xl font-extrabold text-slate-900 dark:text-white mt-0.5">
              {analytics?.technical_prep_count || 0}
            </h4>
            <span className="text-[11px] text-slate-400">11 CS Core Topics</span>
          </div>
        </div>

        {/* Aptitude Average */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs flex items-center gap-4">
          <div className="p-3.5 rounded-2xl bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 shrink-0">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">Aptitude Avg Score</p>
            <h4 className="text-2xl font-extrabold text-slate-900 dark:text-white mt-0.5">
              {aptStats.average_score}%
            </h4>
            <span className="text-[11px] text-slate-400">
              {aptStats.total_tests} test{aptStats.total_tests === 1 ? '' : 's'} taken
            </span>
          </div>
        </div>
      </div>

      {/* Two Column Layout: Aptitude & Mock Interview Deep Dive */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Aptitude Practice Metrics */}
        <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Brain className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Aptitude Readiness</h3>
            </div>
            <Link
              to="/aptitude"
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-500 inline-flex items-center gap-1"
            >
              Practice Tests <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-3 gap-3 text-center py-2 bg-slate-50 dark:bg-slate-800/40 rounded-2xl p-3 border border-slate-100 dark:border-slate-800">
            <div>
              <p className="text-[11px] text-slate-400">Total Attempts</p>
              <p className="text-lg font-bold text-slate-800 dark:text-slate-100">{aptStats.total_tests}</p>
            </div>
            <div>
              <p className="text-[11px] text-slate-400">Average Score</p>
              <p className="text-lg font-bold text-indigo-600 dark:text-indigo-400">{aptStats.average_score}%</p>
            </div>
            <div>
              <p className="text-[11px] text-slate-400">Best Score</p>
              <p className="text-lg font-bold text-emerald-600 dark:text-emerald-400">{aptStats.best_score}%</p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-semibold text-slate-700 dark:text-slate-300">
                <span>Quantitative Aptitude</span>
                <span>{aptStats.categories?.quantitative || 0}%</span>
              </div>
              <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-indigo-600 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, aptStats.categories?.quantitative || 0)}%` }}
                />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-xs font-semibold text-slate-700 dark:text-slate-300">
                <span>Logical Reasoning</span>
                <span>{aptStats.categories?.logical || 0}%</span>
              </div>
              <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, aptStats.categories?.logical || 0)}%` }}
                />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-xs font-semibold text-slate-700 dark:text-slate-300">
                <span>Verbal Ability</span>
                <span>{aptStats.categories?.verbal || 0}%</span>
              </div>
              <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-amber-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, aptStats.categories?.verbal || 0)}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Mock Interview Evaluation Metrics */}
        <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Video className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Mock Interview Rubric Scores</h3>
            </div>
            <Link
              to="/mock-interview"
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-500 inline-flex items-center gap-1"
            >
              Start Simulator <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="flex items-center justify-between p-4 bg-indigo-50/60 dark:bg-indigo-950/40 rounded-2xl border border-indigo-100 dark:border-indigo-900/50">
            <div>
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">Overall Interview Rating</p>
              <h4 className="text-3xl font-extrabold text-indigo-600 dark:text-indigo-400 mt-0.5">
                {mockStats.average_overall} <span className="text-sm font-medium text-slate-400">/ 10</span>
              </h4>
            </div>
            <div className="text-right text-xs text-slate-500">
              <p className="font-semibold text-slate-700 dark:text-slate-300">{mockStats.total_interviews} Completed Sessions</p>
              <p className="text-[11px] text-slate-400 mt-0.5">Scored across 5 criteria</p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
            {Object.entries(mockStats.criteria_averages || {}).map(([criteria, score]) => (
              <div
                key={criteria}
                className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 text-center"
              >
                <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 capitalize">{criteria}</p>
                <p className="text-base font-bold text-slate-800 dark:text-slate-100 mt-0.5">{score} / 10</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recommended Next Topics Section */}
      <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Compass className="w-5 h-5 text-indigo-600" />
            <h3 className="text-base font-bold text-slate-900 dark:text-white">Recommended Next Learning Steps</h3>
          </div>
          <span className="text-xs text-slate-400">AI-driven prioritization</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {recommendations.map((rec, idx) => (
            <div
              key={idx}
              className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 flex flex-col justify-between space-y-3"
            >
              <div>
                <span className="inline-block px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 mb-2">
                  {rec.badge}
                </span>
                <h4 className="text-xs font-bold text-slate-800 dark:text-slate-100 leading-snug">
                  {rec.title}
                </h4>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                  {rec.reason}
                </p>
              </div>
              <Link
                to={rec.action_url}
                className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-700 pt-1 cursor-pointer"
              >
                Start Practice <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          ))}
        </div>
      </div>

      {/* Two Column Layout: Topic-Wise Progress & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Topic-Wise Progress (2 Cols) */}
        <div className="lg:col-span-2 p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Target className="w-5 h-5 text-indigo-600" />
              <h3 className="text-base font-bold text-slate-900 dark:text-white">CS Fundamentals Readiness</h3>
            </div>
            <Link
              to="/technical"
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-500 inline-flex items-center gap-1"
            >
              All 11 Topics <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-4">
            {topicProgress.map((item, idx) => (
              <div key={idx} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <div>
                    <span className="font-bold text-slate-800 dark:text-slate-200">{item.topic}</span>
                    <span className="text-slate-400 ml-2 text-[11px]">{item.description}</span>
                  </div>
                  <span className="font-bold text-indigo-600 dark:text-indigo-400">
                    {item.mastery_percentage}%
                  </span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-indigo-500 to-indigo-700 h-full rounded-full transition-all duration-500"
                    style={{ width: `${item.mastery_percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity Timeline (1 Col) */}
        <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-5">
          <div className="flex items-center gap-2.5">
            <Clock className="w-5 h-5 text-indigo-600" />
            <h3 className="text-base font-bold text-slate-900 dark:text-white">Recent Activity</h3>
          </div>

          {recentActivity.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-xs">
              <Clock className="w-6 h-6 mx-auto mb-2 opacity-40" />
              <p>No recent activity recorded yet.</p>
              <p className="text-[11px] text-slate-500 mt-1">Upload a document or take a test to start!</p>
            </div>
          ) : (
            <div className="space-y-3.5">
              {recentActivity.map((act, i) => (
                <div key={i} className="flex items-start gap-3 text-xs">
                  <div className="w-2 h-2 rounded-full bg-indigo-500 mt-1.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-slate-800 dark:text-slate-200 truncate">{act.title}</p>
                    <p className="text-[11px] text-slate-400 truncate">{act.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
