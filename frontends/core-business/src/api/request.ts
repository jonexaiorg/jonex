import axios from 'axios'
import { readAccessToken } from '@jonex/shell-sdk'
import i18next from '@/locales/i18n'

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
  traceId?: string
}

export const request = axios.create({
  baseURL: (import.meta as any).env?.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
})

request.interceptors.request.use((config) => {
  const token = readAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  (response) => {
    const body = response.data as ApiResponse<unknown>
    if (body.code !== 0) {
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    return response
  },
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      import('antd').then(({ message }) => {
        message.error(i18next.t('knowledgeSearch.sessionExpired'))
      })
    }
    return Promise.reject(error)
  },
)

export async function getData<T>(promise: Promise<{ data: ApiResponse<T> }>): Promise<T> {
  const response = await promise
  return response.data.data
}

export async function postData<T>(url: string, data?: unknown): Promise<T> {
  return getData<T>(request.post(url, data))
}

export async function putData<T>(url: string, data?: unknown): Promise<T> {
  return getData<T>(request.put(url, data))
}

export async function deleteData<T>(url: string): Promise<T> {
  return getData<T>(request.delete(url))
}
