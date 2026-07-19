import React, { useState, useEffect, useCallback } from 'react'
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { ConfigProvider, Spin } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import enUS from 'antd/locale/en_US'
import { antdTheme } from '@jonex/platform-theme'
import { LANGUAGE_STORAGE_KEY, isSupportedLocale } from '@jonex/shell-sdk'
import type { SupportedLocale } from '@jonex/shell-sdk'
import './locales/i18n'
import i18n from './locales/i18n'
import LocaleContext from './locales/LocaleContext'
import Login from './pages/Login'
import AppShellLayout from './components/AppShellLayout'
import Dashboard from './pages/Dashboard'
import AppHost from './pages/AppHost'
import { getAccessToken, clearTokens, fetchCurrentUser } from './api/auth'
import type { ReactNode } from 'react'

function RequireAuth({ children }: { children: ReactNode }) {
  const [authChecked, setAuthChecked] = useState(false)
  const [isAuth, setIsAuth] = useState(false)

  useEffect(() => {
    const token = getAccessToken()
    if (!token) {
      setIsAuth(false)
      setAuthChecked(true)
      return
    }
    fetchCurrentUser()
      .then(() => { setIsAuth(true); setAuthChecked(true) })
      .catch((err: unknown) => {
        const status = (err as { response?: { status?: number } })?.response?.status
        if (status === 401 || status === 403) {
          clearTokens()
          setIsAuth(false)
        } else {

          setIsAuth(true)
        }
        setAuthChecked(true)
      })
  }, [])

  if (!authChecked) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        background: '#f0f4f8',
      }}>
        <Spin size="large" />
      </div>
    )
  }
  if (!isAuth) {
    const redirectParam = encodeURIComponent(window.location.href)
    return <Navigate to={`/login?redirect=${redirectParam}`} replace />
  }
  return <>{children}</>
}

function AuthenticatedLayout() {
  return (
    <RequireAuth>
      <AppShellLayout>
        <Outlet />
      </AppShellLayout>
    </RequireAuth>
  )
}

function App() {
  const [locale, setLocaleState] = useState<SupportedLocale>(() => {
    const storedLocale = localStorage.getItem(LANGUAGE_STORAGE_KEY)
    return storedLocale && isSupportedLocale(storedLocale) ? storedLocale : 'en'
  })

  const handleSetLocale = useCallback((newLocale: string) => {
    const lang: SupportedLocale = isSupportedLocale(newLocale) ? newLocale : 'en'
    setLocaleState(lang)
    localStorage.setItem(LANGUAGE_STORAGE_KEY, lang)
    i18n.changeLanguage(lang)

    window.dispatchEvent(new CustomEvent('jonex:locale-change', { detail: lang }))
  }, [])

  const antdLocale = locale === 'en' ? enUS : zhCN

  return (
    <ConfigProvider locale={antdLocale} theme={antdTheme}>
      <LocaleContext.Provider value={{ locale: locale as SupportedLocale, setLocale: handleSetLocale }}>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route element={<AuthenticatedLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="apps/:appId/*" element={<AppHost />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </LocaleContext.Provider>
    </ConfigProvider>
  )
}

export default App
