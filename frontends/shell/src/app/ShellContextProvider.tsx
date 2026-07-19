import React, { createContext, useContext, useCallback, type ReactNode } from 'react'
import i18n from '../locales/i18n'
import type { ShellContext, ShellUser, SupportedLocale } from '@jonex/shell-sdk'
import { LANGUAGE_STORAGE_KEY } from '@jonex/shell-sdk'

interface ShellContextProviderProps {
  children: ReactNode
  token: string | null
  user: ShellUser | null
  locale: SupportedLocale
  setLocale: (locale: SupportedLocale) => void
  logout: () => void
}

const ShellCtx = createContext<ShellContext | null>(null)

export function ShellContextProvider({ children, token, user, locale, setLocale, logout }: ShellContextProviderProps) {
  const listeners = new Map<string, Set<(payload?: unknown) => void>>()

  const ctx: ShellContext = {
    appId: 'shell',
    basePath: '/',
    mode: 'hosted',
    token,
    user,
    locale,
    theme: {},
    setLocale,
    navigate: (to: string) => {
      window.location.href = to
    },
    logout,
    getToken: () => token,
    getCurrentUser: () => user,
    emitEvent: (name: string, payload?: unknown) => {
      const handlers = listeners.get(name)
      if (handlers) {
        handlers.forEach((fn) => {
          try { fn(payload) } catch {   }
        })
      }
    },
    onEvent: (name: string, handler: (payload?: unknown) => void) => {
      if (!listeners.has(name)) listeners.set(name, new Set())
      listeners.get(name)!.add(handler)
      return () => { listeners.get(name)?.delete(handler) }
    },
    reportError: (error: unknown, extra?: Record<string, unknown>) => {
      console.error('[shell] Sub-app error:', error, extra)
    },
    reportMetric: (name: string, value: number, tags?: Record<string, string>) => {
      console.log('[shell] Metric:', name, value, tags)
    },
  }

  return <ShellCtx.Provider value={ctx}>{children}</ShellCtx.Provider>
}

export function useShellContext(): ShellContext | null {
  return useContext(ShellCtx)
}
