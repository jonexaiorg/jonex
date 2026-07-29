import React, { useState, forwardRef, useImperativeHandle } from 'react';
import { Modal, Input, Select, message } from 'antd';
import { useTranslation } from 'react-i18next';
import { createUser, updateUser, type UserItem, type UserCreatePayload, type UserUpdatePayload } from '../../api/users';
import type { TenantItem } from '../../api/tenants';

export interface UserFormModalHandle {
  open: (user?: UserItem) => void;
  close: () => void;
}

interface Props {
  tenants: (TenantItem & { userCount: number })[];
  onSaved: () => Promise<void>;
}

const UserFormModal = forwardRef<UserFormModalHandle, Props>(({ tenants, onSaved }, ref) => {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<UserItem | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    username: '',
    password: '',
    display_name: '',
    email: '',
    role: 'user',
    tenant_id: '',
  });

  useImperativeHandle(
    ref,
    () => ({
      open(user) {
        if (user) {
          setEditing(user);
          setForm({
            username: user.username,
            password: '',
            display_name: user.display_name || '',
            email: user.email || '',
            role: user.role,
            tenant_id: user.tenant_id,
          });
        } else {
          setEditing(null);
          setForm({
            username: '',
            password: '',
            display_name: '',
            email: '',
            role: 'user',
            tenant_id: tenants[0]?.id || '',
          });
        }
        setOpen(true);
      },
      close() {
        setOpen(false);
      },
    }),
    [tenants],
  );

  const handleSave = async () => {
    if (!editing && !form.username) {
      message.warning(t('userManagement.requiredUsername'));
      return;
    }
    if (!editing && !form.password) {
      message.warning(t('userManagement.requiredPassword'));
      return;
    }
    setSubmitting(true);
    try {
      if (editing) {
        const payload: UserUpdatePayload = { display_name: form.display_name, email: form.email, role: form.role };
        await updateUser(editing.id, payload);
        message.success(t('userManagement.updated'));
      } else {
        const payload: UserCreatePayload = {
          username: form.username,
          password: form.password,
          display_name: form.display_name,
          email: form.email,
          role: form.role,
        };
        await createUser(payload);
        message.success(t('userManagement.created'));
      }
      setOpen(false);
      await onSaved();
    } catch (e: unknown) {
      message.error(e instanceof Error ? e.message : t('userManagement.saveFailed'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      title={editing ? t('userManagement.editUser') : t('userManagement.createUser')}
      open={open}
      onCancel={() => setOpen(false)}
      onOk={handleSave}
      okText={t('common.save')}
      cancelText={t('common.cancel')}
      confirmLoading={submitting}
      width={520}
    >
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 14 }}>
        <div>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: 13 }}>
            {t('userManagement.username')} <span style={{ color: '#dc2626' }}>*</span>
          </label>
          <Input
            placeholder={t('userManagement.placeholderUsername')}
            value={form.username}
            disabled={!!editing}
            onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
          />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: 13 }}>
            {t('userManagement.displayName')} <span style={{ color: '#dc2626' }}>*</span>
          </label>
          <Input
            placeholder={t('userManagement.placeholderDisplayName')}
            value={form.display_name}
            onChange={(e) => setForm((f) => ({ ...f, display_name: e.target.value }))}
          />
        </div>
      </div>
      <div style={{ marginBottom: 14 }}>
        <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: 13 }}>
          {t('userManagement.email')} <span style={{ color: '#dc2626' }}>*</span>
        </label>
        <Input
          placeholder={t('userManagement.placeholderEmail')}
          value={form.email}
          onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
        />
      </div>
      <div style={{ marginBottom: 14 }}>
        <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: 13 }}>
          {t('userManagement.role')} <span style={{ color: '#dc2626' }}>*</span>
        </label>
        <Select
          value={form.role}
          onChange={(v) => setForm((f) => ({ ...f, role: v }))}
          style={{ width: '100%' }}
          options={[
            { label: t('auth.systemAdmin'), value: 'admin' },
            { label: t('userManagement.roleUser'), value: 'user' },
          ]}
        />
      </div>
      {!editing && (
        <div style={{ marginTop: 14 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: 13 }}>
            {t('auth.password')} <span style={{ color: '#dc2626' }}>*</span>
          </label>
          <Input.Password
            placeholder={t('userManagement.placeholderPassword')}
            value={form.password}
            onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
          />
        </div>
      )}
      {editing && (
        <div style={{ marginTop: 14 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: 13 }}>
            {t('userManagement.newPassword')}
          </label>
          <Input.Password
            placeholder={t('userManagement.placeholderNewPassword')}
            value={form.password}
            onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
          />
        </div>
      )}
    </Modal>
  );
});

UserFormModal.displayName = 'UserFormModal';
export default UserFormModal;
