import React, { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal, Form, Input, Select, InputNumber } from 'antd';
import type { CompileStep, SaveCompileStepPayload, CompileScope, CompileTrigger } from '@/types/domainKnowledge';
import { COMPILE_SCOPE_OPTIONS, COMPILE_TRIGGER_OPTIONS, SKILL_OPTIONS } from './constants';

interface StepFormValues {
  order: number;
  name: string;
  prompt?: string;
  scope: CompileScope;
  trigger: CompileTrigger;
  skill?: string;
  template?: string;
}
interface Props {
  open: boolean;
  editing: CompileStep | null;
  submitting: boolean;
  onCancel: () => void;
  onSubmit: (payload: SaveCompileStepPayload) => void;
}

export default function StepFormModal({ open, editing, submitting, onCancel, onSubmit }: Props) {
  const { t } = useTranslation();
  const [form] = Form.useForm<StepFormValues>();

  useEffect(() => {
    if (!open) return;
    if (editing) {
      form.setFieldsValue({
        order: editing.order,
        name: editing.name,
        prompt: editing.prompt,
        scope: editing.scope,
        trigger: editing.trigger,
        skill: editing.skill,
        template: editing.template,
      });
    } else {
      form.setFieldsValue({
        order: undefined as any,
        name: '',
        prompt: '',
        scope: 'single',
        trigger: 'upload',
        skill: '',
        template: '',
      });
    }
  }, [open, editing, form]);

  const handleOk = async () => {
    const v = await form.validateFields();
    onSubmit({
      order: Number(v.order),
      name: v.name.trim(),
      prompt: (v.prompt || '').trim(),
      skill: v.skill || '',
      scope: v.scope,
      trigger: v.trigger,
      template: (v.template || '').trim(),
    });
  };

  return (
    <Modal
      title={editing ? t('compile.step.edit') : t('compile.step.create')}
      open={open}
      onCancel={onCancel}
      onOk={handleOk}
      okText={t('common.save')}
      cancelText={t('common.cancel')}
      confirmLoading={submitting}
      width={620}
      destroyOnHidden
    >
      <Form form={form} layout="vertical" preserve={false}>
        <div style={{ display: 'flex', gap: 12 }}>
          <Form.Item
            label={t('compile.step.order')}
            name="order"
            rules={[{ required: true, message: t('compile.step.orderMessage') }]}
            style={{ width: 160 }}
          >
            <InputNumber min={1} style={{ width: '100%' }} placeholder={t('compile.step.orderPlaceholder')} />
          </Form.Item>
          <Form.Item
            label={t('compile.step.name')}
            name="name"
            rules={[{ required: true, whitespace: true, message: t('compile.step.nameMessage') }]}
            style={{ flex: 1 }}
          >
            <Input placeholder={t('compile.step.namePlaceholder')} />
          </Form.Item>
        </div>
        <Form.Item label={t('compile.step.prompt')} name="prompt">
          <Input.TextArea rows={3} placeholder={t('compile.step.promptPlaceholder')} />
        </Form.Item>
        <div style={{ display: 'flex', gap: 12 }}>
          <Form.Item
            label={t('compile.step.scope')}
            name="scope"
            rules={[{ required: true, message: t('compile.step.scopeMessage') }]}
            style={{ flex: 1 }}
          >
            <Select options={COMPILE_SCOPE_OPTIONS} />
          </Form.Item>
          <Form.Item label={t('compile.step.trigger')} name="trigger" style={{ flex: 1 }}>
            <Select options={COMPILE_TRIGGER_OPTIONS} />
          </Form.Item>
        </div>
        <Form.Item label={t('compile.step.skill')} name="skill">
          <Select options={SKILL_OPTIONS} />
        </Form.Item>
        <Form.Item label={t('compile.step.template')} name="template">
          <Input.TextArea rows={2} placeholder={t('compile.step.templatePlaceholder')} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
