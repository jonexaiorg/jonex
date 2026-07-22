import React, { useState, useMemo } from 'react'
import { Card, Table, Tag, Input, Select } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import { colors, radius } from '@jonex/platform-theme/tokens'
import type { TemplateRelation } from '../../types/catalog'

const initialRelations: TemplateRelation[] = []

export default function TemplateRelations() {
  const [relations] = useState<TemplateRelation[]>(initialRelations)
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
    { title: '关系名称', dataIndex: 'name', key: 'name', width: 140 },
    { title: '源对象', dataIndex: 'sourceObject', key: 'sourceObject', width: 120, render: (v: string) => <Tag color="blue">{v}</Tag> },
    { title: '目标对象', dataIndex: 'targetObject', key: 'targetObject', width: 120, render: (v: string) => <Tag color="green">{v}</Tag> },
    { title: '关系类型', dataIndex: 'relationType', key: 'relationType', width: 90, align: 'center' as const },
    { title: '约束说明', dataIndex: 'constraints', key: 'constraints', ellipsis: true },
  ]

  return (
    <div>
      <div className="yx-page-title">
        <h1 style={{ fontSize: 24, fontWeight: 700, color: colors.brandDark, marginBottom: 4 }}>模板关系管理</h1>
        <p style={{ color: colors.textMuted, margin: '4px 0 0', fontSize: 14 }}>管理模板中对象之间的关系定义</p>
      </div>

      <div className="yx-toolbar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 12 }}>
          <Input
            className="yx-search-box"
            placeholder="搜索关系名称、源对象或目标对象"
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            allowClear
            style={{ width: 320 }}
          />
          <Select
            placeholder="按关系类型筛选"
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
