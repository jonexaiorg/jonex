import { createI18nInstance } from '@jonex/i18n-resources';
import zhLocales from '@/locales/zh.json';
import enLocales from '@/locales/en.json';

const i18n = createI18nInstance({
  resources: {
    zh: { translation: zhLocales },
    en: { translation: enLocales },
  },
});

export default i18n;
