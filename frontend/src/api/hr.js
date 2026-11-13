import apiClient from './client';

export const getHRCategories = async () => {
  const response = await apiClient.get('/hr/categories');
  return response.data;
};

export const generateHRGuidance = async ({ category, target_company, target_role, student_background }) => {
  const response = await apiClient.post('/hr/generate', {
    category,
    target_company,
    target_role,
    student_background,
  });
  return response.data;
};

export const saveHRDraft = async (draftData) => {
  const response = await apiClient.post('/hr/save', draftData);
  return response.data;
};

export const getSavedHRDrafts = async (category = null) => {
  const url = category ? `/hr/saved?category=${encodeURIComponent(category)}` : '/hr/saved';
  const response = await apiClient.get(url);
  return response.data;
};

export const deleteSavedHRDraft = async (draftId) => {
  const response = await apiClient.delete(`/hr/saved/${draftId}`);
  return response.data;
};
