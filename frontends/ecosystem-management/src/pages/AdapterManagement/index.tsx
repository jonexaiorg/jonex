import React, { useState, useEffect, useCallback } from 'react'
import { Button, Tag, Spin, Result } from 'antd'
import {
  ThunderboltOutlined, ApiOutlined, CloudOutlined,
  SketchOutlined, CarryOutOutlined, BugOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { colors } from '@jonex/platform-theme/tokens'
import { listAdapters, type AdapterItem } from '../../api/adapters'
import './index.css'

const ADAPTER_DISPLAY: {
  type: string
  icon: React.ReactNode
  color: string
}[] = [
  { type: 'dingtalk', icon: <ThunderboltOutlined />, color: '#3b82f6' },
  { type: 'wechat_work', icon: <ApiOutlined />, color: '#8b5cf6' },
  { type: 'feishu', icon: <CloudOutlined />, color: '#94a3b8' },
]

const FALLBACK_ICONS: { icon: React.ReactNode; color: string }[] = [
  { icon: <SketchOutlined />, color: '#94a3b8' },
  { icon: <CarryOutOutlined />, color: '#94a3b8' },
  { icon: <BugOutlined />, color: '#94a3b8' },
]

function getDisplay(idx: number) {
  return ADAPTER_DISPLAY[idx] || { icon: FALLBACK_ICONS[idx % 3].icon, color: FALLBACK_ICONS[idx % 3].color }
}

const STATUS_BADGE_MAP: Record<string, { labelKey: string; color: string }> = {
  connected: { labelKey: 'adapter.connected', color: 'success' },
  disconnected: { labelKey: 'adapter.disconnected', color: 'warning' },
  error: { labelKey: 'adapter.error', color: 'error' },
}

export default function AdapterManagement() {
  const { t } = useTranslation('business')
  const [adapters, setAdapters] = useState<AdapterItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadAdapters = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await listAdapters(0, 100)
      setAdapters(result.items)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('common.loadFailed'))
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => { loadAdapters() }, [loadAdapters])

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}><Spin size="large" /></div>
  }

  if (error) {
    return <Result status="error" title={t('common.loadFailed')} subTitle={error} extra={<Button type="primary" onClick={loadAdapters}>{t('common.retry')}</Button>} />
  }

  return (
    <div>
      <div className="yx-page-title">
        <h1 style={{ fontSize: 22, fontWeight: 700, color: colors.brandDark, margin: 0 }}>{t('adapter.list')}</h1>
      </div>
      <div className="adapter-grid">
        {adapters.map((adapter, idx) => {
          const display = getDisplay(idx)
          const badge = STATUS_BADGE_MAP[adapter.status] || { labelKey: adapter.status, color: 'default' }
          const isGrey = adapter.status !== 'connected'

          return (
            <div key={adapter.id} className={`adapter-card${isGrey ? ' grey' : ''}`}>
              {isGrey && <span className="future-tag">{t('common.comingSoon')}</span>}
              <div className="adapter-icon" style={{ background: isGrey ? '#94a3b8' : display.color }}>
                {display.icon}
              </div>
              <h3>{adapter.name}</h3>
              <div className="adapter-desc">
                {(adapter.config_json as Record<string, string>)?.description || adapter.adapter_type}
              </div>
              <div className="adapter-status">
                <Tag color={badge.color} style={{ marginBottom: 0 }}>{t(badge.labelKey)}</Tag>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}