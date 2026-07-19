import type { ShellContext, ShellUser, SupportedLocale } from './types'
import { isSupportedLocale } from './types'
import { LANGUAGE_STORAGE_KEY } from './constants'
import { readAccessToken, readCachedUser, clearAuthStorage } from './authStorage'
import { buildLoginRedirectUrl } from './authRedirect'

interface StandaloneOptions {
  appId: string
  basePath: string
  token?: string | null
  user?: ShellUser | null
  locale?: string
  loginUrl?: string
}

const listeners = new Map<string, Set<(payload?: unknown) => void>>()

function resolveLocale(locale?: string | null): SupportedLocale {
  return locale && isSupportedLocale(locale) ? locale : 'en'
}

export function createStandaloneShellContext(options: StandaloneOptions): ShellContext {
  const appId = options.appId
  const basePath = options.basePath
  const initialLocale = resolveLocale(
    options.locale ?? (typeof window !== 'undefined'
      ? window.localStorage.getItem(LANGUAGE_STORAGE_KEY)
      : null),
  )

  const context: ShellContext = {
    appId,
    basePath,
    mode: 'standalone',
    token: options.token ?? readAccessToken(),
    user: options.user ?? readCachedUser<ShellUser>(),
    locale: initialLocale,
    theme: {},

    navigate: (to: string, opts?: { replace?: boolean }) => {
      const dest = `${basePath}${to}`.replace(/\/+/g, '/')
      if (opts?.replace) {
        window.location.replace(dest)
      } else {
        window.location.href = dest
      }
    },

    logout: () => {
      clearAuthStorage({ keepLocale: true })
      const loginUrl = options.loginUrl || '/login'
      window.location.href = buildLoginRedirectUrl(loginUrl, window.location.href, appId)
    },

    getToken: () => options.token ?? readAccessToken(),
    getCurrentUser: () => options.user ?? readCachedUser<ShellUser>(),

    setLocale: (locale: SupportedLocale) => {
      context.locale = locale
      window.localStorage.setItem(LANGUAGE_STORAGE_KEY, locale)
      window.dispatchEvent(new CustomEvent<SupportedLocale>('jonex:locale-change', { detail: locale }))
    },

    emitEvent: (name: string, payload?: unknown) => {
      const handlers = listeners.get(name)
      if (handlers) {
        handlers.forEach((fn) => {
          try { fn(payload) } catch {   }
        })
      }
    },

    onEvent: (name: string, handler: (payload?: unknown) => void) => {
      if (!listeners.has(name)) {
        listeners.set(name, new Set())
      }
      listeners.get(name)!.add(handler)
      return () => {
        listeners.get(name)?.delete(handler)
      }
    },

    reportError: (error: unknown, extra?: Record<string, unknown>) => {
      console.error('[shell-sdk] Sub-app error:', error, extra)
    },

    reportMetric: (name: string, value: number, tags?: Record<string, string>) => {
      console.log('[shell-sdk] Metric:', name, value, tags)
    },
  }

  return context
}
