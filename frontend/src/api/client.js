import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://terravyn-backend.onrender.com';

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`, // Backend base URL
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to attach the JWT token to every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Helper function to append 'Z' to naive UTC datetime strings
const appendZToDates = (obj) => {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }

  // ISO 8601 regex for datetime without timezone (e.g., "2026-06-14T22:14:55" or "2026-06-14T22:14:55.123456")
  const dateRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d*)?$/;

  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      if (typeof obj[key] === 'string' && dateRegex.test(obj[key])) {
        obj[key] += 'Z';
      } else if (typeof obj[key] === 'object') {
        appendZToDates(obj[key]);
      }
    }
  }
  return obj;
};

// Interceptor to handle 401 Unauthorized responses and format dates
apiClient.interceptors.response.use((response) => {
  if (response.data) {
    appendZToDates(response.data);
  }
  return response;
}, (error) => {
  if (error.response && error.response.status === 401) {
    // Token is invalid or expired
    localStorage.removeItem('token');
    window.location.href = '/login';
  }
  return Promise.reject(error);
});

export default apiClient;
