import axios from 'axios'
import type { ShellUser } from '@jonex/shell-sdk'
import {
  JONEX_ACCESS_TOKEN_KEY,
  JONEX_REFRESH_TOKEN_KEY,
  JONEX_USER_KEY,
  LEGACY_USER_INFO_KEY,
  readAccessToken,
  writeAccessToken,
  readCachedUser,
  writeCachedUser,
  clearAuthStorage,
} from '@jonex/shell-sdk'

const LOCALE_KEY = 'locale'

export const getAccessToken = readAccessToken
export const getUser = readCachedUser<ShellUser>

function normalizeUser(raw: Record<string, unknown>): ShellUser {
  const id = String(raw.user_id || raw.id || '')
  const username = String(raw.username || '')
  const displayName = String(raw.display_name || raw.displayName || username)
  const roles: string[] = Array.isArray(raw.roles)
    ? raw.roles as string[]
    : raw.role
      ? [raw.role as string]
      : []
  return { id, username, displayName, roles } as ShellUser
}

export function setTokens(access: string, refresh: string): void {
  writeAccessToken(access)
  if (refresh) localStorage.setItem(JONEX_REFRESH_TOKEN_KEY, refresh)
}

export function setUser(user: Record<string, unknown>): void {
  const normalized = normalizeUser(user)
  writeCachedUser(normalized)
}

export function setLocale(locale: string): void {
  localStorage.setItem(LOCALE_KEY, locale)
}

export function getLocale(): string {
  return localStorage.getItem(LOCALE_KEY) || 'zh'
}

export function clearTokens(): void {
  clearAuthStorage()
}

/**
 * Clean up legacy URL token params (jonex_token, jonex_user, jonex_refresh_token).
 * Only handles ticket/code/state for future ticket-exchange flow.
 */
export function initCrossOriginAuth(): void {
  const params = new URLSearchParams(window.location.search)
  const blockedKeys = ['jonex_token', 'jonex_user', 'jonex_refresh_token']
  let changed = false
  blockedKeys.forEach((key) => {
    if (params.has(key)) {
      params.delete(key)
      changed = true
    }
  })
  if (changed) {
    const url = new URL(window.location.href)
    url.search = params.toString()
    window.history.replaceState({}, '', url.toString())
  }
}

export function isAuthenticated(): boolean {
  return !!getAccessToken()
}

export const apiClient = axios.create({
  baseURL: '/',
  timeout: 30000,
})

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

interface LoginResult {
  access_token: string
  refresh_token: string
  user: ShellUser
}

export async function login(username: string, password: string): Promise<LoginResult> {
  const resp = await apiClient.post<LoginResult>('/api/v1/auth/login', { username, password })
  return resp.data
}

export async function fetchCurrentUser(): Promise<ShellUser> {
  const resp = await apiClient.get<ShellUser>('/api/v1/auth/me')
  return resp.data
}

export function logout(): void {
  clearTokens()
  window.location.href = '/login'
}

export default apiClient
