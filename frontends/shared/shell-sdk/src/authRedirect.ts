export const BLOCKED_AUTH_QUERY_KEYS = [
  'jonex_token',
  'jonex_refresh_token',
  'jonex_user',
]

export const CALLBACK_QUERY_KEYS = [
  'ticket',
  'code',
  'state',
]

export function buildLoginRedirectUrl(loginUrl: string, redirectUrl: string, appId?: string): string {
  const sep = loginUrl.includes('?') ? '&' : '?'
  let url = `${loginUrl}${sep}redirect=${encodeURIComponent(redirectUrl)}`
  if (appId) {
    url += `&appId=${encodeURIComponent(appId)}`
  }
  return url
}

export function stripBlockedAuthQuery(url: URL): URL {
  let changed = false
  BLOCKED_AUTH_QUERY_KEYS.forEach((key) => {
    if (url.searchParams.has(key)) {
      url.searchParams.delete(key)
      changed = true
    }
  })
  return url
}

export function stripCallbackQuery(url: URL): URL {
  let changed = false
  CALLBACK_QUERY_KEYS.forEach((key) => {
    if (url.searchParams.has(key)) {
      url.searchParams.delete(key)
      changed = true
    }
  })
  return url
}

export function hasTicketCallback(url: URL): boolean {
  return CALLBACK_QUERY_KEYS.some((key) => url.searchParams.has(key))
}

export function getTicketCallback(url: URL): { ticket?: string; code?: string; state?: string } {
  return {
    ticket: url.searchParams.get('ticket') || undefined,
    code: url.searchParams.get('code') || undefined,
    state: url.searchParams.get('state') || undefined,
  }
}

export function isAllowedRedirect(url: URL, allowedOrigins: string[]): boolean {
  const origin = url.origin
  return allowedOrigins.some((allowed) => {
    if (allowed === origin) return true
    // 支持 localhost 通配端口
    if (allowed.startsWith('http://localhost:') || allowed.startsWith('http://127.0.0.1:')) {
      return origin.startsWith(allowed.split(':').slice(0, -1).join(':'))
    }
    return false
  })
}
