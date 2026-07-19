import React, { useState, useMemo } from 'react'
import { Card, Table, Tag, Input, Select } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { colors, radius } from '@jonex/platform-theme/tokens'
import type { TemplateRelation } from '../../data/mock'
import { MOCK_TEMPLATE_RELATIONS } from '../../data/mock'

export default function TemplateRelations() {
  const { t } = useTranslation()
  const [relations] = useState<TemplateRelation[]>(MOCK_TEMPLATE_RELATIONS)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<string>('')

  const relationTypes = useMemo(() => [...new Set(relations.map((r) => r.relationType))], [relations])

  const filtered = useMemo(() => {
    return relations.filter((r) => {
      if (search && !r.name.includes(search) && !r.sourceObject.includes(search) && !r.targetObject.includes(search)) return false
      if (typeFilter && r.relationType !== typeFilter) return false
      return true
    })
  }, [relations, search, typeFilter])

  const columns = [
    { title: t('templateRelation.name'), dataIndex: 'name', key: 'name', width: 140 },
    { title: t('templateRelation.source'), dataIndex: 'sourceObject', key: 'sourceObject', width: 120, render: (v: string) => <Tag color="blue">{v}</Tag> },
    { title: t('templateRelation.target'), dataIndex: 'targetObject', key: 'targetObject', width: 120, render: (v: string) => <Tag color="green">{v}</Tag> },
    { title: t('templateRelation.type'), dataIndex: 'relationType', key: 'relationType', width: 90, align: 'center' as const },
    { title: t('templateRelation.constraints'), dataIndex: 'constraints', key: 'constraints', ellipsis: true },
  ]

  return (
    <div>
      <div className="yx-page-title">
        <h1 style={{ fontSize: 24, fontWeight: 700, color: colors.brandDark, marginBottom: 4 }}>{t('templateRelation.title')}</h1>
        <p style={{ color: colors.textMuted, margin: '4px 0 0', fontSize: 14 }}>{t('templateRelation.subtitle')}</p>
      </div>

      <div className="yx-toolbar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 12 }}>
          <Input
            className="yx-search-box"
            placeholder={t('templateRelation.searchPlaceholder')}
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            allowClear
            style={{ width: 320 }}
          />
          <Select
            placeholder={t('templateRelation.filterType')}
            value={typeFilter || undefined}
            onChange={(v) => setTypeFilter(v || '')}
            allowClear
            style={{ width: 160 }}
            options={relationTypes.map((t) => ({ label: t, value: t }))}
          />
        </div>
      </div>

      <Card style={{ borderRadius: radius.card }}>
        <Table
          dataSource={filtered}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  )
}
