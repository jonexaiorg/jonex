import React, { useState, forwardRef, useImperativeHandle } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal, Button, message } from 'antd';
import { WarningOutlined, DeleteOutlined } from '@ant-design/icons';
import { deleteSpace } from '../../api/domainSpace';
import { useStore } from '../../store';
import { emitSpacesInvalidated, emitSpaceChanged } from '@jonex/shell-sdk';

export interface DeleteSpaceModalHandle {
  open: (spaceName: string) => void;
}

interface DeleteSpaceModalProps {
  spaceId: string;
  onDeleted: () => void;
}

const DeleteSpaceModal = forwardRef<DeleteSpaceModalHandle, DeleteSpaceModalProps>(function DeleteSpaceModal(
  { spaceId, onDeleted },
  ref,
) {
  const { t } = useTranslation();
  const { global } = useStore();

  const [open, setOpen] = useState(false);
  const [spaceName, setSpaceName] = useState('');
  const [deleting, setDeleting] = useState(false);

  useImperativeHandle(
    ref,
    () => ({
      open: (name: string) => {
        setSpaceName(name);
        setOpen(true);
      },
    }),
    [],
  );

  const handleDelete = async () => {
    setDeleting(true);
    try {
      const wasCurrent = global.currentSpaceId === spaceId;
      await deleteSpace(spaceId);
      message.success(t('common.deleteSuccess'));
      setOpen(false);
      await global.refreshSpaces();
      if (wasCurrent) emitSpaceChanged(global.currentSpaceId);
      emitSpacesInvalidated();
      onDeleted();
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('common.deleteFailed'));
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Modal
      wrapClassName="yx-domain-space-modal"
      title={
        <span>
          <WarningOutlined style={{ color: '#ef4444', marginRight: 8 }} />
          {t('domainSpace.confirmDeleteModalTitle')}
        </span>
      }
      open={open}
      onCancel={() => setOpen(false)}
      footer={
        <div style={{ display: 'flex', justifyContent: 'center', gap: 12 }}>
          <Button onClick={() => setOpen(false)}>{t('common.cancel')}</Button>
          <Button danger type="primary" loading={deleting} onClick={handleDelete}>
            {t('common.okText')}
          </Button>
        </div>
      }
      width={420}
    >
      <div style={{ textAlign: 'center', padding: '12px 0' }}>
        <DeleteOutlined style={{ fontSize: 48, color: '#ef4444', marginBottom: 16, display: 'block' }} />
        <p style={{ fontSize: 16, color: '#1e293b', fontWeight: 500 }}>
          {t('domainSpace.confirmDeleteMessage', { name: spaceName })}
        </p>
        <p style={{ fontSize: 13, color: '#94a3b8', marginTop: 8 }}>{t('domainSpace.deleteWarning')}</p>
      </div>
    </Modal>
  );
});

export default DeleteSpaceModal;
