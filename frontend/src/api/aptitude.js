import apiClient from './client';

export const getAptitudeCategories = async () => {
  const response = await apiClient.get('/aptitude/categories');
  return response.data;
};

export const generateAptitudeQuiz = async ({ category = 'all', count = 5, difficulty = 'medium' }) => {
  const response = await apiClient.post('/aptitude/quiz/generate', {
    category,
    count,
    difficulty,
  });
  return response.data;
};

export const submitAptitudeQuiz = async ({ category, answers, time_taken_seconds }) => {
  const response = await apiClient.post('/aptitude/quiz/submit', {
    category,
    answers,
    time_taken_seconds,
  });
  return response.data;
};

export const getAptitudeHistory = async (limit = 20) => {
  const response = await apiClient.get(`/aptitude/history?limit=${limit}`);
  return response.data;
};
