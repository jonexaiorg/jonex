import axios from 'axios';
import { readAccessToken, clearAuthStorage } from '@jonex/shell-sdk';

const apiClient = axios.create({
  baseURL: '/',
  timeout: 30000,
});

apiClient.interceptors.request.use((config) => {
  const token = readAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const locale = localStorage.getItem('jonex_locale') || 'en';
  config.headers['X-Lang'] = locale === 'en' ? 'en-US' : 'zh-CN';
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        clearAuthStorage({ keepLocale: true });
        try {
          (window.top || window.parent || window).dispatchEvent(new CustomEvent('jonex:token-expired'));
        } catch {}
        if (window.parent === window && (window as any).__SHELL_CONTEXT__?.mode !== 'hosted') {
          window.location.href = `/login?redirect=${encodeURIComponent(window.location.href)}`;
        }
      }
      const backendMsg = (error.response?.data as { message?: string })?.message;
      if (backendMsg) {
        return Promise.reject(new Error(backendMsg));
      }
    }
    return Promise.reject(error);
  },
);

export default apiClient;
