import React, { useState, forwardRef, useImperativeHandle } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal, Input, message } from 'antd';
import { createRole } from '../../api/roles';

export interface NewRoleModalRef {
  open: () => void;
}

interface Props {
  onCreated: () => void;
}

const NewRoleModal = forwardRef<NewRoleModalRef, Props>(({ onCreated }, ref) => {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');

  useImperativeHandle(ref, () => ({
    open: () => {
      setName('');
      setOpen(true);
    },
  }));

  const handleCreate = async () => {
    if (!name) {
      message.warning(t('rolePermission.nameRequired'));
      return;
    }
    try {
      await createRole({ name });
      message.success(t('rolePermission.roleCreated'));
      setOpen(false);
      onCreated();
    } catch (e: unknown) {
      message.error(e instanceof Error ? e.message : t('rolePermission.saveFailed'));
    }
  };

  const handleCancel = () => {
    setOpen(false);
  };

  return (
    <Modal
      title={t('rolePermission.newRole')}
      open={open}
      onCancel={handleCancel}
      onOk={handleCreate}
      okText={t('rolePermission.create')}
      cancelText={t('common.cancel')}
    >
      <Input placeholder={t('rolePermission.roleName')} value={name} onChange={(e) => setName(e.target.value)} />
    </Modal>
  );
});

NewRoleModal.displayName = 'NewRoleModal';
export default NewRoleModal;
