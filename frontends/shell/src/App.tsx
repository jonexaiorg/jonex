import React, { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { ConfigProvider, Spin } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { antdTheme } from '@jonex/platform-theme'
import Login from './pages/Login'
import AppShellLayout from './components/AppShellLayout'
import Dashboard from './pages/Dashboard'
import AppHost from './pages/AppHost'
import { getAccessToken, clearTokens, fetchCurrentUser, getLocale, setLocale } from './api/auth'
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
          // 网络错误或远端不可达，信任本地 token
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
  if (!getLocale()) setLocale('zh')

  return (
    <ConfigProvider locale={zhCN} theme={antdTheme}>
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
    </ConfigProvider>
  )
}

export default App
