import apiClient from './client';

export const startMockInterview = async ({ interview_type = 'technical', topic = 'Java', difficulty = 'medium', total_questions = 3 }) => {
  const response = await apiClient.post('/mock-interview/start', {
    interview_type,
    topic,
    difficulty,
    total_questions,
  });
  return response.data;
};

export const submitMockAnswer = async (sessionId, studentAnswer) => {
  const response = await apiClient.post(`/mock-interview/${sessionId}/answer`, {
    student_answer: studentAnswer,
  });
  return response.data;
};

export const getMockSession = async (sessionId) => {
  const response = await apiClient.get(`/mock-interview/${sessionId}`);
  return response.data;
};

export const getMockHistory = async (limit = 20) => {
  const response = await apiClient.get(`/mock-interviews/history?limit=${limit}`);
  return response.data;
};
