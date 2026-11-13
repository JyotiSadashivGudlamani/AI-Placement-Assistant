import React, { useEffect, useState, useRef } from 'react';
import {
  MessageSquare,
  Plus,
  Trash2,
  Sparkles,
  Bot,
  BookOpen,
} from 'lucide-react';
import {
  sendChatMessage,
  getChatSessions,
  getSessionHistory,
  deleteChatSession,
} from '../api/chat';
import { sendAgentMessage } from '../api/agent';
import ChatBubble from '../components/chat/ChatBubble';
import ChatInput from '../components/chat/ChatInput';
import ErrorAlert from '../components/common/ErrorAlert';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function ChatPage() {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        'Hello! I am your **LangGraph AI Placement Preparation Assistant**.\n\n' +
        'I automatically classify and route your preparation requests across:\n' +
        '• **Document RAG:** Concepts from your uploaded syllabus and PDFs\n' +
        '• **Resume Analysis:** Skills audit and ATS gap analysis\n' +
        '• **Job Description:** Role matching and required qualification review\n' +
        '• **Technical Prep:** Coding questions and OOP/DSA problems with examples\n' +
        '• **HR Guidance:** Behavioral STAR framework and interview answers\n' +
        '• **Aptitude Practice:** Quantitative, logical, and verbal practice\n' +
        '• **Answer Evaluation:** Multi-criteria grading and feedback on your practice answers',
      citations: [],
      suggestedActions: [
        'Ask me a Java interview question with code',
        'Analyze my resume for backend engineer skills',
        'Help me answer: Why should we hire you?',
        'Give me a quantitative aptitude puzzle',
      ],
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const fetchSessions = async () => {
    try {
      const data = await getChatSessions(15);
      setSessions(data.sessions || []);
    } catch (err) {
      console.warn('Sessions unavailable:', err.message);
    }
  };

  const startNewSession = () => {
    setCurrentSessionId(null);
    setMessages([
      {
        role: 'assistant',
        content:
          'Starting a new preparation session. What technical placement topic would you like to explore?',
        citations: [],
        suggestedActions: [
          'Give me a Java interview question on inheritance',
          'Review my uploaded resume skills',
          'Practice quantitative aptitude',
        ],
      },
    ]);
  };

  const switchSession = async (sessionId) => {
    setCurrentSessionId(sessionId);
    setError(null);
    try {
      const historyData = await getSessionHistory(sessionId);
      if (historyData.messages && historyData.messages.length > 0) {
        setMessages(historyData.messages);
      }
    } catch (err) {
      setError(`Failed to load session history: ${err.message}`);
    }
  };

  const handleDeleteSession = async (e, sessionId) => {
    e.stopPropagation();
    try {
      await deleteChatSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
      if (currentSessionId === sessionId) {
        startNewSession();
      }
    } catch (err) {
      setError(`Failed to delete session: ${err.message}`);
    }
  };

  const handleSendMessage = async ({ question, topK, category, retrievalMode }) => {
    setError(null);

    // Append user message immediately
    const userMsg = { role: 'user', content: question };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      if (retrievalMode === 'agent') {
        // Phase 6: LangGraph Intelligent Multi-Tool Routing
        const response = await sendAgentMessage({
          message: question,
          sessionId: currentSessionId,
          userId: 'student_user',
        });

        if (response.session_id && !currentSessionId) {
          setCurrentSessionId(response.session_id);
        }

        const assistantMsg = {
          role: 'assistant',
          content: response.response,
          citations: response.citations || [],
          toolUsed: response.tool_used,
          intent: response.intent,
          intentConfidence: response.intent_confidence,
          executionPath: response.execution_path || [],
          suggestedActions: response.suggested_actions || [],
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } else {
        // Standard Document RAG Chat
        const response = await sendChatMessage({
          question,
          sessionId: currentSessionId,
          topK,
          category,
          retrievalMode,
        });

        if (response.session_id && !currentSessionId) {
          setCurrentSessionId(response.session_id);
        }

        const assistantMsg = {
          role: 'assistant',
          content: response.answer,
          citations: response.citations || [],
          retrievalMode: response.retrieval_mode || retrievalMode,
        };
        setMessages((prev) => [...prev, assistantMsg]);
      }
      fetchSessions();
    } catch (err) {
      setError(err.message);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            'Sorry, I encountered an issue communicating with the backend. Please verify FastAPI and Ollama are running.',
          citations: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleActionClick = (actionText) => {
    handleSendMessage({
      question: actionText,
      topK: 4,
      category: null,
      retrievalMode: 'agent',
    });
  };

  return (
    <div className="flex-1 flex overflow-hidden bg-slate-50 dark:bg-slate-950 transition-colors">
      {/* Sessions Sidebar */}
      <aside className="w-64 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hidden md:flex flex-col shrink-0">
        <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <span className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
            History
          </span>
          <button
            onClick={startNewSession}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 cursor-pointer transition-colors"
            title="Start new practice chat session"
          >
            <Plus className="w-3.5 h-3.5" /> New
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1.5 text-xs">
          {sessions.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              <MessageSquare className="w-6 h-6 mx-auto mb-2 opacity-40" />
              <p>No recent sessions</p>
            </div>
          ) : (
            sessions.map((s) => (
              <div
                key={s.session_id}
                onClick={() => switchSession(s.session_id)}
                className={`group flex items-center justify-between p-2.5 rounded-xl cursor-pointer transition-all ${
                  currentSessionId === s.session_id
                    ? 'bg-indigo-50 dark:bg-indigo-950/70 text-indigo-700 dark:text-indigo-300 font-semibold'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <MessageSquare className="w-3.5 h-3.5 shrink-0" />
                  <span className="truncate">{s.last_question || 'Placement Chat'}</span>
                </div>
                <button
                  onClick={(e) => handleDeleteSession(e, s.session_id)}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:text-rose-500 rounded transition-all cursor-pointer"
                  title="Delete chat session"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))
          )}
        </div>
      </aside>

      {/* Main Chat Interface */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Messages Feed */}
        <div className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="max-w-4xl mx-auto">
            <ErrorAlert message={error} onDismiss={() => setError(null)} />

            {messages.map((message, index) => (
              <ChatBubble key={index} message={message} onActionClick={handleActionClick} />
            ))}

            {loading && (
              <div className="flex items-center gap-3 mb-6">
                <div className="w-9 h-9 rounded-2xl bg-indigo-900 text-indigo-400 flex items-center justify-center shrink-0 animate-pulse">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div className="px-5 py-3 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs font-medium text-slate-500 dark:text-slate-400 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-indigo-600 animate-ping" />
                  LangGraph classifying intent & orchestrating specialized tools with Llama 3.2:3b...
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Bar */}
        <ChatInput onSendMessage={handleSendMessage} loading={loading} />
      </div>
    </div>
  );
}
