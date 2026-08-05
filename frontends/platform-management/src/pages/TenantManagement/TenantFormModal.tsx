import React, { forwardRef, useImperativeHandle, useState } from 'react';
import { Form, Input, Modal, Select, message } from 'antd';
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

const TenantFormModal = forwardRef<TenantFormModalRef, { onSaved: () => void }>(function TenantFormModal(
  { onSaved },
  ref,
) {
  const { t } = useTranslation();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<TenantItem | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();

  useImperativeHandle(ref, () => ({
    openCreate() {
      setEditing(null);
      form.setFieldsValue({ id: '', name: '', description: '', plan_type: 'free' });
      setModalOpen(true);
    },
    openEdit(item: TenantItem) {
      setEditing(item);
      form.setFieldsValue({
        id: item.id,
        name: item.name,
        description: item.description || '',
        plan_type: item.plan_type,
      });
      setModalOpen(true);
    },
  }));

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      if (editing) {
        const payload: TenantUpdatePayload = {
          name: values.name,
          description: values.description,
          plan_type: values.plan_type,
        };
        await updateTenant(editing.id, payload);
        message.success(t('tenantManagement.updated'));
      } else {
        const payload: TenantCreatePayload = {
          id: values.id,
          name: values.name,
          description: values.description,
          plan_type: values.plan_type,
        };
        await createTenant(payload);
        message.success(t('tenantManagement.created'));
      }
      setModalOpen(false);
      onSaved();
    } catch (e: unknown) {
      if (e && typeof e === 'object' && 'errorFields' in e) return;
      message.error(e instanceof Error ? e.message : t('tenantManagement.saveFailed'));
    } finally {
      setSubmitting(false);
    }
  };

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
      destroyOnClose
    >
      <Form form={form} layout="vertical" style={{ marginTop: 8 }}>
        {!editing && (
          <Form.Item
            name="id"
            label={t('tenantManagement.tenantId')}
            rules={[{ required: true, message: t('tenantManagement.requiredTenantId') }]}
          >
            <Input placeholder={t('tenantManagement.placeholderTenantId')} />
          </Form.Item>
        )}
        <Form.Item
          name="name"
          label={t('tenantManagement.name')}
          rules={[{ required: true, message: t('tenantManagement.requiredName') }]}
        >
          <Input placeholder={t('tenantManagement.placeholderName')} />
        </Form.Item>
        <Form.Item name="description" label={t('tenantManagement.description')}>
          <Input placeholder={t('tenantManagement.placeholderDescription')} />
        </Form.Item>
        <Form.Item name="plan_type" label={t('tenantManagement.plan')}>
          <Select
            options={[
              { label: t('tenantManagement.planFree'), value: 'free' },
              { label: t('tenantManagement.planPro'), value: 'pro' },
              { label: t('tenantManagement.planEnterprise'), value: 'enterprise' },
            ]}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
});

export default TenantFormModal;
