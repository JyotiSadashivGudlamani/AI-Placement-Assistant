import apiClient from './client';

export const uploadDocument = async (file, category = 'placement', onUploadProgress = null) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', category);

  const response = await apiClient.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onUploadProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onUploadProgress(percent);
      }
    },
  });
  return response.data;
};

export const getDocuments = async (category = null) => {
  const params = category ? { category } : {};
  const response = await apiClient.get('/documents', { params });
  return response.data;
};

export const getDocumentStatus = async (documentId) => {
  const response = await apiClient.get(`/documents/${documentId}`);
  return response.data;
};

export const deleteDocument = async (documentId) => {
  const response = await apiClient.delete(`/documents/${documentId}`);
  return response.data;
};
