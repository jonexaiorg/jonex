import React, { useEffect, useState } from 'react'
import { Card, Row, Col, Spin, Alert, Typography, Input, Tag } from 'antd'
import {
  SearchOutlined,
  HomeOutlined,
  SettingOutlined,
  GlobalOutlined,
  AppstoreAddOutlined,
  ClockCircleOutlined,
  FireOutlined,
} from '@ant-design/icons'
import { fetchAppManifest, getEnabledApps } from '../../api/manifest'
import { getUser } from '../../api/auth'
import type { AppManifest, AppManifestEntry } from '@jonex/shell-sdk'
import { colors, radius, shadows } from '@jonex/platform-theme/tokens'

const { Title, Paragraph, Text } = Typography

const CATEGORY_QUICK_ICONS: Record<string, React.ReactNode> = {
  'core-business': <HomeOutlined />,
  'platform-management': <SettingOutlined />,
  'ecosystem-management': <GlobalOutlined />,
}

const CATEGORY_QUICK_LABELS: Record<string, string> = {
  'core-business': '核心业务',
  'platform-management': '平台管理',
  'ecosystem-management': '生态管理',
}

const DOMAIN_OPTIONS = [
  { key: 'medical', label: '医疗健康', active: true },
  { key: 'finance', label: '金融科技', active: true },
  { key: 'education', label: '教育培训', active: true },
  { key: 'manufacture', label: '智能制造', active: true },
  { key: 'retail', label: '零售电商', active: true },
  { key: 'energy', label: '能源环保', active: false },
  { key: 'law', label: '法律合规', active: false },
]

interface SearchHistoryItem {
  query: string
  domain: string
  time: string
  results: number
}

const searchHistory: SearchHistoryItem[] = []

