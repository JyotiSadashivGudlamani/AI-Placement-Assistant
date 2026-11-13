import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';
import DashboardPage from './pages/DashboardPage';
import DocumentsPage from './pages/DocumentsPage';
import ChatPage from './pages/ChatPage';
import SettingsPage from './pages/SettingsPage';
import TechnicalPrepPage from './pages/TechnicalPrepPage';
import HrPrepPage from './pages/HrPrepPage';
import AptitudePage from './pages/AptitudePage';
import ResumeAnalyzerPage from './pages/ResumeAnalyzerPage';
import JdMatcherPage from './pages/JdMatcherPage';
import MockInterviewPage from './pages/MockInterviewPage';
import { getHealthStatus } from './api/health';

function AppLayout() {
  const location = useLocation();
  const [healthInfo, setHealthInfo] = useState(null);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // 30s probe
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const data = await getHealthStatus();
      setHealthInfo(data);
    } catch {
      setHealthInfo({ status: 'unhealthy' });
    }
  };

  const getPageMeta = () => {
    switch (location.pathname) {
      case '/documents':
        return {
          title: 'Document Management',
          subtitle: 'Ingest resumes, syllabus guides, and technical placement resources',
        };
      case '/chat':
        return {
          title: 'AI Placement Chat',
          subtitle: 'Ask technical questions with verified document citations',
        };
      case '/technical':
        return {
          title: 'Technical Interview Prep',
          subtitle: '11 core CS topics with detailed explanations, verified code, and follow-ups',
        };
      case '/hr':
        return {
          title: 'HR & Behavioral Preparation',
          subtitle: 'STAR and Present-Past-Future frameworks without invented achievements',
        };
      case '/aptitude':
        return {
          title: 'Aptitude Practice & Tests',
          subtitle: 'Quantitative, logical reasoning, and verbal tests with time tracking & solutions',
        };
      case '/resume':
        return {
          title: 'Resume Analyser & ATS Health Scanner',
          subtitle: 'Deterministic skill extraction, gap detection, and ATS improvement suggestions',
        };
      case '/jd':
        return {
          title: 'Job Description Matcher',
          subtitle: 'Transparent skill match percentage and targeted placement action plan',
        };
      case '/mock-interview':
        return {
          title: 'Mock Interview Simulator',
          subtitle: 'Turn-by-turn interview simulation evaluated across 5 core criteria',
        };
      case '/settings':
        return {
          title: 'Settings',
          subtitle: 'Configure backend endpoints and user preferences',
        };
      case '/':
      case '/dashboard':
      default:
        return {
          title: 'Placement Dashboard',
          subtitle: 'Overview of your preparation materials and active RAG pipelines',
        };
    }
  };

  const { title, subtitle } = getPageMeta();

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 font-sans transition-colors overflow-hidden">
      {/* Sidebar Navigation */}
      <Sidebar backendConnected={healthInfo?.status === 'healthy'} />

      {/* Main Content Pane */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header title={title} subtitle={subtitle} healthInfo={healthInfo} />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/technical" element={<TechnicalPrepPage />} />
            <Route path="/hr" element={<HrPrepPage />} />
            <Route path="/aptitude" element={<AptitudePage />} />
            <Route path="/resume" element={<ResumeAnalyzerPage />} />
            <Route path="/jd" element={<JdMatcherPage />} />
            <Route path="/mock-interview" element={<MockInterviewPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<DashboardPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <AppLayout />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}
