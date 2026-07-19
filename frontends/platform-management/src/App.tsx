import React from 'react'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import enUS from 'antd/locale/en_US'
import { useTranslation } from 'react-i18next'
import { antdTheme } from '@jonex/platform-theme'
import AppRoute from '@/router'

export default function App() {
  const { i18n } = useTranslation()
  const locale = (i18n.resolvedLanguage || i18n.language) === 'en' ? enUS : zhCN

  return (
    <ConfigProvider locale={locale} theme={antdTheme}>
      <AppRoute mode="standalone" />
    </ConfigProvider>
  )
}
