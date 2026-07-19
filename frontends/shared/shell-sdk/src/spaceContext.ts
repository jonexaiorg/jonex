






export const SPACE_STORAGE_KEY = 'jonex:core-business:selected-space-id'
export const SPACE_CHANGED_EVENT = 'jonex:core-business:space-changed'
export const SPACE_URL_PARAM = 'space_id'

export interface SpaceChangedDetail {
  spaceId: string | null
}


export function persistSpaceId(spaceId: string | null): void {
  if (spaceId) {
    localStorage.setItem(SPACE_STORAGE_KEY, spaceId)
  } else {
    localStorage.removeItem(SPACE_STORAGE_KEY)
  }
}


export function emitSpaceChanged(spaceId: string | null): void {
  window.dispatchEvent(
    new CustomEvent<SpaceChangedDetail>(SPACE_CHANGED_EVENT, {
      detail: { spaceId },
    }),
  )
}


export function broadcastSpaceChange(spaceId: string | null): void {
  persistSpaceId(spaceId)
  emitSpaceChanged(spaceId)
}


export function readPersistedSpaceId(): string | null {
  return localStorage.getItem(SPACE_STORAGE_KEY)
}







export function onSpaceChanged(
  handler: (spaceId: string | null) => void,
): () => void {
  const onCustom = (e: Event) =>
    handler((e as CustomEvent<SpaceChangedDetail>).detail?.spaceId ?? null)
  const onStorage = (e: StorageEvent) => {
    if (e.key === SPACE_STORAGE_KEY) handler(e.newValue)
  }
  window.addEventListener(SPACE_CHANGED_EVENT, onCustom)
  window.addEventListener('storage', onStorage)
  return () => {
    window.removeEventListener(SPACE_CHANGED_EVENT, onCustom)
    window.removeEventListener('storage', onStorage)
  }
}


export const SPACES_INVALIDATED_EVENT =
  'jonex:core-business:spaces-invalidated'
const SPACES_INVALIDATED_KEY = 'jonex:core-business:spaces-invalidated-at'


export function emitSpacesInvalidated(): void {
  try {
    localStorage.setItem(SPACES_INVALIDATED_KEY, String(Date.now()))
  } catch {

  }
  window.dispatchEvent(new CustomEvent(SPACES_INVALIDATED_EVENT))
}


export function onSpacesInvalidated(handler: () => void): () => void {
  const onCustom = () => handler()
  const onStorage = (e: StorageEvent) => {
    if (e.key === SPACES_INVALIDATED_KEY) handler()
  }
  window.addEventListener(SPACES_INVALIDATED_EVENT, onCustom)
  window.addEventListener('storage', onStorage)
  return () => {
    window.removeEventListener(SPACES_INVALIDATED_EVENT, onCustom)
    window.removeEventListener('storage', onStorage)
  }
}
