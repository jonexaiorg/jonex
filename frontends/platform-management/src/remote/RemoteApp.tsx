import React from 'react'
import { createRoot } from 'react-dom/client'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import enUS from 'antd/locale/en_US'
import { I18nextProvider, useTranslation } from 'react-i18next'
import { antdTheme } from '@jonex/platform-theme'
import i18n from '@/locales/i18n'
import '@/styles/index.scss'
import AppRoute from '@/router'
import { LANGUAGE_STORAGE_KEY, writeAccessToken, writeCachedUser } from '@jonex/shell-sdk'

interface ShellContext {
  basePath?: string
  token?: string
  user?: Record<string, unknown>
  locale?: string
}

function HostedApp({ shellContext }: { shellContext?: ShellContext }) {
  const { i18n: activeI18n } = useTranslation()
  const antdLocale = (activeI18n.resolvedLanguage || activeI18n.language) === 'en' ? enUS : zhCN

  return (
    <ConfigProvider locale={antdLocale} theme={antdTheme}>
      <AppRoute
        basename={shellContext?.basePath || '/apps/platform-management'}
        mode="hosted"
        shellContext={shellContext}
      />
    </ConfigProvider>
  )
}

export default function mount(container: HTMLElement, shellContext?: ShellContext): () => void {
  const { token, user, locale: shellLocale } = shellContext || {}

  if (token) writeAccessToken(token)
  if (user) writeCachedUser(user)

  const currentLocale = (i18n.resolvedLanguage || i18n.language) === 'en' ? 'en' : 'zh'
  const initialLocale = shellLocale === 'en' || shellLocale === 'zh' ? shellLocale : currentLocale
  window.localStorage.setItem(LANGUAGE_STORAGE_KEY, initialLocale)
  void i18n.changeLanguage(initialLocale)

  const root = createRoot(container)
  root.render(
    <I18nextProvider i18n={i18n}>
      <HostedApp shellContext={shellContext} />
    </I18nextProvider>,
  )

  let mounted = true
  return () => {
    if (!mounted) return
    mounted = false
    root.unmount()
  }
}
