import React, { useState, useCallback, forwardRef, useImperativeHandle } from 'react';
import { useTranslation } from 'react-i18next';
import { Button, Checkbox, Form, Input, Modal, Select, message } from 'antd';
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import { createTemplateObject, updateTemplateObject } from '../../api/templateScenarios';
import type { TemplateObject } from '../../api/templateScenarios';

const ATTRIBUTE_TYPE_VALUES = ['字符串', '数值', '日期', '枚举', '布尔', '文本'] as const;

type AttributeFormItem = {
  id?: string;
  name?: string;
  desc?: string;
  type?: string;
  isPrimary?: boolean;
};

type ObjectFormValues = {
  name: string;
  desc?: string;
  attrs?: AttributeFormItem[];
};

function createDraftId(prefix: string) {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
}

function isPrimaryKey(value: boolean | number | undefined) {
  return value === true || value === 1;
}

function getErrorMessage(error: unknown, fallback: string) {
  const err = error as { response?: { data?: { message?: string } }; message?: string };
  return err.response?.data?.message || err.message || fallback;
}

export interface ObjectModalHandle {
  openCreate: () => void;
  openEdit: (item: TemplateObject) => void;
}

interface ObjectModalProps {
  selectedSceneId: string | null;
  attributeTypeOptions: Array<{ label: string; value: string }>;
  onSaved: () => void;
}

const ObjectModal = forwardRef<ObjectModalHandle, ObjectModalProps>(function ObjectModal(
  { selectedSceneId, attributeTypeOptions, onSaved },
  ref,
) {
  const { t } = useTranslation();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingObject, setEditingObject] = useState<TemplateObject | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [objectForm] = Form.useForm<ObjectFormValues>();

  useImperativeHandle(
    ref,
    () => ({
      openCreate: () => {
        setEditingObject(null);
        objectForm.setFieldsValue({
          name: '',
          desc: '',
          attrs: [{ id: createDraftId('attr'), name: '', desc: '', type: ATTRIBUTE_TYPE_VALUES[0], isPrimary: false }],
        });
        setModalOpen(true);
      },
      openEdit: (item: TemplateObject) => {
        setEditingObject(item);
        objectForm.setFieldsValue({
          name: item.name,
          desc: item.description || '',
          attrs: item.attributes.map((attr) => ({
            id: attr.id,
            name: attr.attr_name,
            desc: attr.description || '',
            type: attr.attr_type,
            isPrimary: isPrimaryKey(attr.is_primary_key),
          })),
        });
        setModalOpen(true);
      },
    }),
    [objectForm],
  );

  const handleSave = useCallback(async () => {
    if (!selectedSceneId) return;
    const values = await objectForm.validateFields();
    const attributes = (values.attrs || []).map((attr, index) => ({
      attr_name: attr.name?.trim() || '',
      description: attr.desc?.trim() || '',
      attr_type: attr.type || ATTRIBUTE_TYPE_VALUES[0],
      is_primary_key: Boolean(attr.isPrimary),
      sort_order: index,
    }));

    setSubmitting(true);
    try {
      if (editingObject) {
        await updateTemplateObject(editingObject.id, {
          name: values.name.trim(),
          description: values.desc?.trim() || '',
          attributes,
        });
        message.success(t('templateScenarios.objectUpdated'));
      } else {
        await createTemplateObject(selectedSceneId, {
          name: values.name.trim(),
          description: values.desc?.trim() || '',
          attributes,
        });
        message.success(t('templateScenarios.objectCreated'));
      }
      setModalOpen(false);
      onSaved();
    } catch (error) {
      message.error(
        getErrorMessage(
          error,
          editingObject ? t('templateScenarios.updateObjectFailed') : t('templateScenarios.createObjectFailed'),
        ),
      );
    } finally {
      setSubmitting(false);
    }
  }, [selectedSceneId, editingObject, objectForm, onSaved, t]);

  return (
    <Modal
      title={editingObject ? t('templateScenarios.editObject') : t('templateScenarios.createObjectTitle')}
      open={modalOpen}
      onCancel={() => setModalOpen(false)}
      onOk={handleSave}
      okText={t('common.save')}
      cancelText={t('common.cancel')}
      confirmLoading={submitting}
      width={820}
    >
      <Form form={objectForm} layout="vertical" className="template-scenarios-form">
        <Form.Item
          label={t('common.name')}
          name="name"
          rules={[{ required: true, whitespace: true, message: t('templateScenarios.objectNameInput') }]}
        >
          <Input placeholder={t('templateScenarios.objectNameInput')} />
        </Form.Item>
        <Form.Item label={t('common.description')} name="desc">
          <Input.TextArea placeholder={t('templateScenarios.objectDescPlaceholder')} rows={3} />
        </Form.Item>
        <Form.List name="attrs">
          {(fields, { add, remove }) => (
            <div className="template-scenarios-attr-editor">
              <div className="template-scenarios-attr-editor-head">
                <label>{t('templateScenarios.attrDefSection')}</label>
                <Button
                  type="dashed"
                  size="small"
                  icon={<PlusOutlined />}
                  onClick={() =>
                    add({
                      id: createDraftId('attr'),
                      name: '',
                      desc: '',
                      type: ATTRIBUTE_TYPE_VALUES[0],
                      isPrimary: false,
                    })
                  }
                >
                  {t('templateScenarios.addAttribute')}
                </Button>
              </div>
              {fields.map((field) => (
                <div className="template-scenarios-attr-row" key={field.key}>
                  <Form.Item name={[field.name, 'id']} hidden>
                    <Input />
                  </Form.Item>
                  <Form.Item
                    name={[field.name, 'name']}
                    rules={[{ required: true, whitespace: true, message: t('templateScenarios.attrNameRequired') }]}
                  >
                    <Input placeholder={t('templateScenarios.attrNamePlaceholder')} />
                  </Form.Item>
                  <Form.Item name={[field.name, 'desc']}>
                    <Input placeholder={t('templateScenarios.attrDescPlaceholder')} />
                  </Form.Item>
                  <Form.Item name={[field.name, 'type']}>
                    <Select options={attributeTypeOptions} />
                  </Form.Item>
                  <Form.Item name={[field.name, 'isPrimary']} valuePropName="checked">
                    <Checkbox>{t('templateScenarios.uniquePrimaryKey')}</Checkbox>
                  </Form.Item>
                  <Button danger type="text" icon={<DeleteOutlined />} onClick={() => remove(field.name)} />
                </div>
              ))}
            </div>
          )}
        </Form.List>
      </Form>
    </Modal>
  );
});

export default ObjectModal;
