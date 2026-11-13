import apiClient from './client';

export const getTechnicalTopics = async () => {
  const response = await apiClient.get('/technical/topics');
  return response.data;
};

export const generateTechnicalQuestion = async ({ topic, difficulty = 'medium', subtopic = null, include_code = true }) => {
  const response = await apiClient.post('/technical/generate', {
    topic,
    difficulty,
    subtopic,
    include_code,
  });
  return response.data;
};

export const saveTechnicalQuestion = async (questionData) => {
  const response = await apiClient.post('/technical/save', questionData);
  return response.data;
};

export const getSavedTechnicalQuestions = async (topic = null) => {
  const url = topic ? `/technical/saved?topic=${encodeURIComponent(topic)}` : '/technical/saved';
  const response = await apiClient.get(url);
  return response.data;
};

export const deleteSavedTechnicalQuestion = async (questionId) => {
  const response = await apiClient.delete(`/technical/saved/${questionId}`);
  return response.data;
};
