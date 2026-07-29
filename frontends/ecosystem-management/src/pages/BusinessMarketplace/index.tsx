import React from 'react';
import { useTranslation } from 'react-i18next';
import { Tag } from 'antd';
import { ShopOutlined, BlockOutlined, InboxOutlined, CodepenOutlined, NodeIndexOutlined } from '@ant-design/icons';

const previewCards = [
  {
    icon: <BlockOutlined />,
    title: 'ecosystem.marketplaceDomainTemplates',
    desc: 'ecosystem.marketplaceDomainTemplatesDesc',
  },
  {
    icon: <InboxOutlined />,
    title: 'ecosystem.marketplaceKnowledgePackages',
    desc: 'ecosystem.marketplaceKnowledgePackagesDesc',
  },
  {
    icon: <CodepenOutlined />,
    title: 'ecosystem.marketplacePretrainedModels',
    desc: 'ecosystem.marketplacePretrainedModelsDesc',
  },
  {
    icon: <NodeIndexOutlined />,
    title: 'ecosystem.marketplaceIndustrySolutions',
    desc: 'ecosystem.marketplaceIndustrySolutionsDesc',
  },
];

export default function BusinessMarketplace() {
  const { t } = useTranslation();
  return (
    <div>
      <div style={{ textAlign: 'center', padding: '60px 20px' }}>
        <ShopOutlined style={{ fontSize: 72, color: '#3b82f6', opacity: 0.3, marginBottom: 20, display: 'block' }} />
        <h2 style={{ fontSize: 28, color: '#1e293b', margin: '0 0 8px' }}>
          {t('ecosystem.businessDomainMarketplace')}
        </h2>
        <p style={{ color: '#94a3b8', fontSize: 15, margin: '0 0 40px' }}>{t('ecosystem.marketplaceComingSoonDesc')}</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 20 }}>
          {previewCards.map((c, i) => (
            <div
              key={i}
              style={{
                background: '#fff',
                border: '1px solid #e2e8f0',
                borderRadius: 12,
                padding: 24,
                textAlign: 'center',
                opacity: 0.5,
              }}
            >
              <div style={{ fontSize: 36, color: '#94a3b8', marginBottom: 12 }}>{c.icon}</div>
              <h4 style={{ margin: '0 0 6px', fontSize: 15, color: '#64748b' }}>{t(c.title)}</h4>
              <p style={{ margin: 0, fontSize: 13, color: '#94a3b8' }}>{t(c.desc)}</p>
              <Tag style={{ marginTop: 10, background: '#f1f5f9', color: '#94a3b8', border: 'none' }}>
                {t('ecosystem.comingSoon')}
              </Tag>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
