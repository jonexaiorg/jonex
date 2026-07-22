import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import zhLocales from '@/locales/zh.json'
import enLocales from '@/locales/en.json'
import { getItem } from '@/utils/storage'

i18n.use(initReactI18next).init({
  fallbackLng: 'zh',
  lng: (getItem('locale') as string) || 'zh',
  resources: {
    zh: {
      translation: zhLocales,
    },
    en: {
      translation: enLocales,
    },
  },
  interpolation: {
    escapeValue: false,
  },
})

export default i18n
