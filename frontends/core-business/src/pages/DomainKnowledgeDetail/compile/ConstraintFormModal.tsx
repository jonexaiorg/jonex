import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Modal, Form, Input, Select } from 'antd'
import type {
  ConstraintTargetType,
  ConstraintTypeCode,
  OntologyConstraint,
  SaveOntologyConstraintPayload,
} from '@/types/domainKnowledge'
import {
  constraintTargetTypeTextMap,
  constraintTypeTextMap,
  normalizeConstraintType,
} from '@/types/domainKnowledge'
import type { ConstraintTargetOptions } from '@/api/domainKnowledge'

const TARGET_TYPE_OPTIONS: { labelKey: string; value: ConstraintTargetType }[] = [
  { labelKey: constraintTargetTypeTextMap.entity, value: 'entity' },
  { labelKey: constraintTargetTypeTextMap.attribute, value: 'attribute' },
  { labelKey: constraintTargetTypeTextMap.relation, value: 'relation' },
]

const CONSTRAINT_TYPE_OPTIONS: { labelKey: string; value: ConstraintTypeCode }[] = (
  Object.entries(constraintTypeTextMap) as [ConstraintTypeCode, string][]
).map(([value, labelKey]) => ({ value, labelKey }))

interface ConstraintFormValues {
  name: string
  targetType: ConstraintTargetType
  targetCode: string
  constraintType: ConstraintTypeCode
  expression?: string
  suggestion?: string
}

interface Props {
  open: boolean
  editing: OntologyConstraint | null
  targetOptions: ConstraintTargetOptions
  existingNames: string[]
  submitting: boolean
  onCancel: () => void
  onSubmit: (payload: SaveOntologyConstraintPayload) => void
}

export default function ConstraintFormModal({
  open,
  editing,
  targetOptions,
  existingNames,
  submitting,
  onCancel,
  onSubmit,
}: Props) {
  const { t } = useTranslation()
  const [form] = Form.useForm<ConstraintFormValues>()
  const [targetType, setTargetType] = useState<ConstraintTargetType>('entity')

  useEffect(() => {
    if (!open) return
    if (editing) {
      setTargetType(editing.targetType)
      form.setFieldsValue({
        name: editing.name,
        targetType: editing.targetType,
        targetCode: editing.targetCode,
        constraintType: normalizeConstraintType(editing.constraintType),
        expression: editing.expression,
        suggestion: editing.suggestion,
      })
      return
    }
    setTargetType('entity')
    form.setFieldsValue({
      name: '',
      targetType: 'entity',
      targetCode: undefined,
      constraintType: 'custom',
      expression: '',
      suggestion: '',
    })
  }, [editing, form, open])

  const currentOptions = targetOptions[targetType] || []

  async function handleOk() {
    const values = await form.validateFields()
    const label = (targetOptions[values.targetType] || []).find((o) => o.value === values.targetCode)?.label
    onSubmit({
      name: values.name.trim(),
      targetType: values.targetType,
      targetCode: values.targetCode,
      targetLabel: label,
      constraintType: values.constraintType || 'custom',
      expression: (values.expression || '').trim(),
      suggestion: (values.suggestion || '').trim(),
    })
  }

  return (
    <Modal
      title={editing ? 'Edit Ontology Constraint' : 'Add Ontology Constraint'}
      open={open}
      onCancel={onCancel}
      onOk={handleOk}
      okText="Confirm"
      cancelText="Cancel"
      confirmLoading={submitting}
      width={720}
      destroyOnHidden
    >
      <Form form={form} layout="vertical" preserve={false}>
        <Form.Item
          label="Constraint Name"
          name="name"
          rules={[
            { required: true, whitespace: true, message: 'Enter a constraint name' },
            {
              validator: (_, value) => {
                const name = (value || '').trim()
                if (!name) return Promise.resolve()
                const clash = existingNames.some((n) => n === name && n !== editing?.name)
                return clash ? Promise.reject(new Error('This constraint name already exists')) : Promise.resolve()
              },
            },
          ]}
        >
          <Input placeholder="For example, Non-negative Amount" />
        </Form.Item>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <Form.Item label="Target Type" name="targetType" rules={[{ required: true, message: 'Select a target type' }]}>
            <Select
              options={TARGET_TYPE_OPTIONS.map((option) => ({
                value: option.value,
                label: t(option.labelKey),
              }))}
              onChange={(v: ConstraintTargetType) => {
                setTargetType(v)
                form.setFieldsValue({ targetCode: undefined })
              }}
            />
          </Form.Item>
          <Form.Item label="Target" name="targetCode" rules={[{ required: true, message: 'Select a target' }]}>
            <Select
              options={currentOptions}
              showSearch
              optionFilterProp="label"
              placeholder={currentOptions.length ? 'Select a target' : 'No targets available'}
            />
          </Form.Item>
        </div>
        <Form.Item label="Constraint Type" name="constraintType">
          <Select options={CONSTRAINT_TYPE_OPTIONS.map((option) => ({
            value: option.value,
            label: t(option.labelKey),
          }))} />
        </Form.Item>
        <Form.Item label="Constraint Expression" name="expression">
          <Input.TextArea rows={2} placeholder="Define the condition, for example amount >= 0" />
        </Form.Item>
        <Form.Item label="Recommendation" name="suggestion">
          <Input.TextArea rows={2} placeholder="Message or remediation advice when the constraint is violated" />
        </Form.Item>
      </Form>
    </Modal>
  )
}
