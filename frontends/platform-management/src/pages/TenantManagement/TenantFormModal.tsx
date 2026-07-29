import React, { forwardRef, useImperativeHandle, useState, useCallback } from 'react';
import { Modal, Input, Select, message } from 'antd';
import { useTranslation } from 'react-i18next';
import {
  createTenant,
  updateTenant,
  type TenantItem,
  type TenantCreatePayload,
  type TenantUpdatePayload,
} from '../../api/tenants';

export interface TenantFormModalRef {
  openCreate: () => void;
  openEdit: (item: TenantItem) => void;
}

interface FormState {
  id: string;
  name: string;
  description: string;
  plan_type: string;
}

const INITIAL_FORM: FormState = { id: '', name: '', description: '', plan_type: 'free' };

const TenantFormModal = forwardRef<TenantFormModalRef, { onSaved: () => void }>(function TenantFormModal(
  { onSaved },
  ref,
) {
  const { t } = useTranslation();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<TenantItem | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState<FormState>(INITIAL_FORM);

  useImperativeHandle(ref, () => ({
    openCreate() {
      setEditing(null);
      setForm({ ...INITIAL_FORM });
      setModalOpen(true);
    },
    openEdit(item: TenantItem) {
      setEditing(item);
      setForm({ id: item.id, name: item.name, description: item.description || '', plan_type: item.plan_type });
      setModalOpen(true);
    },
  }));

  const handleSave = useCallback(async () => {
    if (!form.id && !editing) {
      message.warning(t('tenantManagement.requiredTenantId'));
      return;
    }
    if (!form.name) {
      message.warning(t('tenantManagement.requiredName'));
      return;
    }
    setSubmitting(true);
    try {
      if (editing) {
        const payload: TenantUpdatePayload = {
          name: form.name,
          description: form.description,
          plan_type: form.plan_type,
        };
        await updateTenant(editing.id, payload);
        message.success(t('tenantManagement.updated'));
      } else {
        const payload: TenantCreatePayload = {
          id: form.id,
          name: form.name,
          description: form.description,
          plan_type: form.plan_type,
        };
        await createTenant(payload);
        message.success(t('tenantManagement.created'));
      }
      setModalOpen(false);
      onSaved();
    } catch (e: unknown) {
      message.error(e instanceof Error ? e.message : t('tenantManagement.saveFailed'));
    } finally {
      setSubmitting(false);
    }
  }, [editing, form, onSaved, t]);

  return (
    <Modal
      title={editing ? t('tenantManagement.editTenant') : t('tenantManagement.createTenant')}
      open={modalOpen}
      onCancel={() => setModalOpen(false)}
      onOk={handleSave}
      okText={t('common.save')}
      cancelText={t('common.cancel')}
      confirmLoading={submitting}
      width={480}
    >
      {!editing && (
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>
            {t('tenantManagement.tenantId')} <span style={{ color: '#dc2626' }}>*</span>
          </label>
          <Input
            placeholder={t('tenantManagement.placeholderTenantId')}
            value={form.id}
            onChange={(e) => setForm((f) => ({ ...f, id: e.target.value }))}
          />
        </div>
      )}
      <div style={{ marginBottom: 16 }}>
        <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>
          {t('tenantManagement.name')} <span style={{ color: '#dc2626' }}>*</span>
        </label>
        <Input
          placeholder={t('tenantManagement.placeholderName')}
          value={form.name}
          onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
        />
      </div>
      <div style={{ marginBottom: 16 }}>
        <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>
          {t('tenantManagement.description')}
        </label>
        <Input
          placeholder={t('tenantManagement.placeholderDescription')}
          value={form.description}
          onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
        />
      </div>
      <div>
        <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>{t('tenantManagement.plan')}</label>
        <Select
          value={form.plan_type}
          onChange={(v) => setForm((f) => ({ ...f, plan_type: v }))}
          style={{ width: '100%' }}
          options={[
            { label: t('tenantManagement.planFree'), value: 'free' },
            { label: t('tenantManagement.planPro'), value: 'pro' },
            { label: t('tenantManagement.planEnterprise'), value: 'enterprise' },
          ]}
        />
      </div>
    </Modal>
  );
});

export default TenantFormModal;
