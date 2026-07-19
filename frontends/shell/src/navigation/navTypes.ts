import type { ComponentType } from 'react'

export interface PrototypeNavItem {
  key: string
  label: string
  appId?: string
  internalPath?: string
  icon?: ComponentType
  tag?: '设计中' | '未来'
  children?: PrototypeNavItem[]
}

export interface NavSection {
  key: string
  label: string
  icon: ComponentType
  items: PrototypeNavItem[]
}

export interface BreadcrumbEntry {
  title: string
  path: string
}
