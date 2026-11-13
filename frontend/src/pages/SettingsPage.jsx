import React, { useState } from 'react';
import {
  Settings,
  Server,
  Database,
  Moon,
  Sun,
  CheckCircle2,
  AlertCircle,
  Save,
  RotateCcw,
} from 'lucide-react';
import { getApiBaseUrl } from '../api/client';
import { getHealthStatus } from '../api/health';
import { useTheme } from '../context/ThemeContext';
import ErrorAlert from '../components/common/ErrorAlert';

export default function SettingsPage() {
  const { theme, toggleTheme } = useTheme();
  const [apiUrl, setApiUrl] = useState(getApiBaseUrl());
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState(null);

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    setError(null);
    try {
      const data = await getHealthStatus();
      setTestResult(data);
    } catch (err) {
      setError(`Connection failed: ${err.message}`);
    } finally {
      setTesting(false);
    }
  };

  const handleSaveApiUrl = () => {
    try {
      const cleanUrl = apiUrl.trim().replace(/\/+$/, '');
      localStorage.setItem('custom_api_url', cleanUrl);
      setApiUrl(cleanUrl);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleResetDefaults = () => {
    localStorage.removeItem('custom_api_url');
    setApiUrl(import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000');
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8">
      <div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">System Settings</h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Configure API endpoints, verify backend connectivity, and manage preferences.
        </p>
      </div>

      <ErrorAlert message={error} onDismiss={() => setError(null)} />

      {saveSuccess && (
        <div className="flex items-center gap-2 p-3 text-xs text-emerald-800 bg-emerald-50 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 rounded-xl">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span>Settings saved successfully.</span>
        </div>
      )}

      {/* Backend API Configuration */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs space-y-4">
        <div className="flex items-center gap-2.5">
          <Server className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">FastAPI Backend Endpoint</h3>
        </div>

        <p className="text-xs text-slate-500 dark:text-slate-400">
          The base URL of your FastAPI backend service.
        </p>

        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="url"
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            placeholder="http://127.0.0.1:8000"
            className="flex-1 px-4 py-2.5 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white font-mono focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
          />
          <button
            onClick={handleSaveApiUrl}
            className="px-4 py-2.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 transition-colors inline-flex items-center justify-center gap-1.5 cursor-pointer"
          >
            <Save className="w-4 h-4" /> Save
          </button>
          <button
            onClick={handleTestConnection}
            disabled={testing}
            className="px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors inline-flex items-center justify-center gap-1.5 cursor-pointer"
          >
            {testing ? 'Testing...' : 'Test Connection'}
          </button>
        </div>

        {testResult && (
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs space-y-2">
            <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-semibold">
              <CheckCircle2 className="w-4 h-4" /> Connected to FastAPI (Status: {testResult.status})
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-500 dark:text-slate-400 font-mono">
              <div>ChromaDB: {testResult.components?.chromadb?.status || 'Active'}</div>
              <div>Ollama Model: {testResult.components?.ollama?.target_model || 'llama3.2:3b'}</div>
              <div>Embeddings: {testResult.components?.embeddings?.model || 'all-MiniLM-L6-v2'}</div>
              <div>MongoDB: {testResult.components?.mongodb?.status || 'Active'}</div>
            </div>
          </div>
        )}
      </div>

      {/* Model Information */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs space-y-4">
        <div className="flex items-center gap-2.5">
          <Database className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">Active AI Architecture</h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60">
            <span className="text-slate-400 block text-[10px] uppercase font-semibold">Embedding Model</span>
            <span className="font-bold text-slate-800 dark:text-slate-200">all-MiniLM-L6-v2</span>
            <p className="text-[11px] text-slate-500 mt-0.5">384 dimensions · SentenceTransformers</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60">
            <span className="text-slate-400 block text-[10px] uppercase font-semibold">LLM Inference</span>
            <span className="font-bold text-slate-800 dark:text-slate-200">Llama 3.2:3b</span>
            <p className="text-[11px] text-slate-500 mt-0.5">Local Ollama daemon · 128k context</p>
          </div>
        </div>
      </div>

      {/* Theme Preference */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">Appearance</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">Toggle between Light and Dark interface modes.</p>
        </div>

        <button
          onClick={toggleTheme}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors cursor-pointer"
        >
          {theme === 'light' ? (
            <>
              <Moon className="w-4 h-4" /> Dark Mode
            </>
          ) : (
            <>
              <Sun className="w-4 h-4" /> Light Mode
            </>
          )}
        </button>
      </div>

      {/* Reset */}
      <div className="pt-2 flex justify-end">
        <button
          onClick={handleResetDefaults}
          className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-colors cursor-pointer"
        >
          <RotateCcw className="w-3.5 h-3.5" /> Reset Default Settings
        </button>
      </div>
    </div>
  );
}