export default function Dashboard() {
  const [manifest, setManifest] = useState<AppManifest | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchValue, setSearchValue] = useState('')

  useEffect(() => {
    fetchAppManifest()
      .then(setManifest)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 120 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: 48 }}>
        <Alert type="warning" message="加载应用清单失败" description={error} showIcon />
      </div>
    )
  }

  const user = getUser()
  const userRoles: string[] = (
    user?.roles
    ?? ((user as any)?.role ? [(user as any).role as string] : [])
  )

  const apps: AppManifestEntry[] = manifest ? getEnabledApps(manifest, userRoles) : []

  return (
    <div>
      {/* Hero Search Area */}
      <div style={{
        background: colors.white,
        borderRadius: radius.card,
        padding: '36px 40px',
        marginBottom: 24,
        boxShadow: shadows.card,
        border: `1px solid ${colors.borderLight}`,
      }}>
        <div style={{ marginBottom: 8 }}>
          <Title level={3} style={{ marginBottom: 4, color: colors.brandDark, fontSize: 22 }}>
            {user ? `${user.displayName || user.username}，欢迎使用Jonex平台` : '欢迎使用Jonex平台'}
          </Title>
          <Text type="secondary" style={{ fontSize: 14 }}>
            知识数据平台 · 智能检索 · 知识管理 · 数据接入
          </Text>
        </div>

        {/* Search Input */}
        <div style={{ margin: '20px 0 16px' }}>
          <div style={{
            display: 'flex', alignItems: 'center',
            background: colors.white,
            border: `1px solid ${colors.border}`,
            borderRadius: radius.btn,
            padding: '4px 4px 4px 16px',
            maxWidth: 680,
            transition: 'border-color 0.2s, box-shadow 0.2s',
            boxShadow: 'none',
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = colors.accent
            e.currentTarget.style.boxShadow = shadows.searchFocus
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = colors.border
            e.currentTarget.style.boxShadow = 'none'
          }}
          >
            <SearchOutlined style={{ color: colors.textMuted, fontSize: 16 }} />
            <input
              type="text"
              placeholder="输入关键词检索知识、文档、数据源..."
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              style={{
                border: 'none', outline: 'none', padding: '10px 12px',
                fontSize: 14, color: colors.textPrimary, background: 'transparent',
                flex: 1, minWidth: 300,
              }}
            />
            <button style={{
              padding: '9px 24px', borderRadius: radius.btn,
              background: colors.accent, color: '#fff', border: 'none',
              fontSize: 14, fontWeight: 500, cursor: 'pointer',
              transition: 'background 0.2s',
            }}>
              检索
            </button>
          </div>
        </div>

        {/* Domain Quick Select */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 13, color: colors.textMuted, marginRight: 4 }}>业务领域：</span>
          {DOMAIN_OPTIONS.map((d) => (
            <button
              key={d.key}
              style={{
                padding: '4px 14px', borderRadius: radius.tag,
                border: `1px solid ${d.active ? colors.accentSoft : colors.border}`,
                background: d.active ? colors.infoBg : colors.white,
                color: d.active ? colors.accent : colors.textMuted,
                fontSize: 12, fontWeight: 500, cursor: d.active ? 'pointer' : 'default',
                opacity: d.active ? 1 : 0.6,
                transition: 'all 0.2s',
              }}
            >
              {d.label}
              {!d.active && <span style={{ marginLeft: 4, fontSize: 10 }}>即将开放</span>}
            </button>
          ))}
        </div>
      </div>

      <Row gutter={24}>
        {/* History */}
        <Col xs={24} lg={14}>
          <Card
            style={{ borderRadius: radius.card, marginBottom: 24 }}
            styles={{ body: { padding: 0 } }}
          >
            <div style={{ padding: '20px 24px 16px', borderBottom: `1px solid ${colors.borderTable}` }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 16, fontWeight: 600, color: colors.brandDark }}>
                  <ClockCircleOutlined style={{ marginRight: 8, color: colors.accent }} />
                  最近检索
                </span>
                <span style={{ fontSize: 13, color: colors.accent, cursor: 'pointer' }}>查看全部</span>
              </div>
            </div>
            <div style={{ padding: '8px 24px 16px' }}>
              {searchHistory.length === 0 ? (
                <div className="yx-empty-state">
                  <p style={{ fontSize: 14 }}>暂无检索记录</p>
                </div>
              ) : (
                searchHistory.map((item, idx) => (
                  <div
                    key={idx}
                    className="yx-result-card"
                    style={{ cursor: 'pointer' }}
                  >
                    <h4>{item.query}</h4>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <span className="source">
                        领域：{item.domain} · 返回 {item.results} 条结果
                      </span>
                      <span style={{ fontSize: 12, color: colors.textMuted }}>{item.time}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </Col>

        {/* Quick Entry & Stats */}
        <Col xs={24} lg={10}>
          <Card
            style={{ borderRadius: radius.card, marginBottom: 24 }}
            styles={{ body: { padding: '20px 24px' } }}
          >
            <div style={{ marginBottom: 16 }}>
              <span style={{ fontSize: 16, fontWeight: 600, color: colors.brandDark }}>
                <FireOutlined style={{ marginRight: 8, color: colors.accent }} />
                快速进入
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {apps
                .map((app) => {
                  const icon = CATEGORY_QUICK_ICONS[app.category || ''] || <AppstoreAddOutlined />
                  return (
                    <a
                      key={app.id}
                      href={`/apps/${app.id}`}
                      onClick={(e) => {
                        e.preventDefault()
                        window.location.href = `/apps/${app.id}`
                      }}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 12,
                        padding: '14px 16px',
                        background: colors.rowHover,
                        borderRadius: radius.btn,
                        textDecoration: 'none',
                        color: colors.textPrimary,
                        transition: 'all 0.2s',
                        border: `1px solid transparent`,
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = colors.infoBg
                        e.currentTarget.style.borderColor = colors.borderAccent
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = colors.rowHover
                        e.currentTarget.style.borderColor = 'transparent'
                      }}
                    >
                      <span style={{
                        width: 36, height: 36, borderRadius: 8,
                        background: `linear-gradient(135deg, ${colors.accentSoft}, ${colors.accent})`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: '#fff', fontSize: 16,
                      }}>
                        {icon}
                      </span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 14, fontWeight: 500 }}>{app.name}</div>
                        <div style={{ fontSize: 12, color: colors.textMuted }}>{app.description || ''}</div>
                      </div>
                      <span style={{ color: colors.accent, fontSize: 18 }}>→</span>
                    </a>
                  )
                })}
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
