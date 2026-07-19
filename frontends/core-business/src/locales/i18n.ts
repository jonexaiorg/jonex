import { createI18nInstance, normalizeLocale } from '@jonex/i18n-resources'
import zhBusiness from './zh.json'
import enBusiness from './en.json'

const instance = createI18nInstance({
  resources: {


    zh: { translation: zhBusiness, business: zhBusiness },
    en: { translation: enBusiness, business: enBusiness },
  },
})


if (typeof window !== 'undefined') {
  window.addEventListener('jonex:locale-change', ((event: CustomEvent<string>) => {
    void instance.changeLanguage(normalizeLocale(event.detail))
  }) as EventListener)
}

export default instance
