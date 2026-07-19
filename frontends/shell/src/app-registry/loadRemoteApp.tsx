interface FederationRemote {
  get: (module: string) => Promise<() => { default?: unknown }>
  init?: (sharedScope: Record<string, unknown>) => void
}

interface LoadRemoteOptions {
  entry: string
  scope: string
  module: string
}

declare global {
  interface Window {
    __federation_shared__?: Record<string, unknown>
  }
}

const loadedRemotes: Record<string, FederationRemote> = {}

export async function loadRemoteApp<T = (container: HTMLElement, context: unknown) => () => void>({
  entry,
  scope,
  module,
}: LoadRemoteOptions): Promise<T> {
  if (!entry || !scope || !module) {
    throw new Error('loadRemoteApp: entry, scope, and module are required')
  }

  let remote: FederationRemote
  if (!loadedRemotes[scope]) {
    try {
      const moduleUrl = entry + '?v=' + Date.now()
      remote = (await import(  moduleUrl)) as FederationRemote
    } catch (err) {
      throw new Error(`Failed to load remote entry "${entry}": ${(err as Error).message}`)
    }

    if (!remote || typeof remote.get !== 'function') {
      throw new Error(
        `Remote "${scope}" entry loaded but has no get() function. ` +
        `Is "${entry}" a valid federation remoteEntry?`
      )
    }

    if (typeof remote.init === 'function') {
      const sharedScope = window.__federation_shared__ || {}
      remote.init(sharedScope)
    }

    loadedRemotes[scope] = remote
  } else {
    remote = loadedRemotes[scope]
  }

  const factory = await remote.get(module)
  if (typeof factory !== 'function') {
    throw new Error(`Remote "${scope}" module "${module}" did not return a factory function`)
  }

  const Module = factory()
  return (Module as { default?: T }).default || (Module as T)
}
