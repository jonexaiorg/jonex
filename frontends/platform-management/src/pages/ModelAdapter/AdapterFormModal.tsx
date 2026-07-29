import React, { useState, forwardRef, useImperativeHandle, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Input, Modal, message } from 'antd';
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
  const [form, setForm] = useState({ name: '', provider_type: 'llm', endpoint: '', model_name: '' });

  const resetForm = () => {
    setEditing(null);
    setForm({ name: '', provider_type: 'llm', endpoint: '', model_name: '' });
  };

  useImperativeHandle(ref, () => ({
    open() {
      resetForm();
      setOpen(true);
    },
    openEdit(data: ModelProviderItem) {
      setEditing(data);
      setForm({
        name: data.name,
        provider_type: data.provider_type,
        endpoint: data.endpoint || '',
        model_name: data.model_name || '',
      });
      setOpen(true);
    },
  }));

  const handleSave = useCallback(async () => {
    if (!form.name) {
      message.warning(t('modelAdapter.nameRequired'));
      return;
    }
    setSubmitting(true);
    try {
      const payload: SaveProviderPayload = {
        name: form.name,
        provider_type: form.provider_type,
        endpoint: form.endpoint || undefined,
        model_name: form.model_name || undefined,
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
      message.error(err instanceof Error ? err.message : t('modelAdapter.saveFailed'));
    } finally {
      setSubmitting(false);
    }
  }, [form, editing, t, onSuccess]);

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
    >
      <div style={{ marginBottom: 16 }}>
        <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>
          {t('modelAdapter.name')} <span style={{ color: '#dc2626' }}>*</span>
        </label>
        <Input
          placeholder={t('modelAdapter.namePlaceholder')}
          value={form.name}
          onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
        />
      </div>
      <div style={{ marginBottom: 16 }}>
        <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>{t('modelAdapter.modelName')}</label>
        <Input
          placeholder={t('modelAdapter.modelNamePlaceholder')}
          value={form.model_name}
          onChange={(e) => setForm((f) => ({ ...f, model_name: e.target.value }))}
        />
      </div>
      <div style={{ marginBottom: 16 }}>
        <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>{t('modelAdapter.endpoint')}</label>
        <Input
          placeholder={t('modelAdapter.endpointPlaceholder')}
          value={form.endpoint}
          onChange={(e) => setForm((f) => ({ ...f, endpoint: e.target.value }))}
        />
      </div>
    </Modal>
  );
});

AdapterFormModal.displayName = 'AdapterFormModal';

export default AdapterFormModal;
