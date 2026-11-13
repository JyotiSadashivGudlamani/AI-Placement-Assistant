import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  MessageSquare,
  Settings,
  Sparkles,
  GraduationCap,
  Code2,
  Users2,
  BrainCircuit,
  FileCheck,
  Briefcase,
  Bot,
} from 'lucide-react';

const coreNavigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Document Management', href: '/documents', icon: FileText },
  { name: 'AI Placement Chat', href: '/chat', icon: MessageSquare },
];

const placementModules = [
  { name: 'Technical Prep', href: '/technical', icon: Code2 },
  { name: 'HR Preparation', href: '/hr', icon: Users2 },
  { name: 'Aptitude Practice', href: '/aptitude', icon: BrainCircuit },
  { name: 'Resume Analyser', href: '/resume', icon: FileCheck },
  { name: 'JD Matcher', href: '/jd', icon: Briefcase },
  { name: 'Mock Interview', href: '/mock-interview', icon: Bot },
];

export default function Sidebar({ backendConnected = true }) {
  return (
    <aside className="w-64 bg-slate-900 text-white flex flex-col shrink-0 border-r border-slate-800 select-none">
      {/* Brand Header */}
      <div className="h-18 flex items-center px-6 border-b border-slate-800/80 gap-3">
        <div className="p-2 bg-gradient-to-tr from-indigo-600 to-violet-500 rounded-xl shadow-md shadow-indigo-500/20 text-white">
          <GraduationCap className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-base font-bold tracking-tight bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
            Placement AI
          </h1>
          <p className="text-xs text-indigo-400 font-medium">Assistant v2.0</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-4 overflow-y-auto">
        <div>
          <p className="px-3 text-[11px] font-semibold tracking-wider text-slate-400 uppercase mb-1.5">
            Core Platform
          </p>
          <div className="space-y-1">
            {coreNavigation.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.name}
                  to={item.href}
                  end={item.href === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3.5 py-2 rounded-xl text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                        : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </div>
        </div>

        <div>
          <p className="px-3 text-[11px] font-semibold tracking-wider text-slate-400 uppercase mb-1.5">
            Placement Prep
          </p>
          <div className="space-y-1">
            {placementModules.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.name}
                  to={item.href}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3.5 py-2 rounded-xl text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                        : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </div>
        </div>

        <div>
          <p className="px-3 text-[11px] font-semibold tracking-wider text-slate-400 uppercase mb-1.5">
            Configuration
          </p>
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `flex items-center gap-3 px-3.5 py-2 rounded-xl text-xs font-medium transition-all ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
              }`
            }
          >
            <Settings className="w-4 h-4 shrink-0" />
            <span>Settings</span>
          </NavLink>
        </div>
      </nav>

      {/* RAG Engine Status Card */}
      <div className="p-4 mx-3 mb-4 rounded-xl bg-slate-800/60 border border-slate-700/50">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-200">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <span>RAG Engine</span>
          </div>
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              backendConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
            }`}
            title={backendConnected ? 'Backend Connected' : 'Backend Disconnected'}
          />
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          Powered by ChromaDB, Sentence Transformers & Llama 3.2:3b.
        </p>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-500">
        <span>AI Placement Assistant</span>
        <span>2026</span>
      </div>
    </aside>
  );
}
