import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Input, Button, Card, Tag } from 'antd'
import { SearchOutlined, StarFilled } from '@ant-design/icons'

const SEARCH_RESULTS = [
  { key: 'bankCreditRisk', date: '2026-03-15', relevance: 96 },
  { key: 'insurancePricing', date: '2026-02-20', relevance: 92 },
  { key: 'medicalFraud', date: '2026-04-10', relevance: 88 },
  { key: 'financialCompliance', date: '2026-01-08', relevance: 85 },
  { key: 'supplyChainFinance', date: '2026-05-05', relevance: 82 },
] as const

const DOMAIN_FILTERS = ['all', 'financialRisk', 'medicalInsurance', 'smartManufacturing', 'education', 'legal'] as const
type DomainFilter = (typeof DOMAIN_FILTERS)[number]

export default function DomainManagementSearch() {
  const { t } = useTranslation('business')
  const [query, setQuery] = useState('')
  const [activeFilter, setActiveFilter] = useState<DomainFilter>('all')

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('knowledgeSearch.title')}</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 14 }}>{t('knowledgeSearch.allDomainDesc')}</p>
      </div>

      <Card style={{ borderRadius: 16, marginBottom: 24, textAlign: 'center' }} styles={{ body: { padding: 32 } }}>
        <div style={{ fontSize: 15, color: '#64748b' }}>{t('domainService.searchIntro')}</div>
        <div style={{ display: 'flex', maxWidth: 700, margin: '16px auto 0', gap: 8 }}>
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t('domainService.searchContentPlaceholder')}
            style={{ flex: 1, padding: '14px 20px', border: '2px solid #e2e8f0', borderRadius: 12, fontSize: 16 }}
            onPressEnter={() => {}}
          />
          <Button type="primary" style={{ padding: '14px 32px', borderRadius: 12, fontSize: 15, height: 'auto' }} icon={<SearchOutlined />}>
            {t('domainService.searchAction')}
          </Button>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center', marginTop: 16 }}>
          {DOMAIN_FILTERS.map((filter) => (
            <Tag
              key={filter}
              style={{ padding: '6px 16px', borderRadius: 20, fontSize: 13, cursor: 'pointer', border: `1px solid ${activeFilter === filter ? '#3b82f6' : '#d1d5db'}`, background: activeFilter === filter ? '#3b82f6' : '#fff', color: activeFilter === filter ? '#fff' : '#64748b' }}
              onClick={() => setActiveFilter(filter)}
            >
              {t(`domainService.searchDomains.${filter}`)}
            </Tag>
          ))}
        </div>
      </Card>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <span style={{ fontSize: 14, color: '#64748b' }}>
          {t('domainService.searchResultSummary', { count: 42, seconds: '0.35' })}
        </span>
        <select aria-label={t('domainService.sortResults')} style={{ padding: '6px 12px', border: '1px solid #d1d5db', borderRadius: 6, fontSize: 13 }}>
          <option>{t('domainService.sortByRelevance')}</option>
          <option>{t('domainService.sortByTime')}</option>
        </select>
      </div>

      {SEARCH_RESULTS.map((result) => (
        <Card key={result.key} style={{ borderRadius: 12, marginBottom: 12, border: '1px solid #e2e8f0' }} styles={{ body: { padding: 20 } }} hoverable>
          <h3 style={{ margin: '0 0 8px', fontSize: 16 }}>
            <a style={{ color: '#3b82f6' }}>{t(`domainService.samples.searchResults.${result.key}.title`)}</a>
          </h3>
          <p style={{ margin: '0 0 12px', color: '#64748b', fontSize: 14, lineHeight: 1.6 }}>
            {t(`domainService.samples.searchResults.${result.key}.snippet`)}
          </p>
          <div style={{ display: 'flex', gap: 16, fontSize: 12, color: '#94a3b8', alignItems: 'center' }}>
            <Tag style={{ background: '#f1f5f9', border: 'none' }}>
              {t(`domainService.samples.searchResults.${result.key}.source`)}
            </Tag>
            <span>{result.date}</span>
            <span style={{ color: '#22c55e', fontWeight: 600 }}>
              <StarFilled style={{ fontSize: 10 }} /> {t('domainService.relevance', { value: result.relevance })}
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
        <span className="yx-page-info">{t('common.totalPage', { total: 42 })}</span>
      </div>
    </div>
  )
}
