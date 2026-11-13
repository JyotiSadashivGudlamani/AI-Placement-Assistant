import apiClient from './client';

/**
 * Retrieves personalized student placement preparation analytics.
 */
export const getDashboardAnalytics = async () => {
  const response = await apiClient.get('/analytics/dashboard');
  return response.data;
};
