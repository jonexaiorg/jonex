import React, { useState, useMemo } from 'react'
import { Card, Table, Tag, Button, Input, Select, Modal, message } from 'antd'
import { SearchOutlined, EyeOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { colors, radius } from '@jonex/platform-theme/tokens'
import type { TemplateScenario } from '../../types/catalog'

const initialScenarios: TemplateScenario[] = []

const STATUS_MAP: Record<string, { label: string; cls: string }> = {
  published: { label: '已发布', cls: 'active' },
  draft: { label: '草稿', cls: 'pending' },
}

export default function TemplateScenarios() {
  const [scenarios, setScenarios] = useState<TemplateScenario[]>(initialScenarios)
  const [search, setSearch] = useState('')
  const [domainFilter, setDomainFilter] = useState<string>('')
  const [detailModal, setDetailModal] = useState<TemplateScenario | null>(null)

  const domainNames = useMemo(() => [...new Set(scenarios.map((s) => s.domainName))], [scenarios])

  const filtered = useMemo(() => {
    return scenarios.filter((s) => {
      if (search && !s.name.includes(search) && !s.description.includes(search)) return false
      if (domainFilter && s.domainName !== domainFilter) return false
      return true
    })
  }, [scenarios, search, domainFilter])

  const handleDelete = (scenario: TemplateScenario) => {
    setScenarios((prev) => prev.filter((s) => s.id !== scenario.id))
    message.success('场景已删除')
  }

  const columns = [
    { title: '场景名称', dataIndex: 'name', key: 'name', width: 180 },
    {
      title: '所属领域',
      dataIndex: 'domainName',
      key: 'domainName',
      width: 160,
      render: (v: string) => <Tag>{v}</Tag>,
    },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '对象数', dataIndex: 'objectCount', key: 'objectCount', width: 80, align: 'center' as const },
    { title: '关系数', dataIndex: 'relationCount', key: 'relationCount', width: 80, align: 'center' as const },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (v: string) => <span className={`yx-status-badge ${STATUS_MAP[v]?.cls || v}`}>{STATUS_MAP[v]?.label || v}</span>,
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: unknown, record: TemplateScenario) => (
        <div className="yx-table-action">
          <Button size="small" type="link" icon={<EyeOutlined />} onClick={() => setDetailModal(record)}>
            查看
          </Button>
          <Button size="small" type="link" icon={<EditOutlined />}>
            编辑
          </Button>
          <Button size="small" type="link" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record)}>
            删除
          </Button>
        </div>
      ),
    },
  ]

  return (
    <div>
      <div className="yx-page-title">
        <h1 style={{ fontSize: 24, fontWeight: 700, color: colors.brandDark, marginBottom: 4 }}>模板领域场景</h1>
        <p style={{ color: colors.textMuted, margin: '4px 0 0', fontSize: 14 }}>管理各领域模板下的应用场景</p>
      </div>

      <div className="yx-toolbar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 12 }}>
          <Input
            className="yx-search-box"
            placeholder="搜索场景名称或描述"
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
            style={{ width: 200 }}
            options={domainNames.map((d) => ({ label: d, value: d }))}
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

      <Modal
        title="场景详情"
        open={!!detailModal}
        onCancel={() => setDetailModal(null)}
        footer={null}
      >
        {detailModal && (
          <div>
            <p style={{ marginBottom: 8 }}><strong>场景名称:</strong> {detailModal.name}</p>
            <p style={{ marginBottom: 8 }}><strong>所属领域:</strong> <Tag>{detailModal.domainName}</Tag></p>
            <p style={{ marginBottom: 8 }}><strong>描述:</strong> {detailModal.description}</p>
            <p style={{ marginBottom: 8 }}><strong>对象数量:</strong> {detailModal.objectCount}</p>
            <p style={{ marginBottom: 8 }}><strong>关系数量:</strong> {detailModal.relationCount}</p>
            <p style={{ marginBottom: 8 }}>
              <strong>状态:</strong>{' '}
              <span className={`yx-status-badge ${STATUS_MAP[detailModal.status]?.cls || detailModal.status}`}>
                {STATUS_MAP[detailModal.status]?.label || detailModal.status}
              </span>
            </p>
          </div>
        )}
      </Modal>
    </div>
  )
}
