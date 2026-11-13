import apiClient from './client';

export const analyzeResume = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post('/resume/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getResumeById = async (resumeId) => {
  const response = await apiClient.get(`/resume/${resumeId}`);
  return response.data;
};

export const listResumes = async () => {
  const response = await apiClient.get('/resumes/all');
  return response.data;
};
