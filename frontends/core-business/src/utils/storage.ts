import { clearLocalStorageExcept } from '@/utils/utils'

export function getItem<T = unknown>(k: string): T | null {
  const raw = localStorage.getItem(k)
  if (raw === null) return null
  try {
    return JSON.parse(raw) as T
  } catch {
    return raw as unknown as T
  }
}

export function setItem(k: string, v: unknown): void {
  localStorage.setItem(k, JSON.stringify(v))
}

export function removeItem(k: string): void {
  localStorage.removeItem(k)
}

export function clearAll(): void {
  clearLocalStorageExcept(['locale'])
  clearAllCookie()
}

export function setCookie(cname: string, cvalue: string, exhours: number): void {
  const d = new Date()
  d.setTime(d.getTime() + exhours * 60 * 60 * 1000)
  const expires = 'expires=' + d.toUTCString()
  document.cookie = cname + '=' + cvalue + '; ' + expires
}

export function getCookie(cname: string): string {
  const name = cname + '='
  const ca = document.cookie.split(';')
  for (let i = 0; i < ca.length; i++) {
    const c = ca[i].trim()
    if (c.indexOf(name) === 0) {
      return c.substring(name.length, c.length)
    }
  }
  return ''
}

export function clearAllCookie(): void {
  const cookies = document.cookie.split(';')
  for (let i = 0; i < cookies.length; i++) {
    const cookie = cookies[i]
    const eqPos = cookie.indexOf('=')
    const name = eqPos > -1 ? cookie.substring(0, eqPos) : cookie
    document.cookie = name + '=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT'
  }
}
