import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Input, Button, Card, Tag, Space, Select } from 'antd';
import { SearchOutlined, StarFilled } from '@ant-design/icons';

const resultList = [
  { key: 'creditRisk', date: '2026-03-15', relevance: 96 },
  { key: 'insurancePricing', date: '2026-02-20', relevance: 92 },
  { key: 'medicalFraud', date: '2026-04-10', relevance: 88 },
  { key: 'financialCompliance', date: '2026-01-08', relevance: 85 },
  { key: 'supplyChainFinance', date: '2026-05-05', relevance: 82 },
];

const chipKeys = ['all', 'finRisk', 'medInsurance', 'smartManufacturing', 'eduTraining', 'legalRegulations'];

export default function DomainManagementSearch() {
  const { t, i18n } = useTranslation();
  const [query, setQuery] = useState(t('domainManagementSearch.defaultQuery'));
  const [activeChip, setActiveChip] = useState('all');
  const localizedResults = resultList.map((item) => ({
    ...item,
    title: t(`domainManagementSearch.demo.${item.key}.title`),
    source: t(`domainManagementSearch.demo.${item.key}.source`),
    snippet: t(`domainManagementSearch.demo.${item.key}.snippet`),
  }));

  useEffect(() => {
    setQuery(t('domainManagementSearch.defaultQuery'));
  }, [i18n.language, t]);

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('knowledgeSearch.pageTitle')}</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 14 }}>{t('domainManagementSearch.subtitle')}</p>
      </div>

      <Card style={{ borderRadius: 16, marginBottom: 24, textAlign: 'center' }} bodyStyle={{ padding: 32 }}>
        <div style={{ fontSize: 15, color: '#64748b' }}>{t('domainManagementSearch.searchDesc')}</div>
        <div style={{ display: 'flex', maxWidth: 700, margin: '16px auto 0', gap: 8 }}>
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t('domainManagementSearch.searchPlaceholder')}
            style={{ flex: 1, padding: '14px 20px', border: '2px solid #e2e8f0', borderRadius: 12, fontSize: 16 }}
            onPressEnter={() => {}}
          />
          <Button
            type="primary"
            style={{ padding: '14px 32px', borderRadius: 12, fontSize: 15, height: 'auto' }}
            icon={<SearchOutlined />}
          >
            {t('knowledgeSearch.search')}
          </Button>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center', marginTop: 16 }}>
          {chipKeys.map((ck) => (
            <Tag
              key={ck}
              style={{
                padding: '6px 16px',
                borderRadius: 20,
                fontSize: 13,
                cursor: 'pointer',
                border: `1px solid ${activeChip === ck ? '#3b82f6' : '#d1d5db'}`,
                background: activeChip === ck ? '#3b82f6' : '#fff',
                color: activeChip === ck ? '#fff' : '#64748b',
              }}
              onClick={() => setActiveChip(ck)}
            >
              {t(`domainManagementSearch.chip.${ck}`)}
            </Tag>
          ))}
        </div>
      </Card>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <span style={{ fontSize: 14, color: '#64748b' }}>
          {t('domainManagementSearch.resultSummary', { count: 42, time: '0.35' })}
        </span>
        <Select
          defaultValue="relevance"
          style={{ width: 160 }}
          options={[
            { value: 'relevance', label: t('domainManagementSearch.sortByRelevance') },
            { value: 'time', label: t('domainManagementSearch.sortByTime') },
          ]}
        />
      </div>

      {localizedResults.map((r, i) => (
        <Card
          key={i}
          style={{ borderRadius: 12, marginBottom: 12, border: '1px solid #e2e8f0' }}
          bodyStyle={{ padding: 20 }}
          hoverable
        >
          <h3 style={{ margin: '0 0 8px', fontSize: 16 }}>
            <a style={{ color: '#3b82f6' }}>{r.title}</a>
          </h3>
          <p style={{ margin: '0 0 12px', color: '#64748b', fontSize: 14, lineHeight: 1.6 }}>{r.snippet}</p>
          <div style={{ display: 'flex', gap: 16, fontSize: 12, color: '#94a3b8', alignItems: 'center' }}>
            <Tag style={{ background: '#f1f5f9', border: 'none' }}>{r.source}</Tag>
            <span>{r.date}</span>
            <span style={{ color: '#22c55e', fontWeight: 600 }}>
              <StarFilled style={{ fontSize: 10 }} />{' '}
              {t('domainManagementSearch.relevancePercent', { relevance: r.relevance })}
            </span>
          </div>
        </Card>
      ))}

      <div className="yx-pagination" style={{ marginTop: 16 }}>
        <span className="yx-page-btn disabled">‹</span>
        <span className="yx-page-btn active">1</span>
        <span className="yx-page-btn">2</span>
        <span className="yx-page-btn">3</span>
        <span className="yx-page-btn">4</span>
        <span className="yx-page-btn">5</span>
        <span className="yx-page-btn">›</span>
        <span className="yx-page-info">
          {t('domainManagementSearch.pagination', { total: '42', page: '1', pages: '9' })}
        </span>
      </div>
    </div>
  );
}
