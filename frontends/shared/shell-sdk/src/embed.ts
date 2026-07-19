









export const EMBED_QUERY_PARAM = 'embed'





export function isEmbedded(): boolean {
  if (typeof window === 'undefined') return false
  try {
    return new URLSearchParams(window.location.search).get(EMBED_QUERY_PARAM) === '1'
  } catch {
    return false
  }
}
