import React, { createContext, useContext, type ReactNode } from 'react'
import global from './global'

interface ComboStore {
  global: typeof global
}

const comboStore: ComboStore = {
  global,
}
const StoreContext = createContext<ComboStore | null>(null)

export function useStore(): ComboStore {
  const context = useContext(StoreContext)
  return context || comboStore
}

export function StoreProvider({ children, store }: { children: ReactNode; store?: ComboStore }) {
  return <StoreContext.Provider value={store ?? null}>{children}</StoreContext.Provider>
}

export default comboStore
