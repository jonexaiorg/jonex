import React, { useState, useMemo } from 'react'
import { Card, Table, Tag, Input, Select } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import { colors, radius } from '@jonex/platform-theme/tokens'
import type { TemplateObject } from '../../types/catalog'

const initialObjects: TemplateObject[] = []

const STATUS_MAP: Record<string, { label: string; cls: string }> = {
  active: { label: '启用', cls: 'active' },
  draft: { label: '草稿', cls: 'pending' },
}

export default function TemplateObjects() {
  const [objects] = useState<TemplateObject[]>(initialObjects)
  const [search, setSearch] = useState('')
  const [domainFilter, setDomainFilter] = useState<string>('')

  const domainNames = useMemo(() => [...new Set(objects.map((o) => o.domainName))], [objects])

  const filtered = useMemo(() => {
    return objects.filter((o) => {
      if (search && !o.name.includes(search)) return false
      if (domainFilter && o.domainName !== domainFilter) return false
      return true
    })
  }, [objects, search, domainFilter])

  const columns = [
    { title: '对象名称', dataIndex: 'name', key: 'name', width: 140 },
    {
      title: '所属领域',
      dataIndex: 'domainName',
      key: 'domainName',
      width: 120,
      render: (v: string) => <Tag>{v}</Tag>,
    },
    {
      title: '字段数',
      key: 'fieldCount',
      width: 80,
      align: 'center' as const,
      render: (_: unknown, record: TemplateObject) => record.fields.length,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (v: string) => <span className={`yx-status-badge ${STATUS_MAP[v]?.cls || v}`}>{STATUS_MAP[v]?.label || v}</span>,
    },
  ]

  return (
    <div>
      <div className="yx-page-title">
        <h1 style={{ fontSize: 24, fontWeight: 700, color: colors.brandDark, marginBottom: 4 }}>模板对象管理</h1>
        <p style={{ color: colors.textMuted, margin: '4px 0 0', fontSize: 14 }}>管理模板中的对象定义与字段配置</p>
      </div>

      <div className="yx-toolbar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 12 }}>
          <Input
            className="yx-search-box"
            placeholder="搜索对象名称"
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            allowClear
            style={{ width: 260 }}
          />
          <Select
            placeholder="按领域筛选"
            value={domainFilter || undefined}
            onChange={(v) => setDomainFilter(v || '')}
            allowClear
            style={{ width: 160 }}
            options={domainNames.map((d) => ({ label: d, value: d }))}
          />
        </div>
      </div>

      <Card style={{ borderRadius: radius.card }}>
        <Table
          dataSource={filtered}
          columns={columns}
          rowKey="id"
          expandable={{
            expandedRowRender: (record: TemplateObject) => (
              <div style={{ padding: '8px 0' }}>
                <h4 style={{ marginBottom: 8, fontSize: 13, color: colors.brandDark }}>字段定义</h4>
                <Table
                  dataSource={record.fields.map((f, i) => ({ ...f, key: i }))}
                  columns={[
                    { title: '字段名', dataIndex: 'name', key: 'name' },
                    { title: '类型', dataIndex: 'type', key: 'type', width: 100 },
                    {
                      title: '必填',
                      dataIndex: 'required',
                      key: 'required',
                      width: 80,
                      render: (v: boolean) => <Tag color={v ? 'red' : 'default'}>{v ? '必填' : '可选'}</Tag>,
                    },
                  ]}
                  rowKey="key"
                  pagination={false}
                  size="small"
                  showHeader={true}
                />
              </div>
            ),
            rowExpandable: () => true,
          }}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  )
}
