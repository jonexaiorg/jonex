import React, { useState, useEffect, useCallback } from 'react'
import { Spin, Result, Button } from 'antd'
import { useTranslation } from 'react-i18next'
import { CloudOutlined, FolderOpenOutlined, UploadOutlined, WifiOutlined, ApiOutlined } from '@ant-design/icons'
import { colors } from '@jonex/platform-theme/tokens'
import { listDataAccessMethods, type DataAccessItem } from '../../api/dataAccess'
import './index.css'

export default function DataAccess() {
  const { t } = useTranslation('business')
  const [items, setItems] = useState<DataAccessItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await listDataAccessMethods(0, 100)
      setItems(result.items)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('common.loadFailed'))
    } finally { setLoading(false) }
  }, [t])

  useEffect(() => { load() }, [load])

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}><Spin size="large" /></div>
  }
  if (error) {
    return <Result status="error" title={t('common.loadFailed')} subTitle={error} extra={<Button type="primary" onClick={load}>{t('common.retry')}</Button>} />
  }

  const TYPE_ICONS: Record<string, { icon: React.ReactNode; label: string; desc: string }> = {
    api: { icon: <CloudOutlined />, label: t('dataAccess.apiLabel'), desc: t('dataAccess.apiDesc') },
    api_push: { icon: <ApiOutlined />, label: t('dataAccess.apiPushLabel'), desc: t('dataAccess.apiPushDesc') },
    storage: { icon: <FolderOpenOutlined />, label: t('dataAccess.storageLabel'), desc: t('dataAccess.storageDesc') },
    file: { icon: <UploadOutlined />, label: t('dataAccess.fileLabel'), desc: t('dataAccess.fileDesc') },
    mqtt: { icon: <WifiOutlined />, label: t('dataAccess.mqttLabel'), desc: t('dataAccess.mqttDesc') },
  }

  return (
    <div>
      <div className="yx-page-title">
        <h1 style={{ fontSize: 22, fontWeight: 700, color: colors.brandDark, margin: 0 }}>{t('dataAccess.title')}</h1>
      </div>
      <div className="access-grid">
        {items.map((item) => {
          const cfg = TYPE_ICONS[item.access_type] || { icon: <CloudOutlined />, label: item.access_type, desc: '' }
          const isActive = item.status === 'active'

          return (
            <div key={item.id} className={`access-card${isActive ? ' active' : ' grey'}`}>
              <div className="icon-big">{cfg.icon}</div>
              <h3>{item.name}</h3>
              <p>{item.description || cfg.desc}</p>
              <span className="status-tag">
                {isActive ? <><span className="dot-green" /> {t('status.enabled')}</> : t('dataAccess.comingSoon')}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}