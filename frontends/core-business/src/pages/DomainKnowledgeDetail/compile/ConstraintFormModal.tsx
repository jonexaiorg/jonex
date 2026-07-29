import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import i18n from 'i18next';
import { Modal, Form, Input, Select } from 'antd';
import type { ConstraintTargetType, OntologyConstraint, SaveOntologyConstraintPayload } from '@/types/domainKnowledge';
import { constraintTargetTypeLabelKey } from '@/types/domainKnowledge';
import type { ConstraintTargetOptions } from '@/api/domainKnowledge';

const CONSTRAINT_TYPE_OPTIONS = [
  { label: i18n.t('compile.constraintType.mutex'), value: '互斥' },
  { label: i18n.t('compile.constraintType.range'), value: '值域要求' },
  { label: i18n.t('compile.constraintType.unique'), value: '唯一' },
  { label: i18n.t('compile.constraintType.required'), value: '必填' },
  { label: i18n.t('compile.constraintType.custom'), value: 'custom' },
];

interface ConstraintFormValues {
  name: string;
  targetType: ConstraintTargetType;
  targetCode: string;
  constraintType: string;
  expression?: string;
  suggestion?: string;
}

interface Props {
  open: boolean;
  editing: OntologyConstraint | null;
  targetOptions: ConstraintTargetOptions;
  existingNames: string[];
  submitting: boolean;
  onCancel: () => void;
  onSubmit: (payload: SaveOntologyConstraintPayload) => void;
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
  const { t } = useTranslation();
  const TARGET_TYPE_OPTIONS: { label: string; value: ConstraintTargetType }[] = [
    { label: t(constraintTargetTypeLabelKey.entity), value: 'entity' },
    { label: t(constraintTargetTypeLabelKey.attribute), value: 'attribute' },
    { label: t(constraintTargetTypeLabelKey.relation), value: 'relation' },
  ];
  const [form] = Form.useForm<ConstraintFormValues>();
  const [targetType, setTargetType] = useState<ConstraintTargetType>('entity');

  useEffect(() => {
    if (!open) return;
    if (editing) {
      setTargetType(editing.targetType);
      form.setFieldsValue({
        name: editing.name,
        targetType: editing.targetType,
        targetCode: editing.targetCode,
        constraintType: editing.constraintType || 'custom',
        expression: editing.expression,
        suggestion: editing.suggestion,
      });
      return;
    }
    setTargetType('entity');
    form.setFieldsValue({
      name: '',
      targetType: 'entity',
      targetCode: undefined,
      constraintType: 'custom',
      expression: '',
      suggestion: '',
    });
  }, [editing, form, open]);

  const currentOptions = targetOptions[targetType] || [];

  async function handleOk() {
    const values = await form.validateFields();
    const label = (targetOptions[values.targetType] || []).find((o) => o.value === values.targetCode)?.label;
    onSubmit({
      name: values.name.trim(),
      targetType: values.targetType,
      targetCode: values.targetCode,
      targetLabel: label,
      constraintType: values.constraintType || 'custom',
      expression: (values.expression || '').trim(),
      suggestion: (values.suggestion || '').trim(),
    });
  }

  return (
    <Modal
      title={editing ? t('compile.constraintEdit') : t('compile.constraintNew')}
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
        <Form.Item
          label={t('compile.constraint.name')}
          name="name"
          rules={[
            { required: true, whitespace: true, message: t('compile.constraint.nameMessage') },
            {
              validator: (_, value) => {
                const name = (value || '').trim();
                if (!name) return Promise.resolve();
                const clash = existingNames.some((n) => n === name && n !== editing?.name);
                return clash ? Promise.reject(new Error('Constraint name already exists')) : Promise.resolve();
              },
            },
          ]}
        >
          <Input placeholder={t('compile.constraint.namePlaceholder')} />
        </Form.Item>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <Form.Item
            label={t('compile.constraint.targetType')}
            name="targetType"
            rules={[{ required: true, message: t('compile.constraint.targetTypeMessage') }]}
          >
            <Select
              options={TARGET_TYPE_OPTIONS}
              onChange={(v: ConstraintTargetType) => {
                setTargetType(v);
                form.setFieldsValue({ targetCode: undefined });
              }}
            />
          </Form.Item>
          <Form.Item
            label={t('compile.constraint.targetObject')}
            name="targetCode"
            rules={[{ required: true, message: t('compile.constraint.targetObjectMessage') }]}
          >
            <Select
              options={currentOptions}
              showSearch
              optionFilterProp="label"
              placeholder={
                currentOptions.length
                  ? t('compile.constraint.targetSelectPlaceholder')
                  : t('compile.constraint.noTargetPlaceholder')
              }
            />
          </Form.Item>
        </div>
        <Form.Item label={t('compile.constraint.constraintType')} name="constraintType">
          <Select options={CONSTRAINT_TYPE_OPTIONS} />
        </Form.Item>
        <Form.Item label={t('compile.constraint.expression')} name="expression">
          <Input.TextArea rows={2} placeholder={t('compile.constraint.expressionPlaceholder')} />
        </Form.Item>
        <Form.Item label={t('compile.constraint.suggestion')} name="suggestion">
          <Input.TextArea rows={2} placeholder={t('compile.constraint.suggestionPlaceholder')} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
