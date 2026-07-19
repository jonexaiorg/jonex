import type { AppManifest, AppManifestEntry } from '@jonex/shell-sdk'
import { isManifestV2 } from '@jonex/shell-sdk'

const PLATFORM_MANIFEST_URL = '/api/v1/platform/frontend/apps'
const FALLBACK_MANIFEST_URL = '/app-manifest.json'

let cachedManifest: AppManifest | null = null
let cacheTime = 0
const CACHE_TTL = 5 * 60 * 1000

export async function fetchAppManifest(): Promise<AppManifest> {
  const now = Date.now()
  if (cachedManifest && now - cacheTime < CACHE_TTL) {
    return cachedManifest
  }

  let data: AppManifest | null = null

  try {
    data = await loadManifest(PLATFORM_MANIFEST_URL)
  } catch (error) {
    console.warn('[shell] platform manifest unavailable, using local fallback', error)
    data = await loadManifest(FALLBACK_MANIFEST_URL)
  }

  if (!isManifestV2(data)) {
    throw new Error('Unsupported manifest schema version')
  }

  cachedManifest = data
  cacheTime = now
  return cachedManifest
}

async function loadManifest(url: string): Promise<AppManifest> {
  const resp = await fetch(url)
  if (!resp.ok) {
    throw new Error(`Failed to fetch app manifest from ${url}: ${resp.status}`)
  }

  const payload = await resp.json()
  return (payload?.data ?? payload) as AppManifest
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
