import type { PrototypeNavItem, NavSection, BreadcrumbEntry } from './navTypes'
import { prototypeNavConfig } from './prototypeNav.config'

export function findActivePath(
  pathname: string,
): { section: NavSection; groupItem?: PrototypeNavItem; leaf?: PrototypeNavItem } | null {
  for (const section of prototypeNavConfig) {
    for (const item of section.items) {
      if (!item.children) {
        if (item.appId && item.internalPath) {
          const expected = `/apps/${item.appId}/${item.internalPath}`
          if (pathname === expected || pathname.startsWith(expected + '/')) {
            return { section, leaf: item }
          }
        }
      } else {
        for (const child of item.children) {
          if (child.appId && child.internalPath) {
            const expected = `/apps/${child.appId}/${child.internalPath}`
            if (pathname === expected || pathname.startsWith(expected + '/')) {
              return { section, groupItem: item, leaf: child }
            }
          }
        }
        // Check if the path matches the group itself (e.g. /apps/core-business/domain-management)
        if (item.appId && item.internalPath) {
          const expected = `/apps/${item.appId}/${item.internalPath}`
          if (pathname === expected || pathname.startsWith(expected + '/')) {
            return { section, groupItem: item }
          }
        }
      }
    }
    // Check app root fallback: /apps/<appId> or /apps/<appId>/
    for (const item of section.items) {
      const appId = item.appId || (item.children?.[0]?.appId)
      if (appId) {
        const prefix = `/apps/${appId}`
        if (pathname === prefix || pathname === prefix + '/') {
          return sectionHasPath(section, pathname, prefix, appId)
        }
      }
    }
  }
  return null
}

function sectionHasPath(
  section: NavSection,
  pathname: string,
  prefix: string,
  appId: string,
): { section: NavSection; groupItem?: PrototypeNavItem; leaf?: PrototypeNavItem } | null {
  for (const item of section.items) {
    if (!item.children && item.appId === appId) {
      return { section, leaf: item }
    }
    if (item.children) {
      const child = item.children[0]
      if (child?.appId === appId) {
        return { section, groupItem: item, leaf: child }
      }
    }
  }
  return null
}

export function getExpandedKeys(pathname: string): string[] {
  const keys: string[] = []
  for (const section of prototypeNavConfig) {
    for (const item of section.items) {
      if (item.children) {
        for (const child of item.children) {
          if (child.appId && child.internalPath) {
            const expected = `/apps/${child.appId}/${child.internalPath}`
            if (pathname === expected || pathname.startsWith(expected + '/')) {
              keys.push(item.key)
            }
          }
        }
      }
    }
  }
  return keys
}

export function getBreadcrumbItems(pathname: string): BreadcrumbEntry[] {
  const result = findActivePath(pathname)
  const items: BreadcrumbEntry[] = [{ title: '首页', path: '/' }]

  if (!result) return items

  items.push({ title: result.section.label, path: '#' })

  if (result.groupItem) {
    items.push({ title: result.groupItem.label, path: '#' })
  }

  if (result.leaf) {
    const leafPath = result.leaf.appId && result.leaf.internalPath
      ? `/apps/${result.leaf.appId}/${result.leaf.internalPath}`
      : '#'
    items.push({ title: result.leaf.label, path: leafPath })
  }

  return items
}
