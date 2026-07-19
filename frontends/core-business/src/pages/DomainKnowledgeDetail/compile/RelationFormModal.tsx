import React, { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Modal, Form, Input, Select } from 'antd'
import type { OntologyRelationDef, OntologyRelationType, SaveOntologyRelationPayload } from '@/types/domainKnowledge'

interface RelationFormValues {
  name: string
  description: string
  sourceObject: string
  targetObject: string
  relationType: OntologyRelationType
}

interface Props {
  open: boolean
  editing: OntologyRelationDef | null
  objectNames: string[]
  submitting: boolean
  onCancel: () => void
  onSubmit: (payload: SaveOntologyRelationPayload) => void
}

export default function RelationFormModal({ open, editing, objectNames, submitting, onCancel, onSubmit }: Props) {
  const { t } = useTranslation()
  const [form] = Form.useForm<RelationFormValues>()
  const objectOptions = objectNames.map((name) => ({
    label: name,
    value: name,
  }))

  useEffect(() => {
    if (!open) return
    if (editing) {
      form.setFieldsValue({
        name: editing.name,
        description: editing.description,
        sourceObject: editing.sourceObject,
        targetObject: editing.targetObject,
        relationType: editing.relationType,
      })
      return
    }
    form.setFieldsValue({
      name: '',
      description: '',
      sourceObject: '',
      targetObject: '',
      relationType: '一对一',
    })
  }, [editing, form, open])

  async function handleOk() {
    const values = await form.validateFields()
    onSubmit({
      name: values.name.trim(),
      description: (values.description || '').trim(),
      sourceObject: values.sourceObject,
      targetObject: values.targetObject,
      relationType: values.relationType,
      status: editing?.status || 'active',
    })
  }

  return (
    <Modal
      title={editing ? t('compile.editRelation') : t('compile.createRelation')}
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
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <Form.Item label={t('ontology.relationName')} name="name" rules={[{ required: true, whitespace: true, message: 'Enter a relation name' }]}>
            <Input placeholder="For example, Belongs To Organization" />
          </Form.Item>
          <Form.Item label="Relation Description" name="description">
            <Input placeholder="Describe the business semantics of this relation" />
          </Form.Item>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 180px', gap: 12 }}>
          <Form.Item label="Source Object" name="sourceObject" rules={[{ required: true, message: 'Select a source object' }]}>
            <Select options={objectOptions} showSearch optionFilterProp="label" />
          </Form.Item>
          <Form.Item label="Target Object" name="targetObject" rules={[{ required: true, message: 'Select a target object' }]}>
            <Select options={objectOptions} showSearch optionFilterProp="label" />
          </Form.Item>
          <Form.Item label={t('ontology.relation')} name="relationType" rules={[{ required: true, message: 'Select a relation type' }]}>
            <Select
              options={[
                { label: t('ontology.oneToOne'), value: '一对一' },
                { label: t('ontology.oneToMany'), value: '一对多' },
                { label: t('ontology.manyToOne'), value: '多对一' },
                { label: t('ontology.manyToMany'), value: '多对多' },
                { label: t('ontology.custom'), value: '自定义' },
              ]}
            />
          </Form.Item>
        </div>
      </Form>
    </Modal>
  )
}
