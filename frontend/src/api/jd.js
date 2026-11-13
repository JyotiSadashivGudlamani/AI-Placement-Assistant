import apiClient from './client';

export const analyzeJobDescription = async ({ jd_text, role_title, company_name, resume_id, candidate_skills }) => {
  const response = await apiClient.post('/jd/analyze', {
    jd_text,
    role_title,
    company_name,
    resume_id,
    candidate_skills,
  });
  return response.data;
};

export const getJDHistory = async (limit = 20) => {
  const response = await apiClient.get(`/jd/history?limit=${limit}`);
  return response.data;
};
