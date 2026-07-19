import React from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { Row, Col } from 'antd'
import { ApiOutlined, ShopOutlined } from '@ant-design/icons'

const actions = [
  { labelKey: 'adapter.title', descKey: 'home.adapterDesc', path: '/adapter-management', icon: <ApiOutlined />, color: '#3b82f6' },
  { labelKey: 'businessMarketplace.title', descKey: 'home.marketplaceDesc', path: '/business-marketplace', icon: <ShopOutlined />, color: '#10b981', future: true },
]

export default function Home() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('home.title')}</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 14 }}>{t('home.subtitle')}</p>
      </div>
      <Row gutter={[16, 16]}>
        {actions.map((a) => (
          <Col xs={24} sm={12} key={a.labelKey}>
            <a onClick={() => navigate(a.path)} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '18px 20px', background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', textDecoration: 'none', cursor: 'pointer', transition: 'all 0.2s', opacity: a.future ? 0.6 : 1 }}>
              <span style={{ fontSize: 22, color: a.color, background: `${a.color}15`, width: 44, height: 44, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{a.icon}</span>
              <div><div style={{ fontSize: 14, fontWeight: 500, color: '#1e293b' }}>{t(a.labelKey)}{a.future ? ` (${t('common.comingSoon')})` : ''}</div><div style={{ fontSize: 12, color: '#94a3b8' }}>{t(a.descKey)}</div></div>
            </a>
          </Col>
        ))}
      </Row>
    </div>
  )
}
