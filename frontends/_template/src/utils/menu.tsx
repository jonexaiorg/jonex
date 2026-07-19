import React from 'react'
import { IconMap, menuConfig, type MenuItem } from '@/router/menu.config'

interface RenderedMenuItem {
  key: string
  icon?: React.ReactNode
  label: string
  children?: RenderedMenuItem[]
}

export function renderMenuItems(menuData: MenuItem[] = [], t: (key: string) => string): RenderedMenuItem[] {
  return menuData.map((item): RenderedMenuItem => {
    const Icon = item.icon ? IconMap[item.icon] : null
    const labelText = t(item.label || item.key)

    if (item.children && item.children.length > 0) {
      return {
        key: item.key,
        icon: Icon ? <Icon /> : undefined,
        label: labelText,
        children: renderMenuItems(item.children, t),
      }
    }

    return {
      key: item.path || item.key,
      icon: Icon ? <Icon /> : undefined,
      label: labelText,
    }
  })
}

export function findMenuPathKeys(menuData: MenuItem[] = [], path: string) {
  let result = { selectedKey: '', openKeys: [] as string[] }

  function traverse(items: MenuItem[], parents: string[]): { selectedKey: string; openKeys: string[] } | null {
    for (const item of items) {
      const currentParents = [...parents]
      if (item.children && item.children.length > 0) {
        currentParents.push(item.key)
        const found: { selectedKey: string; openKeys: string[] } | null = traverse(item.children, currentParents)
        if (found) return found
      }
      if (item.path === path) {
        return {
          selectedKey: item.path,
          openKeys: currentParents,
        }
      }
    }
    return null
  }

  const found = traverse(menuData, [])
  if (found) result = found
  return result
}

export function getMenuItemsByRole(
  menuConfigData: MenuItem[],
  roles: string = '',
  tFn?: (key: string) => string,
): RenderedMenuItem[] {
  const roleList = Array.isArray(roles)
    ? roles
    : String(roles || '').split(',').map((r) => r.trim()).filter(Boolean)

  const hasRoleAccess = (item: MenuItem) => {
    if (!item.roles || item.roles.length === 0) return true
    return item.roles.some((role) => roleList.includes(role))
  }

  const filterAndRender = (menus: MenuItem[]): RenderedMenuItem[] => {
    return menus
      .filter(hasRoleAccess)
      .map((item) => {
        const Icon = item.icon ? IconMap[item.icon] : null
        const menuItem: RenderedMenuItem = {
          key: item.path || item.key,
          icon: Icon ? <Icon /> : undefined,
          label: tFn ? tFn(item.label) : item.label,
        }
        if (item.children) {
          menuItem.children = filterAndRender(item.children)
        }
        return menuItem
      })
  }

  return filterAndRender(menuConfigData)
}
