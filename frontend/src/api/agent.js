import apiClient from './client';

/**
 * Sends a student query to the LangGraph Agentic Assistant.
 * The backend StateGraph intelligently classifies intent, routes to the appropriate tool,
 * executes the tool, and returns the grounded answer with citations and execution trace.
 */
export const sendAgentMessage = async ({
  message,
  sessionId = null,
  userId = null,
  context = null,
}) => {
  const payload = {
    message: message.trim(),
    session_id: sessionId,
    user_id: userId,
    context: context,
  };
  const response = await apiClient.post('/agent/chat', payload);
  return response.data;
};

/**
 * Retrieves the list of past LangGraph agent sessions.
 */
export const getAgentSessions = async (limit = 20) => {
  const response = await apiClient.get('/agent/sessions', { params: { limit } });
  return response.data;
};

/**
 * Retrieves the turn history and state transitions for a specific agent session.
 */
export const getAgentSessionDetail = async (sessionId) => {
  const response = await apiClient.get(`/agent/session/${sessionId}`);
  return response.data;
};

/**
 * Retrieves the LangGraph workflow topology, registered nodes, and tools.
 */
export const getAgentWorkflow = async () => {
  const response = await apiClient.get('/agent/workflow');
  return response.data;
};
