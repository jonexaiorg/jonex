import React, { useState } from 'react'
import { Button, Card, Table, Tag, Input, Select, Space } from 'antd'
import { PlayCircleOutlined, SearchOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'

const getStatusColor = (t: (k: string) => string, status: string): string => {
  if (status === t('status.success')) return 'success'
  if (status === t('status.ongoing')) return 'processing'
  if (status === t('status.failed')) return 'error'
  return 'default'
}

export default function DomainKnowledgeCompileResults() {
  const { t } = useTranslation()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState(t('status.allStatus'))

  const compileList = [
    { kb: 'Financial Products Knowledge Base', version: 'v2.5.1', status: t('status.success'), entities: 12845, relations: 45672, duration: '3m 28s' },
    { kb: 'Medical Literature Knowledge Base', version: 'v2.4.0', status: t('status.success'), entities: 35621, relations: 128430, duration: '8m 15s' },
    { kb: 'Equipment Fault Knowledge Base', version: 'v1.9.2', status: t('status.ongoing'), entities: 8234, relations: 0, duration: '--' },
    { kb: 'Course Resources Knowledge Base', version: 'v2.1.0', status: t('status.success'), entities: 24310, relations: 89256, duration: '5m 42s' },
    { kb: 'Legal Regulations Knowledge Base', version: 'v3.0.1', status: t('status.failed'), entities: 0, relations: 0, duration: '1m 05s' },
  ]

  const columns = [
    { title: t('domainKnowledge.knowledgeBase'), dataIndex: 'kb', key: 'kb', width: 180, render: (v: string) => <a className="yx-table-action">{v}</a> },
    { title: t('domainKnowledge.compileVersion'), dataIndex: 'version', key: 'version', width: 100 },
    { title: t('domainService.status'), dataIndex: 'status', key: 'status', width: 90, render: (v: string) => <Tag color={getStatusColor(t, v)}>{v}</Tag> },
    { title: t('domainKnowledge.entityCount'), dataIndex: 'entities', key: 'entities', width: 100, render: (v: number) => v ? v.toLocaleString() : '--' },
    { title: t('domainKnowledge.relationCount'), dataIndex: 'relations', key: 'relations', width: 100, render: (v: number) => v ? v.toLocaleString() : '--' },
    { title: t('domainKnowledge.duration'), dataIndex: 'duration', key: 'duration', width: 100 },
    { title: t('knowledgeSearch.actions'), key: 'actions', width: 100, render: (_: any, r: any) => (
      <Space>
        <a className="yx-table-action">{t('domainKnowledge.detail')}</a>
        {r.status === t('status.success') ? <a className="yx-table-action">{t('domainKnowledge.rollback')}</a> : r.status === t('status.failed') ? <a className="yx-table-action">{t('domainKnowledge.retry')}</a> : null}
      </Space>
    )},
  ]

  const filtered = compileList.filter((c) =>
    c.kb.includes(search) && (statusFilter === t('status.allStatus') || c.status === statusFilter)
  )

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('knowledgeSearch.compileResults')}</h1>
      </div>

      <Card className="yx-card">
        <div className="yx-toolbar">
          <Input
            prefix={<SearchOutlined />} placeholder="Search knowledge bases..." value={search}
            onChange={(e) => setSearch(e.target.value)} style={{ width: 240 }}
          />
          <Select value={statusFilter} onChange={setStatusFilter} style={{ width: 140 }}
            options={[t('status.allStatus'), t('status.success'), t('status.ongoing'), t('status.failed')].map((s) => ({ value: s, label: s }))}
          />
          <Button type="primary" icon={<PlayCircleOutlined />}>{t('compile.title')}</Button>
        </div>
        <Table columns={columns} dataSource={filtered} rowKey="kb" pagination={{ total: 15, pageSize: 5 }} size="middle" />
      </Card>
    </div>
  )
}
