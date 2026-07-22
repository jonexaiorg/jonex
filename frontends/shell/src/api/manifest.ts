import type { AppManifest, AppManifestEntry } from '@jonex/shell-sdk'
import { isManifestV2 } from '@jonex/shell-sdk'

const MANIFEST_URL = '/app-manifest.json'

let cachedManifest: AppManifest | null = null
let cacheTime = 0
const CACHE_TTL = 5 * 60 * 1000

export async function fetchAppManifest(): Promise<AppManifest> {
  const now = Date.now()
  if (cachedManifest && now - cacheTime < CACHE_TTL) {
    return cachedManifest
  }

  const resp = await fetch(MANIFEST_URL)
  if (!resp.ok) {
    throw new Error(`Failed to fetch app manifest: ${resp.status}`)
  }
  const data: AppManifest = await resp.json()

  if (isManifestV2(data) && data.schemaVersion !== 2) {
    throw new Error(`Unsupported manifest schema version: ${data.schemaVersion}`)
  }

  cachedManifest = data
  cacheTime = now
  return cachedManifest
}

export function getEnabledApps(manifest: AppManifest, userRoles: string[]): AppManifestEntry[] {
  if (!manifest?.apps) return []

  return manifest.apps
    .filter((app) => {
      if (!app.enabled) return false
      const roles = app.roles ?? (app as any).permissions?.visibleRoles
      if (!roles || roles.length === 0) return true
      return roles.some((r: string) => userRoles.includes(r))
    })
    .sort((a, b) => (a.order ?? 999) - (b.order ?? 999))
}
