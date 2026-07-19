import React from 'react'
import { useTranslation } from 'react-i18next'
import { Button, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { ShareAltOutlined, PlusOutlined, ImportOutlined, EditOutlined, DeleteOutlined, MessageOutlined } from '@ant-design/icons'
import type { OntologyRelationDef, OntologyRelationType } from '@/types/domainKnowledge'
import { RELATION_TYPE_TAG } from './constants'

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
  data: OntologyRelationDef[]
  loading: boolean
  onCreate: () => void
  onImport: () => void
  onEdit: (r: OntologyRelationDef) => void
  onDelete: (r: OntologyRelationDef) => void
  onPrompt: (r: OntologyRelationDef) => void
}

export default function OntologyRelationSection({ data, loading, onCreate, onImport, onEdit, onDelete, onPrompt }: Props) {
  const { t } = useTranslation()
  const columns: ColumnsType<OntologyRelationDef> = [
    { title: 'Source Object', dataIndex: 'sourceObject', key: 'sourceObject', width: 110, render: (v) => <span className="tag" style={{ background: '#eff6ff', color: '#3b82f6', padding: '2px 8px', borderRadius: 4, fontSize: 12 }}>{v}</span> },
    { title: t('ontology.relationName'), dataIndex: 'name', key: 'name', width: 110, render: (v) => <strong>{v}</strong> },
    { title: 'Target Object', dataIndex: 'targetObject', key: 'targetObject', width: 110, render: (v) => <span className="tag" style={{ background: '#ecfdf5', color: '#059669', padding: '2px 8px', borderRadius: 4, fontSize: 12 }}>{v}</span> },
    { title: t('domainService.description'), dataIndex: 'description', key: 'description', render: (v) => <span style={{ fontSize: 12, color: '#64748b' }}>{v || '—'}</span> },
    {
      title: t('ontology.relation'),
      dataIndex: 'relationType',
      key: 'relationType',
      width: 90,
      render: (v: OntologyRelationType) => {
        const tagMap: Record<OntologyRelationType, { bg: string; color: string }> = {
          '一对一': RELATION_TYPE_TAG.one_to_one,
          '一对多': RELATION_TYPE_TAG.one_to_many,
          '多对一': RELATION_TYPE_TAG.one_to_many,
          '多对多': RELATION_TYPE_TAG.many_to_many,
          '自定义': RELATION_TYPE_TAG.custom,
        }
        const c = tagMap[v] || { bg: '#eff6ff', color: '#3b82f6' }
        return <span style={{ background: c.bg, color: c.color, padding: '2px 8px', borderRadius: 4, fontSize: 12 }}>{v}</span>
      },
    },
    { title: t('domainService.status'), dataIndex: 'status', key: 'status', width: 80, render: (v) => <Tag color={v === 'active' ? 'success' : 'default'}>{v === 'active' ? t('status.active') : t('status.inactive')}</Tag> },
    {
      title: t('knowledgeSearch.actions'),
      key: 'actions',
      width: 250,
      render: (_, r) => (
        <span>
          <a className="yx-table-action" onClick={() => onEdit(r)}><EditOutlined /> {t('domainKnowledge.edit')}</a>
          <a className="yx-table-action" style={{ color: '#ef4444' }} onClick={() => onDelete(r)}><DeleteOutlined /> {t('dataSource.delete')}</a>
          { }
          { }
        </span>
      ),
    },
  ]

  return (
    <div className="config-section" style={cardStyle}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <h3 style={h3Style}><ShareAltOutlined style={{ color: '#8b5cf6' }} /> {t('compile.relations')}</h3>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button type="primary" icon={<PlusOutlined />} style={{ fontSize: 13 }} onClick={onCreate}>{t('compile.relationCreated')}</Button>
          <Button icon={<ImportOutlined />} style={{ fontSize: 13 }} onClick={onImport}>{t('compile.importFromTemplate')}</Button>
        </div>
      </div>
      <p style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16 }}>Define semantic relations between ontology objects, including source, target, name, type, and status.</p>
      <Table columns={columns} dataSource={data} rowKey="id" pagination={false} size="middle" loading={loading} locale={{ emptyText: 'No ontology relations. Create a relation or import from a template.' }} />
    </div>
  )
}
