import React, { createContext, useContext, type ReactNode } from 'react'
import type { ShellContext, ShellUser } from '@jonex/shell-sdk'

interface ShellContextProviderProps {
  children: ReactNode
  token: string | null
  user: ShellUser | null
  locale: string
  logout: () => void
}

const ShellCtx = createContext<ShellContext | null>(null)

export function ShellContextProvider({ children, token, user, locale, logout }: ShellContextProviderProps) {
  const listeners = new Map<string, Set<(payload?: unknown) => void>>()

  const ctx: ShellContext = {
    appId: 'shell',
    basePath: '/',
    mode: 'hosted',
    token,
    user,
    locale,
    theme: {},
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
          try { fn(payload) } catch { /* swallow */ }
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
