import React from 'react'
import { Tag } from 'antd'
import { useTranslation } from 'react-i18next'
import { ShopOutlined, BlockOutlined, InboxOutlined, CodepenOutlined, NodeIndexOutlined } from '@ant-design/icons'

const previewCards = [
  { icon: <BlockOutlined />, titleKey: 'businessMarketplace.domainTemplates', descKey: 'businessMarketplace.domainTemplatesDesc' },
  { icon: <InboxOutlined />, titleKey: 'businessMarketplace.knowledgePackages', descKey: 'businessMarketplace.knowledgePackagesDesc' },
  { icon: <CodepenOutlined />, titleKey: 'businessMarketplace.pretrainedModels', descKey: 'businessMarketplace.pretrainedModelsDesc' },
  { icon: <NodeIndexOutlined />, titleKey: 'businessMarketplace.industrySolutions', descKey: 'businessMarketplace.industrySolutionsDesc' },
]

export default function BusinessMarketplace() {
  const { t } = useTranslation()
  return (
    <div>
      <div style={{ textAlign: 'center', padding: '60px 20px' }}>
        <ShopOutlined style={{ fontSize: 72, color: '#3b82f6', opacity: 0.3, marginBottom: 20, display: 'block' }} />
        <h2 style={{ fontSize: 28, color: '#1e293b', margin: '0 0 8px' }}>{t('businessMarketplace.title')}</h2>
        <p style={{ color: '#94a3b8', fontSize: 15, margin: '0 0 40px' }}>{t('businessMarketplace.comingSoonMessage')}</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 20 }}>
          {previewCards.map((c, i) => (
            <div key={i} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 12, padding: 24, textAlign: 'center', opacity: 0.5 }}>
              <div style={{ fontSize: 36, color: '#94a3b8', marginBottom: 12 }}>{c.icon}</div>
              <h4 style={{ margin: '0 0 6px', fontSize: 15, color: '#64748b' }}>{t(c.titleKey)}</h4>
              <p style={{ margin: 0, fontSize: 13, color: '#94a3b8' }}>{t(c.descKey)}</p>
              <Tag style={{ marginTop: 10, background: '#f1f5f9', color: '#94a3b8', border: 'none' }}>{t('common.comingSoon')}</Tag>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
