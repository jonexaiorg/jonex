import React, { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import type { AppManifest, AppManifestEntry } from '@jonex/shell-sdk'
import { fetchAppManifest } from '../api/manifest'

interface ManifestContextValue {
  manifest: AppManifest | null
  loading: boolean
  error: string | null
  getApp: (appId: string) => AppManifestEntry | undefined
  getEnabledApps: (userRoles: string[]) => AppManifestEntry[]
}

const ManifestContext = createContext<ManifestContextValue | null>(null)

export function ManifestProvider({ children }: { children: ReactNode }) {
  const [manifest, setManifest] = useState<AppManifest | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchAppManifest()
      .then(setManifest)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const value: ManifestContextValue = {
    manifest,
    loading,
    error,
    getApp: (appId: string) => manifest?.apps.find((a) => a.id === appId),
    getEnabledApps: (userRoles: string[]) => {
      if (!manifest?.apps) return []
      return manifest.apps
        .filter((app) => {
          if (!app.enabled) return false
          const roles = app.roles ?? (app as any).permissions?.visibleRoles
          if (!roles || roles.length === 0) return true
          return roles.some((r: string) => userRoles.includes(r))
        })
        .sort((a, b) => (a.order ?? 999) - (b.order ?? 999))
    },
  }

  return (
    <ManifestContext.Provider value={value}>
      {children}
    </ManifestContext.Provider>
  )
}

export function useManifest(): ManifestContextValue {
  const ctx = useContext(ManifestContext)
  if (!ctx) {
    return {
      manifest: null,
      loading: false,
      error: 'ManifestProvider not mounted',
      getApp: () => undefined,
      getEnabledApps: () => [],
    }
  }
  return ctx
}
