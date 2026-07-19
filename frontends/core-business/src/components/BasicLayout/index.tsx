import React, { useState, useEffect, useMemo } from 'react'
import { Layout, Dropdown } from 'antd'
import { LogoutOutlined, HomeOutlined } from '@ant-design/icons'
import { Outlet, useNavigate, useLocation, Link, useMatches } from 'react-router-dom'
import { observer } from 'mobx-react-lite'
import { useTranslation } from 'react-i18next'
import { useStore } from '@/store'
import { menuConfig, IconMap } from '@/router/menu.config'
import type { MenuItem } from '@/router/menu.config'
import { buildLoginRedirectUrl, clearAuthStorage } from '@jonex/shell-sdk'
import SpaceSwitcher from '@/components/SpaceSwitcher'
import styles from './index.module.scss'

const { Content } = Layout

const BasicLayout = observer(() => {
  const { global } = useStore()
  const userInfo = global?.userInfo as Record<string, any> | null | undefined
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const matches = useMatches()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const VITE_LOGIN = (import.meta as any).env?.VITE_LOGIN || '/login'
  const VITE_APP_ID = (import.meta as any).env?.VITE_APP_ID || 'core-business'

  const roleList = useMemo(() => {
    if (!userInfo?.roles) return []
    if (Array.isArray(userInfo.roles)) return userInfo.roles
    return String(userInfo.roles).split(',').map(r => r.trim()).filter(Boolean)
  }, [userInfo?.roles])

  const visibleMenuItems = useMemo(() => {
    return menuConfig.filter(item => {
      if (!item.roles || item.roles.length === 0) return true
      if (roleList.length === 0) return true
      return item.roles.some(role => roleList.includes(role))
    })
  }, [roleList])

  const currentTitle = useMemo(() => {
    const match = matches.reverse().find(
      m => m.handle && (m.handle as Record<string, unknown>).title
    )
    return (match?.handle as Record<string, unknown>)?.title as string || ''
  }, [matches])

  useEffect(() => {
    const isMobile = window.innerWidth < 768
    if (isMobile) setSidebarCollapsed(true)
  }, [])

  const isItemActive = (item: MenuItem): boolean => {
    if (!item.path) return false
    return location.pathname === item.path || location.pathname.startsWith(item.path + '/')
  }

  const handleLogout = () => {
    clearAuthStorage({ keepLocale: true })
    global.setUserInfo(null)
    const loginUrl = VITE_LOGIN || '/login'
    window.location.href = buildLoginRedirectUrl(loginUrl, window.location.href, VITE_APP_ID)
  }

  const renderNavIcon = (iconName?: string) => {
    if (!iconName) return <span className="yx-sub-dot" />
    const IconComp = IconMap[iconName]
    if (!IconComp) return <span className="yx-sub-dot" />
    return (
      <span className="yx-nav-icon">
        <IconComp />
      </span>
    )
  }

  const sidebarWidth = sidebarCollapsed ? 64 : 240

  return (
    <div className={styles['page-layout']}>
      { }
      <aside className="yx-sidebar" style={{ width: sidebarWidth }}>
        <div className={styles['sidebar-brand']}>
          <Link to="/knowledge-search" style={{ textDecoration: 'none', color: 'inherit', display: 'flex', alignItems: 'center' }}>
            <img
              src={sidebarCollapsed ? '/favicon-white.png' : '/logo-white.svg'}
              alt="Jonex"
              style={{ height: sidebarCollapsed ? 36 : 32, transition: 'height 0.2s' }}
            />
          </Link>
        </div>

        <SpaceSwitcher collapsed={sidebarCollapsed} />

        <nav className={styles['sidebar-nav']}>
          {!sidebarCollapsed && <div className="yx-nav-section">{t('site.title')}</div>}
          {visibleMenuItems.map((item) => (
            <a
              key={item.key}
              className={`yx-nav-item${isItemActive(item) ? ' active' : ''}`}
              onClick={(e) => { e.preventDefault(); navigate(item.path!) }}
              style={{ cursor: 'pointer', textDecoration: 'none' }}
            >
              {renderNavIcon(item.icon)}
              {!sidebarCollapsed && <span>{t(item.label)}</span>}
            </a>
          ))}
        </nav>
      </aside>

      { }
      <div className={styles['main-area']}>
        { }
        <header className="yx-topbar">
          <div className="yx-breadcrumb">
            <HomeOutlined style={{ marginRight: 6 }} />
            <span className="current">{t(currentTitle) || t('site.title')}</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {userInfo && (
              <Dropdown
                menu={{
                  items: [
                    {
                      key: 'logout',
                      icon: <LogoutOutlined />,
                      label: t('auth.logout'),
                      onClick: handleLogout,
                    },
                  ],
                }}
                placement="bottomRight"
              >
                <div className={styles['user-avatar']}>
                  {(userInfo.realName || userInfo.username || 'U').charAt(0).toUpperCase()}
                </div>
              </Dropdown>
            )}
          </div>
        </header>

        { }
        <main className="yx-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
})

export default BasicLayout
