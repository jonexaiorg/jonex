import React from 'react'
import { Input, Button, Switch, Tag, message } from 'antd'
import {
  SearchOutlined,
  CloudUploadOutlined,
  ApiOutlined,
  CloudServerOutlined,
  DatabaseOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { colors, radius } from '@jonex/platform-theme/tokens'
import type { DataAccessMethod } from '../../types/management'

const initialMethods: DataAccessMethod[] = []

const iconMap: Record<string, React.ReactNode> = {
  file: <CloudUploadOutlined />,
  api: <ApiOutlined />,
  storage: <CloudServerOutlined />,
  database: <DatabaseOutlined />,
}

const typeLabel: Record<string, string> = {
  file: '文件上传',
  api: 'API 同步',
  storage: '对象存储',
  database: '数据库',
}

export default function DataAccess() {
  const [search, setSearch] = React.useState('')
  const [methods, setMethods] = React.useState<DataAccessMethod[]>(initialMethods)

  const handleToggle = (id: string, enabled: boolean) => {
    setMethods((prev) => prev.map((m) => (m.id === id ? { ...m, enabled } : m)))
    message.success(enabled ? '已启用' : '已禁用')
  }

  const filtered = methods.filter(
    (m) =>
      m.name.includes(search) ||
      m.description.includes(search) ||
      typeLabel[m.type].includes(search),
  )

  return (
    <div>
      <div className="yx-page-title">
        <h1>数据接入方式</h1>
        <p style={{ color: colors.textSecondary, margin: '4px 0 0', fontSize: 14 }}>
          配置平台数据接入方式，管理数据源连接
        </p>
      </div>

      <div className="yx-toolbar" style={{ marginBottom: 20 }}>
        <Input
          prefix={<SearchOutlined />}
          placeholder="搜索接入方式..."
          style={{ width: 280 }}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="yx-config-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 20 }}>
        {filtered.map((m) => (
          <div
            key={m.id}
            style={{
              background: colors.white,
              border: `1px solid ${colors.border}`,
              borderRadius: radius.card,
              padding: 24,
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: 12,
                  background: m.enabled ? `${colors.accent}18` : `${colors.textMuted}18`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 22,
                  color: m.enabled ? colors.accent : colors.textMuted,
                }}
              >
                {iconMap[m.type]}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: 15, color: colors.textPrimary }}>{m.name}</div>
                <div style={{ fontSize: 12, color: colors.textMuted, marginTop: 2 }}>
                  <Tag style={{ fontSize: 11 }}>{typeLabel[m.type]}</Tag>
                </div>
              </div>
              <Switch
                checked={m.enabled}
                onChange={(checked) => handleToggle(m.id, checked)}
              />
            </div>
            <p style={{ color: colors.textSecondary, fontSize: 13, margin: 0, lineHeight: 1.6 }}>{m.description}</p>
            <div style={{ display: 'flex', gap: 8 }}>
              {m.enabled && (
                <Button size="small" icon={<SettingOutlined />}>
                  配置
                </Button>
              )}
              {!m.enabled && (
                <Button size="small" disabled>
                  暂不可用
                </Button>
              )}
            </div>
          </div>
        ))}
        {filtered.length === 0 && (
          <div className="yx-empty-state" style={{ gridColumn: '1 / -1', textAlign: 'center', padding: 48, color: colors.textMuted }}>
            暂无匹配的数据接入方式
          </div>
        )}
      </div>
    </div>
  )
}
