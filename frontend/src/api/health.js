import apiClient from './client';

export const getHealthStatus = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

export const getRootInfo = async () => {
  const response = await apiClient.get('/');
  return response.data;
};
