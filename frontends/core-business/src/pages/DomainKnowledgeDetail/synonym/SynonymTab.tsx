import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Button, Table, Tag, Space, Popconfirm, message, Empty, Alert } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { PlusOutlined, ImportOutlined, ExportOutlined, SwapOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import type { SynonymGroup, SynonymImportResult } from '@/types/domainKnowledge'
import { useSynonyms } from '@/hooks/useSynonyms'
import {
  createSynonym,
  updateSynonym,
  deleteSynonym,
  importSynonyms,
  exportAllSynonyms,
} from '@/api/ontologySynonym'
import SynonymFormModal from './SynonymFormModal'
import SynonymImportModal from './SynonymImportModal'

const cardStyle: React.CSSProperties = {
  background: '#fff',
  borderRadius: 14,
  border: '1px solid #eef2f6',
  padding: 24,
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


function csvCell(value: string): string {
  if (/[",\n\r，]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`
  }
  return value
}

interface Props {
  kbId: string
}

export default function SynonymTab({ kbId }: Props) {
  const { t } = useTranslation()
  const { data, total, page, pageSize, loading, error, refresh, setPage } = useSynonyms(kbId)
  const [formModal, setFormModal] = useState<{ open: boolean; editing: SynonymGroup | null }>({ open: false, editing: null })
  const [importOpen, setImportOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [exporting, setExporting] = useState(false)

  const handleSubmit = async (terms: string[], canonical?: string) => {
    setSubmitting(true)
    try {
      if (formModal.editing) {
        await updateSynonym(formModal.editing.id, terms, canonical)
        message.success(t('synonym.updated'))
      } else {
        await createSynonym(kbId, terms, canonical)
        message.success(t('synonym.created'))
      }
      setFormModal({ open: false, editing: null })
      refresh()
    } catch (e: any) {
      message.error(e?.message || t('synonym.saveFailed'))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (record: SynonymGroup) => {
    try {
      await deleteSynonym(record.id)
      message.success(t('synonym.deleted'))
      refresh()
    } catch (e: any) {
      message.error(e?.message || t('synonym.deleteFailed'))
    }
  }

  const handleImport = async (groups: string[][]): Promise<SynonymImportResult | null> => {
    setSubmitting(true)
    try {
      const res = await importSynonyms(kbId, groups)
      if (res.created > 0) refresh()
      return res
    } catch (e: any) {
      message.error(e?.message || t('synonym.importFailed'))
      return null
    } finally {
      setSubmitting(false)
    }
  }

  const handleExport = async () => {
    setExporting(true)
    try {
      const all = await exportAllSynonyms(kbId)
      const lines = all.map((g) => g.terms.map(csvCell).join(','))
      const blob = new Blob([`\ufeff${lines.join('\r\n')}`], { type: 'text/csv;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `synonyms_${kbId}.csv`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e: any) {
      message.error(e?.message || t('synonym.exportFailed'))
    } finally {
      setExporting(false)
    }
  }

  const columns: ColumnsType<SynonymGroup> = [
    {
      title: t('synonym.synonyms'),
      dataIndex: 'terms',
      key: 'terms',
      render: (terms: string[], record) => (
        <Space size={[4, 4]} wrap>
          {(terms || []).map((t) => (
            <Tag key={t} color={record.canonical === t ? 'blue' : 'default'}>
              {t}
              {record.canonical === t ? ' (Canonical)' : ''}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: t('knowledgeSearch.actions'),
      key: 'actions',
      width: 160,
      render: (_, record) => (
        <span>
          <a className="yx-table-action" onClick={() => setFormModal({ open: true, editing: record })}>
            <EditOutlined /> {t('synonym.editGroup')}
          </a>
          <Popconfirm
            title="Delete Synonym Group"
            description="This action cannot be undone. Delete this synonym group?"
            okText="Delete"
            cancelText={t("dataSource.cancel")}
            okButtonProps={{ danger: true }}
            onConfirm={() => handleDelete(record)}
          >
            <a className="yx-table-action" style={{ color: '#ef4444' }}>
              <DeleteOutlined /> {t('synonym.deleteGroup')}
            </a>
          </Popconfirm>
        </span>
      ),
    },
  ]

  return (
    <div className="config-section" style={cardStyle}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <h3 style={h3Style}><SwapOutlined style={{ color: '#3b82f6' }} /> {t('synonym.title')}</h3>
        <Space>
          <Button icon={<ImportOutlined />} onClick={() => setImportOpen(true)}>{t('synonym.importGroup')}</Button>
          <Button icon={<ExportOutlined />} loading={exporting} onClick={handleExport}>{t('synonym.exportGroup')}</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setFormModal({ open: true, editing: null })}>
            {t('synonym.createGroup')}
          </Button>
        </Space>
      </div>
      <p style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16 }}>
        Define synonym mappings. Synonyms are mapped to canonical entities during compilation and queries.
      </p>

      {error && <Alert type="error" showIcon style={{ marginBottom: 12 }} message={error} action={<a onClick={refresh}>{t('domainKnowledge.retry')}</a>} />}

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        size="middle"
        loading={loading}
        locale={{ emptyText: <Empty description="No synonym data" /> }}
        pagination={{
          current: page,
          pageSize,
          total,
          showTotal: (t) => `${t} groups`,
          onChange: setPage,
        }}
      />

      <SynonymFormModal
        open={formModal.open}
        editing={formModal.editing}
        submitting={submitting}
        onCancel={() => setFormModal({ open: false, editing: null })}
        onSubmit={handleSubmit}
      />
      <SynonymImportModal
        open={importOpen}
        submitting={submitting}
        onCancel={() => setImportOpen(false)}
        onImport={handleImport}
      />
    </div>
  )
}
