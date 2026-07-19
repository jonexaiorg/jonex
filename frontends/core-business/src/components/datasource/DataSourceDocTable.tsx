import React from 'react'
import { Table, Tag, Space, Modal, message } from 'antd'
import { useTranslation } from 'react-i18next'
import type { ManualDocItem } from '@/types/domainKnowledge'
import { deleteManualDocument } from '@/api/domainKnowledge'
import { useDocumentViewer } from '@/components/DocumentViewer'


const STATUS_STEPS = ['Ingest', 'Parse', 'Compile']
type StepState = 'done' | 'active' | 'pending'
const stepColors: Record<StepState, { bg: string; text: string }> = {
  done: { bg: '#ecfdf5', text: '#10b981' },
  active: { bg: '#eff6ff', text: '#3b82f6' },
  pending: { bg: '#f1f5f9', text: '#cbd5e1' },
}

function getStepStates(status: string): StepState[] {
  const steps = status.split('·').map((s) => s.trim())
  const result: StepState[] = ['pending', 'pending', 'pending']
  for (let i = 0; i < Math.min(steps.length, 3); i++) {
    result[i] = steps[i].includes('中') ? 'active' : 'done'
  }
  return result
}

function renderStatus(v: string) {

  if (!v.includes('·')) {
    const isError = v === 'failed'
    return (
      <Tag
        style={{
          fontSize: 11, padding: '2px 8px', border: 'none', fontWeight: 500,
          background: isError ? '#fef2f2' : '#f1f5f9',
          color: isError ? '#ef4444' : '#64748b',
        }}
      >
        {isError ? 'Parsing Failed' : v}
      </Tag>
    )
  }
  const states = getStepStates(v)
  return (
    <Space size={4}>
      {STATUS_STEPS.map((label, i) => {
        const s = states[i]
        return (
          <React.Fragment key={i}>
            <span
              style={{
                display: 'inline-block',
                fontSize: 11, padding: '2px 8px', border: 'none', fontWeight: 500,
                background: stepColors[s].bg, color: stepColors[s].text,
                borderRadius: 4, lineHeight: '18px',
              }}
            >
              {label}
            </span>
            {i < STATUS_STEPS.length - 1 && (
              <span style={{ color: '#d1d5db', fontSize: 10 }}>·</span>
            )}
          </React.Fragment>
        )
      })}
    </Space>
  )
}

interface Props {
  kbId: string
  docs: ManualDocItem[]
  loading?: boolean

  onChanged?: () => void

  emptyText?: string

  pageSize?: number
}





export default function DataSourceDocTable({
  kbId,
  docs,
  loading,
  onChanged,
  emptyText,
  pageSize = 10,
}: Props) {
  const { t } = useTranslation()
  const resolvedEmptyText = emptyText ?? t('dataSource.noDocuments')
  const { openDocument, viewer } = useDocumentViewer()


  const handleView = (doc: ManualDocItem) => {
    openDocument({ docId: doc.id, fileName: doc.name })
  }


  const handleDelete = (doc: ManualDocItem) => {
    Modal.confirm({
      title: t('dataSource.deleteDocument'),
      content: t('dataSource.deleteDocumentConfirm'),
      okText: t('dataSource.delete'),
      okButtonProps: { danger: true },
      cancelText: t('dataSource.cancel'),
      onOk: async () => {
        try {
          await deleteManualDocument(kbId, doc.id)
          message.success(t('common.deletedSuccess'))
          onChanged?.()
        } catch (err: any) {
          message.error(err?.message || t('common.deleteFailed'))
        }
      },
    })
  }

  const columns = [
    {
      title: t('dataSource.documentName'), dataIndex: 'name', key: 'name', width: 240,
      render: (v: string) => <a className="yx-table-action">{v}</a>,
    },
    { title: t('dataSource.documentType'), dataIndex: 'type', key: 'type', width: 80 },
    { title: t('dataSource.documentSize'), dataIndex: 'size', key: 'size', width: 90 },
    { title: t('dataSource.documentUploader'), dataIndex: 'uploader', key: 'uploader', width: 90 },
    { title: t('dataSource.documentTime'), dataIndex: 'uploadTime', key: 'uploadTime', width: 160 },
    {
      title: t('dataSource.documentStatus'), dataIndex: 'status', key: 'status', width: 200,
      render: (v: string) => renderStatus(v),
    },
    {
      title: t('knowledgeSearch.actions'), key: 'actions', width: 100,
      render: (_: unknown, record: ManualDocItem) => (
        <>
          <a className="yx-table-action" onClick={() => handleView(record)}>{t('domainKnowledge.roleView')}</a>
          <a className="yx-table-action" onClick={() => handleDelete(record)}>{t('dataSource.delete')}</a>
        </>
      ),
    },
  ]

  return (
    <>
      <Table
        columns={columns}
        dataSource={docs}
        rowKey="id"
        size="middle"
        loading={loading}
        pagination={{ pageSize }}
        locale={{ emptyText: resolvedEmptyText }}
      />
      {viewer}
    </>
  )
}
