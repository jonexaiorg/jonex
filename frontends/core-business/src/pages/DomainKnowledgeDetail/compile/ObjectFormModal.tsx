import React, { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Modal, Form, Input, Select, Switch, Button } from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import type { OntologyAttrType, OntologyObjectDef, SaveOntologyObjectPayload } from '@/types/domainKnowledge'
import { ATTR_TYPE_OPTIONS } from './constants'

interface AttrFormItem {
  id?: string
  name?: string
  description?: string
  type?: OntologyAttrType
  isPrimaryKey?: boolean
}

interface ObjectFormValues {
  name: string
  description: string
  requirement: string
  attributes?: AttrFormItem[]
}

interface Props {
  open: boolean
  editing: OntologyObjectDef | null
  submitting: boolean
  onCancel: () => void
  onSubmit: (payload: SaveOntologyObjectPayload) => void
}

export default function ObjectFormModal({ open, editing, submitting, onCancel, onSubmit }: Props) {
  const { t } = useTranslation()
  const [form] = Form.useForm<ObjectFormValues>()

  useEffect(() => {
    if (!open) return
    if (editing) {
      form.setFieldsValue({
        name: editing.name,
        description: editing.description,
        requirement: editing.requirement,
        attributes: editing.attributes.map((attr) => ({
          id: attr.id,
          name: attr.name,
          description: attr.description,
          type: attr.type,
          isPrimaryKey: attr.isPrimaryKey,
        })),
      })
      return
    }
    form.setFieldsValue({
      name: '',
      description: '',
      requirement: '',
      attributes: [{ type: '字符串', isPrimaryKey: false }],
    })
  }, [editing, form, open])

  async function handleOk() {
    const values = await form.validateFields()
    onSubmit({
      name: values.name.trim(),
      description: (values.description || '').trim(),
      requirement: (values.requirement || '').trim(),
      status: editing?.status || 'active',
      attributes: (values.attributes || [])
        .filter((item) => (item.name || '').trim())
        .map((item) => ({
          id: item.id || '',
          name: (item.name || '').trim(),
          description: (item.description || '').trim(),
          type: item.type || '字符串',
          isPrimaryKey: Boolean(item.isPrimaryKey),
        })),
    })
  }

  return (
    <Modal
      title={editing ? t('compile.editObject') : t('compile.createObject')}
      open={open}
      onCancel={onCancel}
      onOk={handleOk}
      okText="Confirm"
      cancelText="Cancel"
      confirmLoading={submitting}
      width={860}
      destroyOnHidden
    >
      <Form form={form} layout="vertical" preserve={false}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <Form.Item label="Object Name" name="name" rules={[{ required: true, whitespace: true, message: 'Enter an object name' }]}>
            <Input placeholder="For example, Financial Product" />
          </Form.Item>
          <Form.Item label="Object Description" name="description">
            <Input placeholder="Briefly describe the business meaning of this object" />
          </Form.Item>
        </div>
        <Form.Item label="Additional Requirements" name="requirement">
          <Input.TextArea rows={2} placeholder="Add constraints, extraction requirements, or validation rules" />
        </Form.Item>
        <Form.List name="attributes">
          {(fields, { add, remove }) => (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <label>Attribute Definitions</label>
                <Button type="dashed" size="small" icon={<PlusOutlined />} onClick={() => add({ type: '字符串', isPrimaryKey: false })}>
                  Add Attribute
                </Button>
              </div>
              {fields.map((field) => (
                <div key={field.key} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 130px 90px 40px', gap: 8, marginBottom: 8 }}>
                  <Form.Item
                    name={[field.name, 'name']}
                    rules={[{ required: true, whitespace: true, message: 'Attribute name is required' }]}
                    style={{ marginBottom: 0 }}
                  >
                    <Input placeholder="Attribute Name" />
                  </Form.Item>
                  <Form.Item name={[field.name, 'description']} style={{ marginBottom: 0 }}>
                    <Input placeholder="Attribute Description" />
                  </Form.Item>
                  <Form.Item name={[field.name, 'type']} style={{ marginBottom: 0 }}>
                    <Select options={ATTR_TYPE_OPTIONS.map((option) => ({
                      value: option.value,
                      label: t(option.labelKey),
                    }))} />
                  </Form.Item>
                  <Form.Item name={[field.name, 'isPrimaryKey']} valuePropName="checked" style={{ marginBottom: 0 }}>
                    <Switch checkedChildren="Primary Key" unCheckedChildren="Standard" />
                  </Form.Item>
                  <Button danger type="text" icon={<DeleteOutlined />} onClick={() => remove(field.name)} />
                </div>
              ))}
            </div>
          )}
        </Form.List>
      </Form>
    </Modal>
  )
}
