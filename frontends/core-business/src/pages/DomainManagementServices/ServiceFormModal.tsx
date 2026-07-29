import React, { useState, useCallback, forwardRef, useImperativeHandle } from 'react';
import { useTranslation } from 'react-i18next';
import { Input, Modal, Select, message } from 'antd';
import { EditOutlined, PlusCircleOutlined } from '@ant-design/icons';
import { createService, updateService } from '../../api/domainService';
import type { DomainServiceItem, DomainServiceFormData, KnowledgeBaseOption } from '../../types/domainService';

export interface ServiceFormModalHandle {
  openCreate: () => void;
  openEdit: (item: DomainServiceItem) => void;
}

interface ServiceFormModalProps {
  spaceId: string | null;
  availableKbs: KnowledgeBaseOption[];
  onSaved: () => void;
}

const ServiceFormModal = forwardRef<ServiceFormModalHandle, ServiceFormModalProps>(function ServiceFormModal(
  { spaceId, availableKbs, onSaved },
  ref,
) {
  const { t } = useTranslation();

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<DomainServiceItem | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [formName, setFormName] = useState('');
  const [formDomainType, setFormDomainType] = useState('');
  const [formStatus, setFormStatus] = useState(true);
  const [formKbIds, setFormKbIds] = useState<string[]>([]);

  useImperativeHandle(
    ref,
    () => ({
      openCreate: () => {
        setEditing(null);
        setFormName('');
        setFormDomainType('');
        setFormStatus(true);
        setFormKbIds([]);
        setFormOpen(true);
      },
      openEdit: (item: DomainServiceItem) => {
        setEditing(item);
        setFormName(item.name);
        setFormDomainType(item.domain_type || '');
        setFormStatus(item.status === 'active');
        setFormKbIds(item.kb_ids || []);
        setFormOpen(true);
      },
    }),
    [],
  );

  const toggleKb = useCallback((kbId: string) => {
    setFormKbIds((prev) => (prev.includes(kbId) ? prev.filter((id) => id !== kbId) : [...prev, kbId]));
  }, []);

  const handleSave = useCallback(async () => {
    if (!formName.trim()) {
      message.warning(t('domainManagement.nameRequired'));
      return;
    }
    if (!spaceId) {
      message.warning(t('domainManagement.spaceRequired'));
      return;
    }
    setSubmitting(true);
    try {
      const data: DomainServiceFormData = {
        name: formName.trim(),
        space_id: spaceId!,
        domain_type: formDomainType || undefined,
        status: formStatus ? 'active' : 'inactive',
        kb_ids: formKbIds,
      };
      if (editing) {
        await updateService(editing.id, data);
      } else {
        await createService(data);
      }
      message.success(t('common.saveSuccess'));
      setFormOpen(false);
      onSaved();
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('common.saveFailed'));
    } finally {
      setSubmitting(false);
    }
  }, [formName, spaceId, formDomainType, formStatus, formKbIds, editing, onSaved, t]);

  const typeOptions = [
    { value: 'retrieval', label: t('domainManagementServices.typeRetrieval') },
    { value: 'inference', label: t('domainManagementServices.typeInference') },
    { value: 'analysis', label: t('domainManagementServices.typeAnalysis') },
    { value: 'general', label: t('domainManagementServices.typeGeneral') },
  ];

  return (
    <Modal
      wrapClassName="yx-domain-space-modal"
      title={
        <span>
          {editing ? (
            <EditOutlined style={{ color: '#3b82f6', marginRight: 8 }} />
          ) : (
            <PlusCircleOutlined style={{ color: '#3b82f6', marginRight: 8 }} />
          )}
          {editing ? t('domainManagement.edit') : t('domainManagementServices.createService')}
        </span>
      }
      open={formOpen}
      onCancel={() => setFormOpen(false)}
      onOk={handleSave}
      confirmLoading={submitting}
      okText={editing ? t('common.save') : t('common.add')}
      cancelText={t('common.cancel')}
      width={600}
      destroyOnHidden
    >
      <div className="yx-form-row">
        <label>
          {t('domainManagement.name')} <span style={{ color: '#ef4444' }}>*</span>
        </label>
        <Input placeholder={t('rules.placeholder')} value={formName} onChange={(e) => setFormName(e.target.value)} />
      </div>
      <div className="yx-form-row">
        <label>{t('domainManagementServices.columnType')}</label>
        <Select
          value={formDomainType || undefined}
          onChange={(v) => setFormDomainType(v || '')}
          style={{ width: '100%' }}
          placeholder={t('domainManagementServices.typePlaceholder')}
          allowClear
          options={typeOptions}
        />
      </div>
      <div className="yx-form-row">
        <label>{t('domainManagement.kb')}</label>
        <div className="yx-kb-check-list">
          {availableKbs.length === 0 ? (
            <span className="yx-kb-tag">{t('domainManagement.noKbAvailable')}</span>
          ) : (
            availableKbs.map((kb) => (
              <label key={kb.id} className="yx-kb-check-item">
                <input type="checkbox" checked={formKbIds.includes(kb.id)} onChange={() => toggleKb(kb.id)} />
                {kb.name}
              </label>
            ))
          )}
        </div>
        <div className="yx-form-hint">{t('domainManagement.kbHint')}</div>
      </div>
      <div className="yx-form-row">
        <label>{t('domainManagement.status')}</label>
        <div className="yx-switch-wrap">
          <label className="yx-switch-label">
            <input type="checkbox" checked={formStatus} onChange={(e) => setFormStatus(e.target.checked)} />
            <span className="yx-switch-slider" />
          </label>
          <span className="yx-switch-text">{formStatus ? t('status.active') : t('status.inactive')}</span>
        </div>
      </div>
    </Modal>
  );
});

export default ServiceFormModal;
