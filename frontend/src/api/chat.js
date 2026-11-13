import apiClient from './client';

export const sendChatMessage = async ({
  question,
  sessionId = null,
  topK = 4,
  category = null,
  documentId = null,
  retrievalMode = 'hybrid_rerank',
}) => {
  const payload = {
    question: question.trim(),
    session_id: sessionId,
    top_k: topK,
    category,
    document_id: documentId,
    retrieval_mode: retrievalMode,
  };
  const response = await apiClient.post('/chat', payload);
  return response.data;
};

export const getChatSessions = async (limit = 20) => {
  const response = await apiClient.get('/chats', { params: { limit } });
  return response.data;
};

export const getSessionHistory = async (sessionId) => {
  const response = await apiClient.get(`/chats/${sessionId}`);
  return response.data;
};

export const deleteChatSession = async (sessionId) => {
  const response = await apiClient.delete(`/chats/${sessionId}`);
  return response.data;
};
