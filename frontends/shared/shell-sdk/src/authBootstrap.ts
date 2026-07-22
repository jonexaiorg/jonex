import type { ShellUser } from './types'
import { readAccessToken, writeAccessToken, writeRefreshToken, writeCachedUser, clearAuthStorage } from './authStorage'
import {
  buildLoginRedirectUrl,
  hasTicketCallback,
  getTicketCallback,
  stripBlockedAuthQuery,
  stripCallbackQuery,
} from './authRedirect'

export interface AuthBootstrapOptions {
  appId: string
  loginUrl: string
  authMeUrl?: string
  exchangeTicketUrl?: string
  currentUrl?: string
  fetchImpl?: typeof fetch
}

export interface AuthBootstrapResult {
  authenticated: boolean
  token: string | null
  user: ShellUser | null
  source: 'ticket' | 'local-token' | 'none'
}

export async function bootstrapStandaloneAuth(
  options: AuthBootstrapOptions,
): Promise<AuthBootstrapResult> {
  const fetchFn = options.fetchImpl || window.fetch.bind(window)
  const currentUrl = options.currentUrl || window.location.href
  const url = new URL(currentUrl)
  const getCleanCurrentUrl = () => {
    const cleanUrl = new URL(url.toString())
    stripBlockedAuthQuery(cleanUrl)
    stripCallbackQuery(cleanUrl)
    return cleanUrl.toString()
  }

  // 1. 清理历史 URL token 参数
  const originalUrl = url.toString()
  stripBlockedAuthQuery(url)
  if (url.toString() !== originalUrl) {
    window.history.replaceState({}, '', url.toString())
  }

  // 2. 如果有 ticket/code，尝试交换 token
  if (hasTicketCallback(url) && options.exchangeTicketUrl) {
    try {
      const cb = getTicketCallback(url)
      const resp = await fetchFn(options.exchangeTicketUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          appId: options.appId,
          ticket: cb.ticket,
          code: cb.code,
          state: cb.state,
          redirectUri: window.location.origin + window.location.pathname,
        }),
      })

      if (resp.ok) {
        const data = await resp.json()
        const accessToken = data.access_token || data.accessToken
        const user = data.user
        if (accessToken) {
          writeAccessToken(accessToken)
          if (data.refresh_token) {
            writeRefreshToken(data.refresh_token)
          }
          if (user) writeCachedUser(user)
          // 清理 URL 中的 ticket/code/state
          stripCallbackQuery(url)
          window.history.replaceState({}, '', url.toString())
          return { authenticated: true, token: accessToken, user: user || null, source: 'ticket' }
        }
      }
    } catch (err) {
      console.error('[authBootstrap] Ticket exchange failed:', err)
    }
  }

  // URL 中有 ticket/code 但交换失败或未配置 exchange endpoint
  // 清理 URL 参数避免残留
  if (hasTicketCallback(url)) {
    stripCallbackQuery(url)
    window.history.replaceState({}, '', url.toString())
  }

  // 3. 如果本域有 token，验证有效性
  const token = readAccessToken()
  if (token) {
    if (options.authMeUrl) {
      try {
        const resp = await fetchFn(options.authMeUrl, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (resp.ok) {
          const data = await resp.json()
          const user = data.user || data
          if (user && user.id) {
            writeCachedUser(user)
            return { authenticated: true, token, user: user as ShellUser, source: 'local-token' }
          }
        }
        // 401 或其他错误 → 清理并跳转登录
        if (resp.status === 401 || resp.status === 403) {
          clearAuthStorage({ keepLocale: true })
          window.location.href = buildLoginRedirectUrl(options.loginUrl, getCleanCurrentUrl(), options.appId)
          return { authenticated: false, token: null, user: null, source: 'none' }
        }
      } catch {
        // 网络错误，信任本地 token
        return { authenticated: true, token, user: null, source: 'local-token' }
      }
    }
    // 没有配置 authMeUrl，信任本地 token
    return { authenticated: true, token, user: null, source: 'local-token' }
  }

  // 4. 无任何登录态 → 跳转登录页
  window.location.href = buildLoginRedirectUrl(options.loginUrl, getCleanCurrentUrl(), options.appId)
  return { authenticated: false, token: null, user: null, source: 'none' }
}
