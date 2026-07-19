import React, { createContext, useContext } from 'react'
import type { SupportedLocale } from '@jonex/shell-sdk'

export interface LocaleContextValue {
  locale: SupportedLocale
  setLocale: (locale: SupportedLocale) => void
}

const LocaleContext = createContext<LocaleContextValue>({
  locale: 'en',
  setLocale: () => {},
})

export function useAppLocale(): LocaleContextValue {
  return useContext(LocaleContext)
}

export default LocaleContext
