import React, { useState, useEffect } from 'react'
import { Modal, Upload, Select, Space, message } from 'antd'
import type { UploadProps } from 'antd/es/upload'
import {
  PlusOutlined,
  CloudUploadOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { uploadManualDocument, getFolderList } from '@/api/domainKnowledge'
import { ACCEPT_EXTENSIONS } from '@/constants/upload'
import type { FolderItem } from '@/types/domainKnowledge'

export interface UploadModalProps {
  kbId: string
  open: boolean
  onClose: () => void
  onSuccess?: () => void
}

const UploadModal: React.FC<UploadModalProps> = ({
  kbId,
  open,
  onClose,
  onSuccess,
}) => {
  const { t } = useTranslation()
  const [uploading, setUploading] = useState(false)
  const [selectedFolderId, setSelectedFolderId] = useState<string>('')
  const [folders, setFolders] = useState<FolderItem[]>([])

  useEffect(() => {
    if (open) {
      getFolderList(kbId)
        .then((res) => setFolders(res.items ?? []))
        .catch(() => setFolders([]))
    }
  }, [open, kbId])

  const handleUpload: UploadProps['customRequest'] = async ({
    file,
    onSuccess: onUploadSuccess,
    onError,
  }) => {
    setUploading(true)
    try {
      const f = file as File
      if (f.size === 0) {
        message.error(t('common.fileEmpty'))
        onError?.(new Error('empty file'))
        setUploading(false)
        return
      }
      await uploadManualDocument(kbId, f, selectedFolderId || undefined, t)
      message.success(t('common.uploadSuccess', { name: (file as File).name }))
      onUploadSuccess?.(void 0)
      onSuccess?.()
      onClose()
    } catch (err: any) {
      message.error(err?.message || t('common.uploadFailed'))
      onError?.(err)
    } finally {
      setUploading(false)
    }
  }

  return (
    <Modal
      title={
        <Space>
          <PlusOutlined style={{ color: '#3b82f6' }} />
          <span>{t('common.addDocument')}</span>
        </Space>
      }
      open={open}
      onCancel={onClose}
      footer={null}
      width={560}
    >
      <div style={{ marginBottom: 16 }}>
        <div
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: '#0b2b5c',
            marginBottom: 6,
          }}
        >
          {t('common.targetDirectory')}
        </div>
        <Select
          value={selectedFolderId}
          onChange={setSelectedFolderId}
          placeholder={t('common.selectDirectory')}
          style={{ width: '100%' }}
          options={[
            { value: '', label: t('common.allDocuments') },
            ...folders.map((f) => ({ value: f.id, label: f.name })),
          ]}
        />
      </div>

      <Upload.Dragger
        name="file"
        customRequest={handleUpload}
        showUploadList={false}
        accept={ACCEPT_EXTENSIONS}
        disabled={uploading}
      >
        <div style={{ padding: '20px 0' }}>
          <p className="ant-upload-drag-icon">
            <CloudUploadOutlined
              style={{ fontSize: 48, color: '#3b82f6' }}
            />
          </p>
          <p
            style={{
              fontSize: 16,
              color: '#0b2b5c',
              fontWeight: 500,
              marginBottom: 8,
            }}
          >
            {t('common.uploadDraggerText')}
          </p>
          <p
            style={{
              fontSize: 14,
              color: '#64748b',
              marginBottom: 8,
              lineHeight: 1.6,
            }}
          >
            {t('common.uploadDescription')}
          </p>
          <p style={{ fontSize: 13, color: '#f97316', margin: 0 }}>
            <ExclamationCircleOutlined style={{ marginRight: 4 }} />
            {t('common.uploadMaxSize')}
          </p>
        </div>
      </Upload.Dragger>
      {uploading && (
        <p
          style={{
            textAlign: 'center',
            color: '#64748b',
            marginTop: 12,
            fontSize: 14,
          }}
        >
          {t('common.uploading')}
        </p>
      )}
    </Modal>
  )
}

export default UploadModal
