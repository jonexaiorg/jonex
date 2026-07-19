import { useEffect } from 'react'
import { useLocation, matchRoutes } from 'react-router-dom'
import i18next from '@/locales/i18n'
import { getRoutes } from '@/router/routes.config'

export default function useDocumentTitle() {
  const location = useLocation()

  useEffect(() => {
    const updateTitle = () => {
      const routeData = getRoutes()
      const matches = matchRoutes(routeData as any[], location)
      if (!matches || matches?.length === 0) return

      const route = matches[matches.length - 1].route as Record<string, any>
      const titleKey = (route?.title || route?.handle?.title || 'site.title') as string
      if (titleKey) {
        document.title = i18next.t(titleKey)
      }
    }

    updateTitle()

    const handleLangChange = () => updateTitle()
    i18next.on('languageChanged', handleLangChange)

    return () => {
      i18next.off('languageChanged', handleLangChange)
    }
  }, [location])
}
