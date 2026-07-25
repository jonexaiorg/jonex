import React from 'react'
import { Modal, Input } from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import type { DomainKnowledgeItem } from '@/types/domainKnowledge'

interface CreateEditModalProps {
  open: boolean
  editingKb: DomainKnowledgeItem | null
  name: string
  description: string
  submitting: boolean
  onNameChange: (val: string) => void
  onDescChange: (val: string) => void
  onOk: () => void
  onCancel: () => void
}

export default function CreateEditModal({
  open,
  editingKb,
  name,
  description,
  submitting,
  onNameChange,
  onDescChange,
  onOk,
  onCancel,
}: CreateEditModalProps) {
  const { t } = useTranslation()

  return (
    <Modal
      open={open}
      onCancel={onCancel}
      onOk={onOk}
      confirmLoading={submitting}
      okText={editingKb ? t('common.save') : t('common.create')}
      cancelText={t('common.cancel')}
      width={520}
      title={
        <span>
          {editingKb ? (
            <EditOutlined style={{ color: '#3b82f6', marginRight: 8 }} />
          ) : (
            <PlusOutlined style={{ color: '#3b82f6', marginRight: 8 }} />
          )}
          {editingKb ? t('domainKnowledge.editKnowledgeBase') : t('domainKnowledge.createKnowledgeBase')}
        </span>
      }>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div>
          <label
            style={{
              display: 'block',
              fontSize: 13,
              fontWeight: 500,
              color: '#475569',
              marginBottom: 4,
            }}>
            {t('domainKnowledge.knowledgeBaseName')} <span style={{ color: '#ef4444' }}>*</span>
          </label>
          <Input
            placeholder={t('domainKnowledge.namePlaceholder')}
            value={name}
            onChange={(e) => onNameChange(e.target.value)}
          />
        </div>
        <div>
          <label
            style={{
              display: 'block',
              fontSize: 13,
              fontWeight: 500,
              color: '#475569',
              marginBottom: 4,
            }}>
            {t('domainKnowledge.description')}
          </label>
          <Input.TextArea
            rows={3}
            placeholder={t('domainKnowledge.descPlaceholder')}
            value={description}
            onChange={(e) => onDescChange(e.target.value)}
          />
        </div>
      </div>
    </Modal>
  )
}
