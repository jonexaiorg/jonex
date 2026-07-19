import React from 'react'
import { useTranslation } from 'react-i18next'
import { Button, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { ControlOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import type { OntologyConstraint } from '@/types/domainKnowledge'
import { constraintTargetTypeTextMap, constraintTypeTextMap, normalizeConstraintType } from '@/types/domainKnowledge'

const cardStyle: React.CSSProperties = {
  background: '#fff',
  borderRadius: 14,
  border: '1px solid #eef2f6',
  padding: 24,
  marginBottom: 20,
  boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
}

const h3Style: React.CSSProperties = {
  margin: 0,
  fontSize: 15,
  fontWeight: 600,
  color: '#0b2b5c',
  display: 'flex',
  alignItems: 'center',
  gap: 8,
}

const TARGET_TYPE_TAG: Record<string, string> = {
  entity: 'blue',
  attribute: 'gold',
  relation: 'purple',
}

interface Props {
  data: OntologyConstraint[]
  loading: boolean
  onCreate: () => void
  onEdit: (item: OntologyConstraint) => void
  onDelete: (item: OntologyConstraint) => void
}

export default function OntologyConstraintSection({ data, loading, onCreate, onEdit, onDelete }: Props) {
  const { t } = useTranslation()
  const columns: ColumnsType<OntologyConstraint> = [
    {
      title: 'Constraint Name',
      dataIndex: 'name',
      key: 'name',
      width: 160,
      render: (value) => <strong>{value}</strong>,
    },
    {
      title: 'Target Type',
      dataIndex: 'targetType',
      key: 'targetType',
      width: 100,
      render: (value: string) => (
        <Tag color={TARGET_TYPE_TAG[value] || 'default'}>{t(constraintTargetTypeTextMap[value as keyof typeof constraintTargetTypeTextMap] || value)}</Tag>
      ),
    },
    {
      title: 'Target',
      key: 'target',
      width: 200,
      render: (_, record) => record.targetLabel || record.targetCode,
    },
    {
      title: 'Constraint Type',
      dataIndex: 'constraintType',
      key: 'constraintType',
      width: 120,
      render: (value: string) => t(constraintTypeTextMap[normalizeConstraintType(value)]),
    },
    {
      title: 'Expression',
      dataIndex: 'expression',
      key: 'expression',
      render: (value: string) => value || <span style={{ color: '#94a3b8' }}>—</span>,
    },
    {
      title: 'Recommendation',
      dataIndex: 'suggestion',
      key: 'suggestion',
      width: 200,
      render: (value: string) => value || <span style={{ color: '#94a3b8' }}>—</span>,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 160,
      render: (_, record) => (
        <span>
          <a className="yx-table-action" onClick={() => onEdit(record)}><EditOutlined /> Edit</a>
          <a className="yx-table-action" style={{ color: '#ef4444' }} onClick={() => onDelete(record)}><DeleteOutlined /> Delete</a>
        </span>
      ),
    },
  ]

  return (
    <div className="config-section" style={cardStyle}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <h3 style={h3Style}><ControlOutlined style={{ color: '#3b82f6' }} /> Ontology Constraints</h3>
        <Button type="primary" icon={<PlusOutlined />} style={{ fontSize: 13 }} onClick={onCreate}>Add Constraint</Button>
      </div>
      <p style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16 }}>
        Define constraints for ontology objects, attributes, or relations, such as exclusivity, ranges, and uniqueness.
      </p>
      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        pagination={false}
        size="middle"
        loading={loading}
        locale={{ emptyText: 'No ontology constraints. Select Add Constraint to begin.' }}
      />
    </div>
  )
}
