import React, { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Modal, Form, Input, Select, InputNumber } from 'antd'
import type { CompileStep, SaveCompileStepPayload, CompileScope, CompileTrigger } from '@/types/domainKnowledge'
import { COMPILE_SCOPE_OPTIONS, COMPILE_TRIGGER_OPTIONS, SKILL_OPTIONS } from './constants'

interface StepFormValues {
  order: number
  name: string
  prompt?: string
  scope: CompileScope
  trigger: CompileTrigger
  skill?: string
  template?: string
}
interface Props {
  open: boolean
  editing: CompileStep | null
  submitting: boolean
  onCancel: () => void
  onSubmit: (payload: SaveCompileStepPayload) => void
}

export default function StepFormModal({ open, editing, submitting, onCancel, onSubmit }: Props) {
  const { t } = useTranslation()
  const [form] = Form.useForm<StepFormValues>()

  useEffect(() => {
    if (!open) return
    if (editing) {
      form.setFieldsValue({
        order: editing.order, name: editing.name, prompt: editing.prompt,
        scope: editing.scope, trigger: editing.trigger, skill: editing.skill, template: editing.template,
      })
    } else {
      form.setFieldsValue({ order: undefined as any, name: '', prompt: '', scope: 'single', trigger: 'upload', skill: '', template: '' })
    }
  }, [open, editing, form])

  const handleOk = async () => {
    const v = await form.validateFields()
    onSubmit({
      order: Number(v.order),
      name: v.name.trim(),
      prompt: (v.prompt || '').trim(),
      skill: v.skill || '',
      scope: v.scope,
      trigger: v.trigger,
      template: (v.template || '').trim(),
    })
  }

  return (
    <Modal title={editing ? t('compile.editStep') : t('compile.createStep')} open={open} onCancel={onCancel} onOk={handleOk} okText={t('common.save')} cancelText={t('dataSource.cancel')} confirmLoading={submitting} width={620} destroyOnHidden>
      <Form form={form} layout="vertical" preserve={false}>
        <div style={{ display: 'flex', gap: 12 }}>
          <Form.Item label={t('compile.stepOrder')} name="order" rules={[{ required: true, message: 'Enter the step order' }]} style={{ width: 160 }}>
            <InputNumber min={1} style={{ width: '100%' }} placeholder="For example: 1" />
          </Form.Item>
          <Form.Item label={t('compile.stepName')} name="name" rules={[{ required: true, whitespace: true, message: 'Enter a step name' }]} style={{ flex: 1 }}>
            <Input placeholder="For example: Entity Extraction" />
          </Form.Item>
        </div>
        <Form.Item label="Description and Prompt" name="prompt">
          <Input.TextArea rows={3} placeholder="Describe the compilation task and prompt for this step" />
        </Form.Item>
        <div style={{ display: 'flex', gap: 12 }}>
          <Form.Item label="Scope" name="scope" rules={[{ required: true, message: 'Select a scope' }]} style={{ flex: 1 }}>
            <Select options={COMPILE_SCOPE_OPTIONS} />
          </Form.Item>
          <Form.Item label="Trigger" name="trigger" style={{ flex: 1 }}>
            <Select options={COMPILE_TRIGGER_OPTIONS} />
          </Form.Item>
        </div>
        <Form.Item label="Linked Skill" name="skill">
          <Select options={SKILL_OPTIONS} />
        </Form.Item>
        <Form.Item label="Result Template" name="template">
          <Input.TextArea rows={2} placeholder="Describe the output format template for this step" />
        </Form.Item>
      </Form>
    </Modal>
  )
}