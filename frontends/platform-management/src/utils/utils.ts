export const getAvatarText = (name: string = ''): string => {
  if (!name || typeof name !== 'string') return ''

  const parts = name.trim().split(/\s+/).filter(Boolean)

  if (parts.length === 0) return ''

  if (parts.length === 1 && /[一-龥]/.test(name)) {
    return name[0]
  }

  const initials = parts.map((part) => part[0].toUpperCase()).join('')
  return initials
}

export function clearLocalStorageExcept(keepKeys: string[] = []) {
  const keepSet = new Set(keepKeys)

  for (let i = localStorage.length - 1; i >= 0; i--) {
    const key = localStorage.key(i)
    if (key && !keepSet.has(key)) {
      localStorage.removeItem(key)
    }
  }
}
