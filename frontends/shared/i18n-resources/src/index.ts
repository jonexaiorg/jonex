import i18n, { type i18n as I18nInstance, type InitOptions } from 'i18next'
import { initReactI18next } from 'react-i18next'
import zhResources from './locales/zh.json'
import enResources from './locales/en.json'


export const SUPPORTED_LOCALES = ['zh', 'en'] as const


export const LANGUAGE_OPTIONS: { label: string; value: string }[] = [
  { label: '中文', value: 'zh' },
  { label: 'English', value: 'en' },
]


export const LANGUAGE_STORAGE_KEY = 'jonex_locale'

export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number]

export function normalizeLocale(value?: string | null): SupportedLocale {
  return SUPPORTED_LOCALES.includes(value as SupportedLocale) ? value as SupportedLocale : 'en'
}

type TranslationRecord = Record<string, unknown>
type ResourceMap = Record<string, Record<string, TranslationRecord>>

function isPlainObject(value: unknown): value is TranslationRecord {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}




function deepMergeTranslations(base: TranslationRecord, override: TranslationRecord): TranslationRecord {
  const merged: TranslationRecord = { ...base }

  for (const [key, overrideValue] of Object.entries(override)) {
    const baseValue = merged[key]
    merged[key] = isPlainObject(baseValue) && isPlainObject(overrideValue)
      ? deepMergeTranslations(baseValue, overrideValue)
      : overrideValue
  }

  return merged
}







export function createI18nInstance(options?: {
  resources?: ResourceMap
  lng?: string
}): I18nInstance {
  const instance = i18n.createInstance()
  const resources: ResourceMap = {
    zh: { translation: { ...zhResources } },
    en: { translation: { ...enResources } },
  }

  for (const lang of SUPPORTED_LOCALES) {
    const businessNamespaces = options?.resources?.[lang]
    if (!businessNamespaces) continue

    for (const [namespace, businessResources] of Object.entries(businessNamespaces)) {
      const commonResources = resources[lang][namespace] ?? {}
      resources[lang][namespace] = deepMergeTranslations(commonResources, businessResources)
    }
  }

  const initOptions: InitOptions = {
    fallbackLng: 'en',
    lng: normalizeLocale(options?.lng ?? (typeof window !== 'undefined'
      ? window.localStorage.getItem(LANGUAGE_STORAGE_KEY)
      : null)),
    interpolation: {
      escapeValue: false,
    },
    resources,
  }

  void instance.use(initReactI18next).init(initOptions)
  return instance
}
