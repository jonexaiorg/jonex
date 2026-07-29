import React, { useState, useImperativeHandle, forwardRef } from 'react';
import { Modal, Input, Select, message } from 'antd';
import { useTranslation } from 'react-i18next';
import type { TemplateDomain } from '../../api/templateDomains';
import { createDomain, updateDomain } from '../../api/templateDomains';

export interface DomainFormModalHandle {
  open: (domain?: TemplateDomain) => void;
}

interface DomainFormModalProps {
  onSuccess?: () => void;
}

const DomainFormModal = forwardRef<DomainFormModalHandle, DomainFormModalProps>(({ onSuccess }, ref) => {
  const { t } = useTranslation();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingDomain, setEditingDomain] = useState<TemplateDomain | null>(null);
  const [formName, setFormName] = useState('');
  const [formDesc, setFormDesc] = useState('');
  const [formStatus, setFormStatus] = useState('active');
  const [saving, setSaving] = useState(false);

  // 对外暴露方法
  useImperativeHandle(
    ref,
    () => ({
      open(domain?: TemplateDomain) {
        if (domain) {
          setEditingDomain(domain);
          setFormName(domain.name);
          setFormDesc(domain.description || '');
          setFormStatus(domain.status);
        } else {
          setEditingDomain(null);
          setFormName('');
          setFormDesc('');
          setFormStatus('active');
        }
        setModalOpen(true);
      },
    }),
    [],
  );

  const handleSave = async () => {
    if (!formName.trim()) {
      message.warning(t('templateDomains.nameWarning'));
      return;
    }
    setSaving(true);
    try {
      if (editingDomain) {
        await updateDomain(editingDomain.id, {
          name: formName.trim(),
          description: formDesc.trim() || undefined,
          status: formStatus,
        });
        message.success(t('templateDomains.domainUpdated'));
      } else {
        await createDomain({
          name: formName.trim(),
          description: formDesc.trim() || undefined,
          status: formStatus,
        });
        message.success(t('templateDomains.domainCreated'));
      }
      setModalOpen(false);
      onSuccess?.();
    } catch {
      message.error(t('common.operationFailed'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      title={editingDomain ? t('templateDomains.editTitle') : t('templateDomains.createTitle')}
      open={modalOpen}
      onCancel={() => setModalOpen(false)}
      onOk={handleSave}
      okText={t('common.save')}
      cancelText={t('common.cancel')}
      confirmLoading={saving}
      width={520}
    >
      <div className="yx-form-row">
        <label>
          {t('templateDomains.nameLabel')} <span style={{ color: '#dc2626' }}>*</span>
        </label>
        <Input
          placeholder={t('templateDomains.namePlaceholder')}
          value={formName}
          onChange={(e) => setFormName(e.target.value)}
        />
      </div>
      <div className="yx-form-row">
        <label>{t('common.description')}</label>
        <Input.TextArea
          placeholder={t('templateDomains.descPlaceholder')}
          value={formDesc}
          onChange={(e) => setFormDesc(e.target.value)}
          rows={3}
        />
      </div>
      <div className="yx-form-row">
        <label>{t('common.status')}</label>
        <Select
          value={formStatus}
          onChange={(v) => setFormStatus(v)}
          style={{ width: '100%' }}
          options={[
            { label: t('status.active'), value: 'active' },
            { label: t('status.inactive'), value: 'inactive' },
          ]}
        />
      </div>
    </Modal>
  );
});

DomainFormModal.displayName = 'DomainFormModal';

export default DomainFormModal;
