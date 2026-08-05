import React, { useState, forwardRef, useImperativeHandle } from 'react';
import { useTranslation } from 'react-i18next';
import { Checkbox, Form, Input, Modal, Select, Switch, message } from 'antd';
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
  const [form] = Form.useForm();

  useImperativeHandle(
    ref,
    () => ({
      openCreate: () => {
        setEditing(null);
        form.setFieldsValue({ name: '', domain_type: undefined, status: true, kb_ids: [] });
        setFormOpen(true);
      },
      openEdit: (item: DomainServiceItem) => {
        setEditing(item);
        form.setFieldsValue({
          name: item.name,
          domain_type: item.domain_type || undefined,
          status: item.status === 'active',
          kb_ids: item.kb_ids || [],
        });
        setFormOpen(true);
      },
    }),
    [form],
  );

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      if (!spaceId) {
        message.warning(t('domainManagement.spaceRequired'));
        return;
      }
      setSubmitting(true);
      const data: DomainServiceFormData = {
        name: values.name.trim(),
        space_id: spaceId!,
        domain_type: values.domain_type || undefined,
        status: values.status ? 'active' : 'inactive',
        kb_ids: values.kb_ids || [],
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
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      message.error(err instanceof Error ? err.message : t('common.saveFailed'));
    } finally {
      setSubmitting(false);
    }
  };

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
      <Form form={form} layout="vertical" style={{ marginTop: 8 }}>
        <Form.Item
          name="name"
          label={t('domainManagement.name')}
          rules={[{ required: true, message: t('domainManagement.nameRequired') }]}
        >
          <Input placeholder={t('rules.placeholder')} />
        </Form.Item>
        <Form.Item name="domain_type" label={t('domainManagementServices.columnType')}>
          <Select
            style={{ width: '100%' }}
            placeholder={t('domainManagementServices.typePlaceholder')}
            allowClear
            options={typeOptions}
          />
        </Form.Item>
        <Form.Item name="kb_ids" label={t('domainManagement.kb')}>
          <Checkbox.Group>
            <div className="yx-kb-check-list">
              {availableKbs.length === 0 ? (
                <span className="yx-kb-tag">{t('domainManagement.noKbAvailable')}</span>
              ) : (
                availableKbs.map((kb) => (
                  <Checkbox key={kb.id} value={kb.id}>
                    {kb.name}
                  </Checkbox>
                ))
              )}
            </div>
          </Checkbox.Group>
        </Form.Item>
        <Form.Item name="status" label={t('domainManagement.status')} valuePropName="checked">
          <Switch checkedChildren={t('status.active')} unCheckedChildren={t('status.inactive')} />
        </Form.Item>
      </Form>
    </Modal>
  );
});

export default ServiceFormModal;
