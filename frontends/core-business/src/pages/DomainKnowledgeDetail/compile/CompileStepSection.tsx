import React from 'react'
import { useTranslation } from 'react-i18next'
import { Button, Table } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { OrderedListOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import type { CompileStep } from '@/types/domainKnowledge'
import { compileScopeTextMap, compileTriggerTextMap } from '@/types/domainKnowledge'

const cardStyle: React.CSSProperties = {
  background: '#fff', borderRadius: 14, border: '1px solid #eef2f6', padding: 24, marginBottom: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
}
const h3Style: React.CSSProperties = { margin: 0, fontSize: 15, fontWeight: 600, color: '#0b2b5c', display: 'flex', alignItems: 'center', gap: 8 }

interface Props {
  data: CompileStep[]
  loading: boolean
  onCreate: () => void
  onEdit: (s: CompileStep) => void
  onDelete: (s: CompileStep) => void
}

export default function CompileStepSection({ data, loading, onCreate, onEdit, onDelete }: Props) {
  const { t } = useTranslation()
  const columns: ColumnsType<CompileStep> = [
    { title: 'Step Order', dataIndex: 'order', key: 'order', width: 80, align: 'center', render: (v) => <span style={{ fontWeight: 600, color: '#0b2b5c' }}>{v}</span> },
    { title: 'Step Name', dataIndex: 'name', key: 'name', width: 110, render: (v) => <strong>{v}</strong> },
    { title: 'Description and Prompt', dataIndex: 'prompt', key: 'prompt', render: (v) => <span style={{ fontSize: 12, color: '#64748b' }}>{v}</span> },
    { title: 'Linked Skill', dataIndex: 'skill', key: 'skill', width: 130, render: (v: string) => v ? <span style={{ background: '#f5f3ff', color: '#7c3aed', padding: '2px 8px', borderRadius: 4, fontSize: 12 }}>{v}</span> : <span style={{ fontSize: 12, color: '#94a3b8' }}>—</span> },
    { title: 'Scope', dataIndex: 'scope', key: 'scope', width: 100, render: (v: CompileStep['scope']) => <span style={{ background: v === 'single' ? '#eff6ff' : '#ecfdf5', color: v === 'single' ? '#3b82f6' : '#059669', padding: '2px 8px', borderRadius: 4, fontSize: 12 }}>{t(compileScopeTextMap[v])}</span> },
    { title: 'Trigger', dataIndex: 'trigger', key: 'trigger', width: 160, render: (v: CompileStep['trigger']) => <span style={{ fontSize: 12, color: '#64748b' }}>{t(compileTriggerTextMap[v])}</span> },
    { title: 'Result Template', dataIndex: 'template', key: 'template', width: 180, render: (v) => <span style={{ fontSize: 12, color: '#64748b' }}>{v}</span> },
    {
      title: 'Actions', key: 'actions', width: 140,
      render: (_, r) => (
        <span>
          <a className="yx-table-action" onClick={() => onEdit(r)}><EditOutlined /> Edit</a>
          <a className="yx-table-action" style={{ color: '#ef4444' }} onClick={() => onDelete(r)}><DeleteOutlined /> Delete</a>
        </span>
      ),
    },
  ]
  return (
    <div className="config-section" style={cardStyle}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <h3 style={h3Style}><OrderedListOutlined style={{ color: '#f97316' }} /> Compile Step Settings</h3>
        <Button type="primary" icon={<PlusOutlined />} style={{ fontSize: 13 }} onClick={onCreate}>Create Step</Button>
      </div>
      <p style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16 }}>Define knowledge compilation steps. Steps run in ascending order.</p>
      <Table columns={columns} dataSource={data} rowKey="id" pagination={false} size="middle" loading={loading} locale={{ emptyText: 'No compilation steps. Select Create Step to add one.' }} />
    </div>
  )
}