import axios from 'axios';

export const axiosInstance = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

// Интерсептор запроса: добавляем токен
axiosInstance.interceptors.request.use((config) => {
  if (config.url && !config.url.endsWith('/')) {
    config.url += '/';
  }
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Интерсептор ответа: обработка 401 и рефреш
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const { data } = await axios.post('/api/auth/refresh/', { refresh: refreshToken });
        localStorage.setItem('access_token', data.access);
        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        // рефреш не удался – разлогиниваем пользователя
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export default async function customMutator<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await axiosInstance({
    url,
    method: options?.method,
    data: options?.body ? JSON.parse(options.body as string) : undefined,
    headers: options?.headers,
    signal: options?.signal,
  });
  return response.data;
}