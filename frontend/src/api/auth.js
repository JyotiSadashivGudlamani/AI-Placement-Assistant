import apiClient from './client';

/**
 * Registers a new student account.
 */
export const registerUser = async ({ email, password, fullName }) => {
  const response = await apiClient.post('/auth/register', {
    email: email.trim(),
    password,
    full_name: fullName.trim(),
  });
  return response.data;
};

/**
 * Authenticates user credentials and returns JWT Bearer token.
 */
export const loginUser = async ({ email, password }) => {
  const response = await apiClient.post('/auth/login', {
    email: email.trim(),
    password,
  });
  return response.data;
};

/**
 * Retrieves the currently authenticated user's profile.
 */
export const getCurrentUser = async () => {
  const response = await apiClient.get('/auth/me');
  return response.data;
};

/**
 * Logs out the current session.
 */
export const logoutUser = async () => {
  const response = await apiClient.post('/auth/logout');
  return response.data;
};
