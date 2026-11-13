import axios from 'axios';

export const getApiBaseUrl = () => {
  return localStorage.getItem('custom_api_url') || import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
};

const apiClient = axios.create({
  timeout: 120000, // 120s to allow local LLM inference
});

// Dynamic baseURL & JWT Bearer token interceptor
apiClient.interceptors.request.use((config) => {
  config.baseURL = getApiBaseUrl();
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for structured error messages
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let message = 'An unexpected error occurred.';
    if (error.response?.data?.detail) {
      message = error.response.data.detail;
    } else if (error.message) {
      message = error.message;
    }
    return Promise.reject(new Error(message));
  }
);

export default apiClient;
