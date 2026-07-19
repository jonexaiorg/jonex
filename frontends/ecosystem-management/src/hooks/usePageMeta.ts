import { useLocation } from 'react-router-dom'
import { getRoutes } from '@/router/routes.config'

interface RouteItem {
  path?: string
  children?: RouteItem[]
  meta?: Record<string, unknown>
  [key: string]: unknown
}

function matchRouteMeta(pathname: string, routeList: RouteItem[]): Record<string, unknown> | null {
  for (const route of routeList) {
    if (route.children) {
      const childMeta = matchRouteMeta(pathname, route.children)
      if (childMeta) return childMeta
    }

    let pattern = route.path || ''
    if (!pattern.startsWith('/')) pattern = '/' + pattern
    const regex = new RegExp(`^${pattern.replace(/:\w+/g, '[^/]+')}$`)
    if (regex.test(pathname)) return route.meta || null
  }
  return null
}

export default function usePageMeta() {
  const location = useLocation()
  const routeData = getRoutes() as RouteItem[]
  const meta = matchRouteMeta(location.pathname, routeData) || {}
  return meta
}
