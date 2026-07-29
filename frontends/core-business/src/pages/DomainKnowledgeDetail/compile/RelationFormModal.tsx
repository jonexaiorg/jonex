import React, { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal, Form, Input, Select } from 'antd';
import type { OntologyRelationDef, OntologyRelationType, SaveOntologyRelationPayload } from '@/types/domainKnowledge';
import { RELATION_CARDINALITY_LABEL_KEYS } from './constants';

interface RelationFormValues {
  name: string;
  description: string;
  sourceObject: string;
  targetObject: string;
  relationType: OntologyRelationType;
}

interface Props {
  open: boolean;
  editing: OntologyRelationDef | null;
  objectNames: string[];
  submitting: boolean;
  onCancel: () => void;
  onSubmit: (payload: SaveOntologyRelationPayload) => void;
}

export default function RelationFormModal({ open, editing, objectNames, submitting, onCancel, onSubmit }: Props) {
  const { t } = useTranslation();
  const [form] = Form.useForm<RelationFormValues>();
  const objectOptions = objectNames.map((name) => ({
    label: name,
    value: name,
  }));

  useEffect(() => {
    if (!open) return;
    if (editing) {
      form.setFieldsValue({
        name: editing.name,
        description: editing.description,
        sourceObject: editing.sourceObject,
        targetObject: editing.targetObject,
        relationType: editing.relationType,
      });
      return;
    }
    form.setFieldsValue({
      name: '',
      description: '',
      sourceObject: '',
      targetObject: '',
      relationType: '一对一',
    });
  }, [editing, form, open]);

  async function handleOk() {
    const values = await form.validateFields();
    onSubmit({
      name: values.name.trim(),
      description: (values.description || '').trim(),
      sourceObject: values.sourceObject,
      targetObject: values.targetObject,
      relationType: values.relationType,
      status: editing?.status || 'active',
    });
  }

  return (
    <Modal
      title={editing ? t('compile.relationEdit') : t('compile.relationNew')}
      open={open}
      onCancel={onCancel}
      onOk={handleOk}
      okText={t('common.confirm')}
      cancelText={t('common.cancel')}
      confirmLoading={submitting}
      width={720}
      destroyOnHidden
    >
      <Form form={form} layout="vertical" preserve={false}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <Form.Item
            label={t('compile.relation.name')}
            name="name"
            rules={[{ required: true, whitespace: true, message: t('compile.relation.nameMessage') }]}
          >
            <Input placeholder={t('compile.relation.namePlaceholder')} />
          </Form.Item>
          <Form.Item label={t('compile.relation.description')} name="description">
            <Input placeholder={t('compile.relation.descriptionPlaceholder')} />
          </Form.Item>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 180px', gap: 12 }}>
          <Form.Item
            label={t('compile.relation.sourceObject')}
            name="sourceObject"
            rules={[{ required: true, message: t('compile.relation.sourceObjectMessage') }]}
          >
            <Select options={objectOptions} showSearch optionFilterProp="label" />
          </Form.Item>
          <Form.Item
            label={t('compile.relation.targetObject')}
            name="targetObject"
            rules={[{ required: true, message: t('compile.relation.targetObjectMessage') }]}
          >
            <Select options={objectOptions} showSearch optionFilterProp="label" />
          </Form.Item>
          <Form.Item
            label={t('compile.relation.type')}
            name="relationType"
            rules={[{ required: true, message: t('compile.relation.typeMessage') }]}
          >
            <Select
              options={[
                { label: t('compile.cardinality.oneToOne'), value: '一对一' },
                { label: t('compile.cardinality.oneToMany'), value: '一对多' },
                { label: t('compile.cardinality.manyToOne'), value: '多对一' },
                { label: t('compile.cardinality.manyToMany'), value: '多对多' },
                { label: t('compile.cardinality.custom'), value: '自定义' },
              ]}
            />
          </Form.Item>
        </div>
      </Form>
    </Modal>
  );
}
