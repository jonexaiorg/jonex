import { useEffect } from 'react';
import { useLocation, matchRoutes } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getRoutes } from '@/router/routes.config';

export default function useDocumentTitle() {
  const location = useLocation();
  const { i18n } = useTranslation();

  useEffect(() => {
    const updateTitle = () => {
      const routeData = getRoutes();
      const matches = matchRoutes(routeData as any[], location);
      if (!matches || matches?.length === 0) return;

      const route = matches[matches.length - 1].route as Record<string, any>;
      const titleKey = (route?.title || route?.handle?.title || 'site.title') as string;
      if (titleKey) {
        document.title = i18n.t(titleKey);
      }
    };

    updateTitle();

    const handleLangChange = () => updateTitle();
    i18n.on('languageChanged', handleLangChange);

    return () => {
      i18n.off('languageChanged', handleLangChange);
    };
  }, [location, i18n]);
}
