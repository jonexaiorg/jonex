import React from 'react'
import { useTranslation } from 'react-i18next'
import { Button, Table } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { AppstoreOutlined, PlusOutlined, ImportOutlined, EditOutlined, DeleteOutlined, MessageOutlined } from '@ant-design/icons'
import type { OntologyAttribute, OntologyObjectDef } from '@/types/domainKnowledge'

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

interface Props {
  data: OntologyObjectDef[]
  loading: boolean
  onCreate: () => void
  onImport: () => void
  onEdit: (item: OntologyObjectDef) => void
  onDelete: (item: OntologyObjectDef) => void
  onPrompt: (item: OntologyObjectDef) => void
}

function AttrInlineTable({ attrs }: { attrs: OntologyAttribute[] }) {
  if (!attrs.length) return <span style={{ fontSize: 12, color: '#94a3b8' }}>No attributes</span>
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
      <thead>
        <tr>
          <th style={{ textAlign: 'left', padding: '3px 6px', color: '#64748b', borderBottom: '1px solid #e8edf3', fontSize: 11 }}>Name</th>
          <th style={{ textAlign: 'left', padding: '3px 6px', color: '#64748b', borderBottom: '1px solid #e8edf3', fontSize: 11 }}>Description</th>
          <th style={{ textAlign: 'left', padding: '3px 6px', color: '#64748b', borderBottom: '1px solid #e8edf3', fontSize: 11 }}>Type</th>
          <th style={{ textAlign: 'left', padding: '3px 6px', color: '#64748b', borderBottom: '1px solid #e8edf3', fontSize: 11 }}>Primary Key</th>
        </tr>
      </thead>
      <tbody>
        {attrs.map((attr) => (
          <tr key={attr.id || attr.name}>
            <td style={{ padding: '3px 6px' }}>{attr.name}</td>
            <td style={{ padding: '3px 6px' }}>{attr.description || '—'}</td>
            <td style={{ padding: '3px 6px' }}>{attr.type}</td>
            <td style={{ padding: '3px 6px' }}>{attr.isPrimaryKey ? 'Yes' : 'No'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default function OntologyObjectSection({ data, loading, onCreate, onImport, onEdit, onDelete, onPrompt }: Props) {
  const { t } = useTranslation()
  const columns: ColumnsType<OntologyObjectDef> = [
    {
      title: 'Object Name',
      dataIndex: 'name',
      key: 'name',
      width: 180,
      render: (value) => <strong>{value}</strong>,
    },
    {
      title: t('domainService.description'),
      dataIndex: 'description',
      key: 'description',
      width: 220,
      render: (value: string) => value || <span style={{ color: '#94a3b8' }}>None</span>,
    },
    {
      title: 'Additional Requirements',
      dataIndex: 'requirement',
      key: 'requirement',
      width: 220,
      render: (value: string) => value || <span style={{ color: '#94a3b8' }}>None</span>,
    },
    {
      title: t('ontology.attribute'),
      dataIndex: 'attributes',
      key: 'attributes',
      render: (attrs: OntologyAttribute[]) => <AttrInlineTable attrs={attrs || []} />,
    },
    {
      title: t('knowledgeSearch.actions'),
      key: 'actions',
      width: 250,
      render: (_, record) => (
        <span>
          <a className="yx-table-action" onClick={() => onEdit(record)}><EditOutlined /> {t('domainKnowledge.edit')}</a>
          <a className="yx-table-action" style={{ color: '#ef4444' }} onClick={() => onDelete(record)}><DeleteOutlined /> {t('dataSource.delete')}</a>
          { }
          { }
        </span>
      ),
    },
  ]

  return (
    <div className="config-section" style={cardStyle}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <h3 style={h3Style}><AppstoreOutlined style={{ color: '#3b82f6' }} /> {t('compile.objects')}</h3>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button type="primary" icon={<PlusOutlined />} style={{ fontSize: 13 }} onClick={onCreate}>{t('compile.objectCreated')}</Button>
          <Button icon={<ImportOutlined />} style={{ fontSize: 13 }} onClick={onImport}>{t('compile.importFromTemplate')}</Button>
        </div>
      </div>
      <p style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16 }}>
        Manage knowledge-base ontology object definitions, descriptions, attributes, and additional requirements.
      </p>
      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        pagination={false}
        size="middle"
        loading={loading}
        locale={{ emptyText: 'No ontology objects. Add an object or initialize from a template.' }}
      />
    </div>
  )
}
