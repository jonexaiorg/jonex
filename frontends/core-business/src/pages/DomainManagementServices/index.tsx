import React, { useState } from 'react'
import { Input, Select, Button, Card, Table, Tag, Space } from 'antd'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'

const SERVICE_TYPES = ['all', 'search', 'inference', 'analysis'] as const
type ServiceType = (typeof SERVICE_TYPES)[number]

const MOCK_SERVICES = [
  { nameKey: 'smartQa', domainKey: 'financialRisk', type: 'inference', callType: 'REST API', status: 'running' },
  { nameKey: 'knowledgeRetrieval', domainKey: 'financialRisk', type: 'search', callType: 'gRPC', status: 'running' },
  { nameKey: 'medicalRecordAnalysis', domainKey: 'medicalInsurance', type: 'analysis', callType: 'REST API', status: 'running' },
  { nameKey: 'equipmentDiagnostics', domainKey: 'smartProduction', type: 'inference', callType: 'REST API', status: 'maintenance' },
  { nameKey: 'courseRecommendation', domainKey: 'onlineEducation', type: 'analysis', callType: 'gRPC', status: 'running' },
] as const

export default function DomainManagementServices() {
  const { t } = useTranslation('business')
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<ServiceType>('all')

  const services = MOCK_SERVICES.map((service) => ({
    ...service,
    name: t(`domainService.samples.services.${service.nameKey}`),
    domain: t(`domainService.samples.domains.${service.domainKey}`),
  }))

  const columns = [
    { title: t('domainService.name'), dataIndex: 'name', key: 'name', width: 160, render: (v: string) => <a className="yx-table-action">{v}</a> },
    { title: t('domainService.space'), dataIndex: 'domain', key: 'domain', width: 120 },
    { title: t('domainService.serviceType'), dataIndex: 'type', key: 'type', width: 110, render: (value: Exclude<ServiceType, 'all'>) => t(`domainService.serviceTypes.${value}`) },
    { title: t('domainService.callMethod'), dataIndex: 'callType', key: 'callType', width: 110 },
    { title: t('domainService.status'), dataIndex: 'status', key: 'status', width: 90, render: (value: string) => <Tag color={value === 'running' ? 'success' : 'warning'}>{t(value === 'running' ? 'domainEngine.running' : 'status.maintenance')}</Tag> },
    { title: t('knowledgeSearch.actions'), key: 'actions', width: 120, render: () => <Space><a className="yx-table-action">{t('domainService.edit')}</a><a className="yx-table-action">{t('domainService.monitor')}</a></Space> },
  ]

  const normalizedSearch = search.trim().toLocaleLowerCase()
  const filtered = services.filter((service) =>
    (!normalizedSearch || service.name.toLocaleLowerCase().includes(normalizedSearch))
    && (typeFilter === 'all' || service.type === typeFilter)
  )

  return (
    <div>
      <div className="yx-page-title"><h1>{t('domainService.serviceList')}</h1></div>

      <Card className="yx-card">
        <div className="yx-toolbar">
          <Input prefix={<SearchOutlined />} placeholder={t('domainService.searchServices')} value={search} onChange={(e) => setSearch(e.target.value)} style={{ width: 240 }} />
          <Select<ServiceType>
            value={typeFilter}
            onChange={setTypeFilter}
            style={{ width: 140 }}
            options={SERVICE_TYPES.map((value) => ({ value, label: t(`domainService.serviceTypes.${value}`) }))}
          />
          <Button type="primary" icon={<PlusOutlined />}>{t('domainService.create')}</Button>
        </div>
        <Table columns={columns} dataSource={filtered} rowKey="nameKey" pagination={{ total: filtered.length, pageSize: 5 }} size="middle" />
      </Card>
    </div>
  )
}
