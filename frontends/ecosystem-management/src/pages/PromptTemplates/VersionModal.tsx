import React, { useEffect, useState, useCallback } from 'react'
import { Modal, Table, Button, Tag, message, Popconfirm, Typography } from 'antd'
import { EyeOutlined, RollbackOutlined, BranchesOutlined, CopyOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import {
  listVersions,
  rollbackVersion,
  type VersionItem,
  type PromptTemplateItem,
} from '../../api/promptTemplates'

const { Paragraph } = Typography

interface VersionModalProps {
  open: boolean
  template: PromptTemplateItem | null
  onClose: () => void
  onRollback: () => void
}

const VersionModal: React.FC<VersionModalProps> = ({ open, template, onClose, onRollback }) => {
  const { t } = useTranslation()
  const [versions, setVersions] = useState<VersionItem[]>([])
  const [currentVersion, setCurrentVersion] = useState('')
  const [loading, setLoading] = useState(false)
  const [detailOpen, setDetailOpen] = useState(false)
  const [detailVersion, setDetailVersion] = useState<VersionItem | null>(null)

  const loadVersions = useCallback(async () => {
    if (!template) return
    setLoading(true)
    try {
      const result = await listVersions(template.id)
      setVersions(result.items)
      setCurrentVersion(result.current_version)
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('common.loadFailed'))
    } finally {
      setLoading(false)
    }
  }, [template, t])

  useEffect(() => {
    if (open && template) loadVersions()
  }, [open, template, loadVersions])

  const handleRollback = async (targetVersion: string) => {
    if (!template) return
    try {
      await rollbackVersion(template.id, targetVersion)
      message.success(t('promptTemplate.rollbackSuccess', { version: targetVersion }))
      await loadVersions()
      onRollback()
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('common.operationFailed'))
    }
  }

  const handleViewDetail = (ver: VersionItem) => {
    setDetailVersion(ver)
    setDetailOpen(true)
  }

  const handleCopyContent = () => {
    if (!detailVersion) return
    navigator.clipboard.writeText(detailVersion.content).then(
      () => message.success(t('promptTemplate.copySuccess')),
      () => message.error(t('common.operationFailed')),
    )
  }

  const columns = [
    {
      title: t('promptTemplate.versionNumber'), dataIndex: 'version', width: 100,
      render: (v: string, _: VersionItem, idx: number) => (
        <span>
          <span style={{ fontWeight: 600, color: '#7c3aed' }}>v{v}</span>
          {idx === 0 && <Tag color="green" style={{ marginLeft: 6, fontSize: 10 }}>{t('promptTemplate.currentVersion')}</Tag>}
        </span>
      ),
    },
    {
      title: t('promptTemplate.versionPreview'), dataIndex: 'content', ellipsis: true,
      render: (content: string, record: VersionItem) => (
        <div>
          <div style={{
            fontFamily: "'Courier New', monospace", fontSize: 11, color: '#64748b',
            maxWidth: 260, maxHeight: 36, overflow: 'hidden', lineHeight: 1.5,
            whiteSpace: 'pre-wrap',
          }}>
            {content?.replace(/\n/g, ' ').slice(0, 80)}{(content || '').length > 80 ? '…' : ''}
          </div>
          <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 4 }}>
            {record.remark || '—'}
          </div>
        </div>
      ),
    },
    { title: t('promptTemplate.updatedBy'), dataIndex: 'updated_by', width: 90 },
    { title: t('promptTemplate.updatedAt'), dataIndex: 'updated_at', width: 150 },
    {
      title: t('promptTemplate.actions'), key: 'actions', width: 120,
      render: (_: unknown, record: VersionItem, idx: number) => (
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          <Button size="small" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)}>
            {t('promptTemplate.view')}
          </Button>
          {idx > 0 && (
            <Popconfirm
              title={t('promptTemplate.rollbackConfirm', { version: record.version })}
              description={t('promptTemplate.rollbackConfirmDesc')}
              onConfirm={() => handleRollback(record.version)}
              okText={t('promptTemplate.confirmRollback')}
              cancelText={t('common.cancel')}
            >
              <Button size="small" icon={<RollbackOutlined />} style={{ color: '#f59e0b' }}>
                {t('promptTemplate.rollback')}
              </Button>
            </Popconfirm>
          )}
        </div>
      ),
    },
  ]

  return (
    <>
      <Modal
        title={
          <span>
            <BranchesOutlined style={{ color: '#7c3aed', marginRight: 8 }} />
            {t('promptTemplate.version')} · {template?.name}
          </span>
        }
        open={open}
        onCancel={onClose}
        footer={<Button onClick={onClose}>{t('common.close')}</Button>}
        width={780}
      >
        <div style={{ marginBottom: 16, fontSize: 13, color: '#475569' }}>
          <span>{t('promptTemplate.currentVersion')}：<Tag color="purple">v{currentVersion}</Tag></span>
          <span style={{ marginLeft: 16 }}>{t('promptTemplate.versionCount', { count: versions.length })}</span>
        </div>
        <Table
          dataSource={versions}
          columns={columns}
          rowKey="version"
          loading={loading}
          pagination={false}
          size="small"
        />
      </Modal>

      { }
      <Modal
        title={t('promptTemplate.versionDetail')}
        open={detailOpen}
        onCancel={() => setDetailOpen(false)}
        footer={[
          <Button key="copy" icon={<CopyOutlined />} onClick={handleCopyContent}>
            {t('promptTemplate.copyContent')}
          </Button>,
          <Button key="close" onClick={() => setDetailOpen(false)}>{t('common.close')}</Button>,
        ]}
        width={700}
      >
        {detailVersion && (
          <>
            <div style={{ display: 'flex', gap: 24, marginBottom: 14, fontSize: 13 }}>
              <div>
                <span style={{ color: '#94a3b8' }}>{t('promptTemplate.versionNumber')}：</span>
                <Tag color="purple">v{detailVersion.version}</Tag>
              </div>
              <div>
                <span style={{ color: '#94a3b8' }}>{t('promptTemplate.updatedAtBy')}：</span>
                {detailVersion.updated_at} · {detailVersion.updated_by}
              </div>
            </div>
            <div style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>{t('promptTemplate.versionRemark')}</div>
              <div style={{
                fontSize: 13, color: '#475569', padding: '8px 12px',
                background: '#f8fafc', borderRadius: 6,
              }}>
                {detailVersion.remark || '—'}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>{t('promptTemplate.content')}</div>
              <Paragraph
                copyable
                style={{
                  background: '#f8fafc', border: '1px solid #e8edf3', borderRadius: 8,
                  padding: 14, fontFamily: "'Courier New', monospace", fontSize: 12,
                  color: '#475569', lineHeight: 1.7, whiteSpace: 'pre-wrap',
                  maxHeight: 320, overflow: 'auto',
                }}
              >
                {detailVersion.content}
              </Paragraph>
            </div>
          </>
        )}
      </Modal>
    </>
  )
}

export default React.memo(VersionModal)
