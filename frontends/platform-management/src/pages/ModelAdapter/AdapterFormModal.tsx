import React, { useState, forwardRef, useImperativeHandle } from 'react';
import { useTranslation } from 'react-i18next';
import { Form, Input, Modal, message } from 'antd';
import {
  createProvider,
  updateProvider,
  type ModelProviderItem,
  type SaveProviderPayload,
} from '../../api/modelProviders';

export interface AdapterFormModalHandle {
  open: () => void;
  openEdit: (data: ModelProviderItem) => void;
}

interface Props {
  onSuccess: () => void;
}

const AdapterFormModal = forwardRef<AdapterFormModalHandle, Props>(({ onSuccess }, ref) => {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<ModelProviderItem | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();

  useImperativeHandle(ref, () => ({
    open() {
      setEditing(null);
      form.setFieldsValue({ name: '', provider_type: 'llm', endpoint: '', model_name: '' });
      setOpen(true);
    },
    openEdit(data: ModelProviderItem) {
      setEditing(data);
      form.setFieldsValue({
        name: data.name,
        provider_type: data.provider_type,
        endpoint: data.endpoint || '',
        model_name: data.model_name || '',
      });
      setOpen(true);
    },
  }));

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      const payload: SaveProviderPayload = {
        name: values.name,
        provider_type: values.provider_type,
        endpoint: values.endpoint || undefined,
        model_name: values.model_name || undefined,
      };
      if (editing) {
        await updateProvider(editing.id, payload);
        message.success(t('modelAdapter.updated'));
      } else {
        await createProvider(payload);
        message.success(t('modelAdapter.created'));
      }
      setOpen(false);
      onSuccess();
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      message.error(err instanceof Error ? err.message : t('modelAdapter.saveFailed'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      title={editing ? t('modelAdapter.editModel') : t('modelAdapter.addModel')}
      open={open}
      onCancel={() => setOpen(false)}
      onOk={handleSave}
      okText={t('common.save')}
      cancelText={t('common.cancel')}
      confirmLoading={submitting}
      width={480}
      destroyOnClose
    >
      <Form form={form} layout="vertical" style={{ marginTop: 8 }}>
        <Form.Item name="provider_type" hidden initialValue="llm">
          <Input type="hidden" />
        </Form.Item>
        <Form.Item
          name="name"
          label={t('modelAdapter.name')}
          rules={[{ required: true, message: t('modelAdapter.nameRequired') }]}
        >
          <Input placeholder={t('modelAdapter.namePlaceholder')} />
        </Form.Item>
        <Form.Item name="model_name" label={t('modelAdapter.modelName')}>
          <Input placeholder={t('modelAdapter.modelNamePlaceholder')} />
        </Form.Item>
        <Form.Item name="endpoint" label={t('modelAdapter.endpoint')}>
          <Input placeholder={t('modelAdapter.endpointPlaceholder')} />
        </Form.Item>
      </Form>
    </Modal>
  );
});

AdapterFormModal.displayName = 'AdapterFormModal';

export default AdapterFormModal;
