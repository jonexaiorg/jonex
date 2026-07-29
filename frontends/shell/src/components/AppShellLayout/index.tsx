import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { Button, Layout, Dropdown } from 'antd';
import { useTranslation } from 'react-i18next';
import { LogoutOutlined, MenuFoldOutlined, MenuUnfoldOutlined, HomeOutlined, RightOutlined } from '@ant-design/icons';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { getUser, logout } from '../../api/auth';
import { fetchAppManifest, getEnabledApps } from '../../api/manifest';
import SpaceSwitcher from '../SpaceSwitcher';
import LocaleSwitcher from '../LocaleSwitcher';
import type { AppManifestEntry } from '@jonex/shell-sdk';
import { colors } from '@jonex/platform-theme/tokens';
import { prototypeNavConfig } from '../../navigation/prototypeNav.config';
import { getExpandedKeys, getBreadcrumbItems } from '../../navigation/navUtils';
import type { PrototypeNavItem, NavSection } from '../../navigation/navTypes';
import { userDisplayName } from '../../utils/userDisplay';

export default function AppShellLayout({ children }: { children: React.ReactNode }) {
  const { t, i18n } = useTranslation();
  const [user] = useState(() => getUser());
  const navigate = useNavigate();
  const location = useLocation();
  const [apps, setApps] = useState<AppManifestEntry[]>([]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);

  const userRoles = useMemo<string[]>(() => {
    return user?.roles ?? ((user as any)?.role ? [(user as any).role as string] : []);
  }, [user]);

  useEffect(() => {
    fetchAppManifest()
      .then((manifest) => {
        setApps(getEnabledApps(manifest, userRoles));
      })
      .catch(() => {});
  }, [userRoles]);

  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
  useEffect(() => {
    if (isMobile) setSidebarCollapsed(true);
  }, [isMobile]);

  // Auto-expand groups based on current route
  useEffect(() => {
    const keys = getExpandedKeys(location.pathname);
    setExpandedKeys((prev) => {
      const merged = new Set([...prev, ...keys]);
      return Array.from(merged);
    });
  }, [location.pathname]);

  const toggleGroup = useCallback((key: string) => {
    setExpandedKeys((prev) => (prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]));
  }, []);

  const isItemActive = (item: PrototypeNavItem): boolean => {
    if (!item.appId || !item.internalPath) return false;
    const expected = `/apps/${item.appId}/${item.internalPath}`;
    if (location.pathname === expected || location.pathname.startsWith(expected + '/')) {
      return true;
    }
    // 同时检查 matchPaths 中的额外路径
    if (item.matchPaths) {
      return item.matchPaths.some(({ appId, internalPath }) => {
        const p = `/apps/${appId}/${internalPath}`;
        return location.pathname === p || location.pathname.startsWith(p + '/');
      });
    }
    return false;
  };

  const isAnyChildActive = (item: PrototypeNavItem): boolean => {
    if (item.children) {
      return item.children.some((c) => isItemActive(c));
    }
    return isItemActive(item);
  };

  const isGroupExpanded = (key: string): boolean => expandedKeys.includes(key);

  const navigateToItem = (item: PrototypeNavItem) => {
    if (item.appId && item.internalPath) {
      navigate(`/apps/${item.appId}/${item.internalPath}`);
    }
  };

  const currentAppId = useMemo(() => {
    const match = location.pathname.match(/^\/apps\/([^/]+)/);
    return match ? match[1] : null;
  }, [location.pathname]);

  const userMenuItems = {
    items: [
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: t('auth.logout'),
        onClick: () => {
          logout();
          navigate('/login');
        },
      },
    ],
  };

  const breadcrumbItems = useMemo(() => getBreadcrumbItems(location.pathname), [location.pathname]);

  const sidebarWidth = sidebarCollapsed ? 64 : 240;

  const renderNavIcon = (Icon: React.ComponentType | undefined, className?: string) => {
    if (!Icon) return <span className={className || 'yx-sub-dot'} />;
    return (
      <span className={className || 'yx-nav-icon'}>
        <Icon />
      </span>
    );
  };

  const renderNavItem = (item: PrototypeNavItem, isSubItem = false) => {
    const ItemTag = isSubItem ? 'div' : 'a';
    const active = isItemActive(item);

    if (isSubItem) {
      const hasTag = !!item.tag;
      return (
        <div
          key={item.key}
          className={`yx-sub-item${active ? ' active' : ''}`}
          onClick={() => navigateToItem(item)}
          style={{ cursor: 'pointer' }}
        >
          <span className="yx-sub-dot" />
          <span>{t(item.label)}</span>
          {item.tag && <span className="yx-tag-future">{item.tag}</span>}
        </div>
      );
    }

    return (
      <a
        key={item.key}
        className={`yx-nav-item${active ? ' active' : ''}`}
        onClick={(e) => {
          e.preventDefault();
          navigateToItem(item);
        }}
        style={{ cursor: 'pointer', textDecoration: 'none' }}
      >
        {renderNavIcon(item.icon as React.ComponentType)}
        {!sidebarCollapsed && <span>{t(item.label)}</span>}
        {!sidebarCollapsed && item.tag && <span className="yx-tag-future">{t(item.tag)}</span>}
      </a>
    );
  };

  const renderNavGroup = (item: PrototypeNavItem) => {
    const expanded = isGroupExpanded(item.key);
    const hasActiveChild = isAnyChildActive(item);

    return (
      <div key={item.key} className={`yx-nav-group${expanded ? ' open' : ''}`}>
        <div
          className={`yx-nav-group-header${hasActiveChild && !expanded ? ' active' : ''}`}
          onClick={() => toggleGroup(item.key)}
        >
          {renderNavIcon(item.icon as React.ComponentType)}
          {!sidebarCollapsed && <span>{t(item.label)}</span>}
          {!sidebarCollapsed && <RightOutlined className="yx-nav-arrow" />}
        </div>
        <div className="yx-sub-menu">
          {item.children?.filter((child) => !child.hidden).map((child) => renderNavItem(child, true))}
        </div>
      </div>
    );
  };

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Sidebar */}
      <aside className="yx-sidebar" style={{ width: sidebarWidth }}>
        <div
          style={{
            padding: sidebarCollapsed ? '16px 0' : '24px 20px 20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
            borderBottom: `1px solid ${colors.sidebarBorder}`,
          }}
        >
          <Link
            to="/apps/core-business/knowledge-search"
            style={{
              textDecoration: 'none',
              color: 'inherit',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <img
              src={sidebarCollapsed ? '/favicon.png' : i18n.language === 'en' ? '/logo-en.svg' : '/logo.svg'}
              alt="Jonex"
              style={{
                height: sidebarCollapsed ? 36 : 32,
                transition: 'height 0.2s',
              }}
            />
          </Link>
        </div>

        <SpaceSwitcher collapsed={sidebarCollapsed} />

        <nav style={{ flex: 1, overflowY: 'auto', padding: '12px 0' }}>
          {prototypeNavConfig.map((section) => (
            <div key={section.key} style={{ marginBottom: 4 }}>
              {!sidebarCollapsed && <div className="yx-nav-section">{t(section.label)}</div>}
              {section.items
                .filter((item) => {
                  if (item.hidden) return false;
                  // 组内全部隐藏则组也不显示
                  if (item.children?.length && item.children.every((c) => c.hidden)) return false;
                  return true;
                })
                .map((item) => (item.children ? renderNavGroup(item) : renderNavItem(item)))}
            </div>
          ))}
        </nav>
      </aside>

      {/* Main Area */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
        }}
      >
        {/* Topbar */}
        <header className="yx-topbar">
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <Button
              type="text"
              icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setSidebarCollapsed((prev) => !prev)}
              style={{ fontSize: 18, width: 36, height: 36 }}
            />
            <div className="yx-breadcrumb">
              {breadcrumbItems.map((item, i) => (
                <span key={i}>
                  {i > 0 && <span style={{ margin: '0 6px', color: colors.textMuted }}>/</span>}
                  {item.path && item.path !== '#' ? (
                    <a
                      href={item.path}
                      onClick={(e) => {
                        e.preventDefault();
                        navigate(item.path);
                      }}
                      style={{
                        color: i === breadcrumbItems.length - 1 ? colors.brandBlue : colors.textSecondary,
                        textDecoration: 'none',
                        fontWeight: i === breadcrumbItems.length - 1 ? 600 : 400,
                      }}
                    >
                      {i === 0 && (
                        <>
                          <HomeOutlined style={{ marginRight: 4 }} />
                        </>
                      )}
                      {t(item.title)}
                    </a>
                  ) : (
                    <span
                      style={{
                        color: i === breadcrumbItems.length - 1 ? colors.brandBlue : colors.textSecondary,
                        fontWeight: i === breadcrumbItems.length - 1 ? 600 : 400,
                      }}
                    >
                      {i === 0 && (
                        <>
                          <HomeOutlined style={{ marginRight: 4 }} />
                        </>
                      )}
                      {t(item.title)}
                    </span>
                  )}
                </span>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
            <LocaleSwitcher />
            {/* TODO: 搜索和通知功能暂未实现，先隐藏 */}

            {user && (
              <Dropdown menu={userMenuItems} placement="bottomRight">
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    cursor: 'pointer',
                    padding: '4px 12px 4px 4px',
                    borderRadius: 10,
                  }}
                >
                  <div
                    style={{
                      width: 34,
                      height: 34,
                      borderRadius: 9,
                      background: `linear-gradient(135deg, ${colors.accent}, ${colors.brandBlue})`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#fff',
                      fontSize: 14,
                      fontWeight: 600,
                    }}
                  >
                    {userDisplayName(user, t).charAt(0).toUpperCase()}
                  </div>
                  {!sidebarCollapsed && (
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span
                        style={{
                          fontSize: 14,
                          fontWeight: 500,
                          color: colors.textPrimary,
                        }}
                      >
                        {userDisplayName(user, t)}
                      </span>
                      <span style={{ fontSize: 12, color: colors.textMuted }}>{t('auth.admin')}</span>
                    </div>
                  )}
                </div>
              </Dropdown>
            )}
          </div>
        </header>

        {/* Content */}
        <main className="yx-content">{children}</main>
      </div>
    </div>
  );
}
