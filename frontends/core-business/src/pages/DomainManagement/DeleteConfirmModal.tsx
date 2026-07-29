import React from 'react';
import { Modal, Button } from 'antd';
import { DeleteOutlined, StopOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { DomainServiceItem } from '../../types/domainService';

interface DeleteConfirmModalProps {
  open: boolean;
  deleteTarget: DomainServiceItem | null;
  submitting: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export default function DeleteConfirmModal({
  open,
  deleteTarget,
  submitting,
  onCancel,
  onConfirm,
}: DeleteConfirmModalProps) {
  const { t } = useTranslation();

  return (
    <Modal
      wrapClassName="yx-domain-space-modal"
      title={
        <span>
          <StopOutlined style={{ color: '#ef4444', marginRight: 8 }} />
          {t('common.confirmDeleteTitle')}
        </span>
      }
      open={open}
      onCancel={onCancel}
      footer={
        <div style={{ display: 'flex', justifyContent: 'center', gap: 12 }}>
          <Button onClick={onCancel}>{t('common.cancel')}</Button>
          <Button danger type="primary" loading={submitting} onClick={onConfirm}>
            {t('common.okText')}
          </Button>
        </div>
      }
      width={420}
    >
      <div style={{ textAlign: 'center', padding: '12px 0' }}>
        <DeleteOutlined
          style={{
            fontSize: 48,
            color: '#ef4444',
            marginBottom: 16,
            display: 'block',
          }}
        />
        <p style={{ fontSize: 16, color: '#1e293b', fontWeight: 500 }}>
          {t('common.confirmDeleteContent', { name: deleteTarget?.name || '' })}
        </p>
        <p style={{ fontSize: 13, color: '#94a3b8', marginTop: 8 }}>{t('common.deleteWarning')}</p>
      </div>
    </Modal>
  );
}
