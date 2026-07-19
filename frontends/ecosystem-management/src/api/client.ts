import axios from 'axios'
import { readAccessToken } from '@jonex/shell-sdk'

const apiClient = axios.create({
  baseURL: '/',
  timeout: 30000,
})

apiClient.interceptors.request.use((config) => {
  const token = readAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default apiClient
