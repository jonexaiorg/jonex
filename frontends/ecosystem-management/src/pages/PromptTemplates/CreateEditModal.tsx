import React, { useEffect, useState } from 'react'
import { Modal, Form, Input, Select, message } from 'antd'
import { useTranslation } from 'react-i18next'
import {
  PROMPT_CATEGORIES,
  type PromptTemplateItem,
  type CreatePromptTemplatePayload,
  type UpdatePromptTemplatePayload,
} from '../../api/promptTemplates'

const { TextArea } = Input

interface CreateEditModalProps {
  open: boolean
  mode: 'create' | 'edit' | 'view'
  template: PromptTemplateItem | null
  onClose: () => void
  onSubmit: (data: CreatePromptTemplatePayload | UpdatePromptTemplatePayload) => Promise<void>
}

function getCurrentContent(t: PromptTemplateItem | null): string {
  if (!t) return ''
  const versions = t.versions_json || []
  return versions.length > 0 ? versions[0].content : ''
}

const CreateEditModal: React.FC<CreateEditModalProps> = ({
  open, mode, template, onClose, onSubmit,
}) => {
  const { t } = useTranslation()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const isView = mode === 'view'

  useEffect(() => {
    if (!open) return
    if (mode === 'create') {
      form.resetFields()
      form.setFieldsValue({ category: 'promptTemplate.categories.general', status: '启用' })
    } else if (template) {
      form.setFieldsValue({
        name: template.name,
        category: template.category,
        description: template.description || '',
        content: getCurrentContent(template),
        status: template.status,
        version_remark: '',
        target_version: '',
      })
    }
  }, [open, mode, template, form])

  const handleOk = async () => {
    if (isView) { onClose(); return }
    try {
      const values = await form.validateFields()
      setLoading(true)
      await onSubmit(values)
      onClose()
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) return
      message.error(err instanceof Error ? err.message : t('common.saveFailed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={
        mode === 'create' ? t('promptTemplate.create')
          : mode === 'edit' ? t('promptTemplate.edit')
          : t('promptTemplate.view')
      }
      open={open}
      onOk={handleOk}
      onCancel={onClose}
      okText={isView ? t('common.close') : t('common.save')}
      cancelText={t('common.cancel')}
      confirmLoading={loading}
      cancelButtonProps={isView ? { style: { display: 'none' } } : undefined}
      width={640}
      destroyOnClose
    >
      <Form form={form} layout="vertical" disabled={isView}>
        <Form.Item
          name="name"
          label={t('promptTemplate.name')}
          rules={[{ required: true, message: t('promptTemplate.nameRequired') }]}
        >
          <Input placeholder={t('promptTemplate.namePlaceholder')} maxLength={255} />
        </Form.Item>

        <Form.Item
          name="category"
          label={t('promptTemplate.category')}
          rules={[{ required: true, message: t('promptTemplate.categoryRequired') }]}
        >
          <Select placeholder={t('promptTemplate.categoryPlaceholder')}>
            {PROMPT_CATEGORIES.map(cat => (
              <Select.Option key={cat} value={cat}>{t(cat)}</Select.Option>
            ))}
          </Select>
        </Form.Item>

        {mode === 'edit' && (
          <>
            <Form.Item name="version_remark" label={t('promptTemplate.versionRemark')}>
              <Input placeholder={t('promptTemplate.versionRemarkPlaceholder')} maxLength={512} />
            </Form.Item>

            <Form.Item
              name="target_version"
              label={t('promptTemplate.targetVersion')}
              extra={t('promptTemplate.targetVersionExtra', { current: template?.current_version || '1.1' })}
            >
              <Input placeholder={t('promptTemplate.targetVersionPlaceholder')} maxLength={32} />
            </Form.Item>
          </>
        )}

        <Form.Item name="description" label={t('promptTemplate.descriptionField')}>
          <Input placeholder={t('promptTemplate.descriptionPlaceholder')} maxLength={512} />
        </Form.Item>

        <Form.Item
          name="content"
          label={t('promptTemplate.content')}
          rules={[{ required: true, message: t('promptTemplate.contentRequired') }]}
          extra={t('promptTemplate.variableHint', {
            placeholder: '{{variable}}',
            example: '{{user_question}}',
          })}
        >
          <TextArea
            rows={8}
            placeholder={t('promptTemplate.contentPlaceholder', {
              placeholder: '{{variable}}',
            })}
            style={{ fontFamily: "'Courier New', monospace", lineHeight: 1.6 }}
          />
        </Form.Item>

        <Form.Item name="status" label={t('promptTemplate.status')}>
          <Select>
            <Select.Option value="启用">{t('promptTemplate.enabled')}</Select.Option>
            <Select.Option value="停用">{t('promptTemplate.disabled')}</Select.Option>
          </Select>
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default React.memo(CreateEditModal)
