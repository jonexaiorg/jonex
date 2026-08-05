import React, { useEffect } from 'react';
import { Form, Modal, Input } from 'antd';
import { PlusOutlined, EditOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { DomainKnowledgeItem } from '@/types/domainKnowledge';

interface CreateEditModalProps {
  open: boolean;
  editingKb: DomainKnowledgeItem | null;
  submitting: boolean;
  onOk: (data: { name: string; description?: string }) => void;
  onCancel: () => void;
}

export default function CreateEditModal({ open, editingKb, submitting, onOk, onCancel }: CreateEditModalProps) {
  const { t } = useTranslation();
  const [form] = Form.useForm();

  useEffect(() => {
    if (open) {
      form.setFieldsValue({
        name: editingKb?.name ?? '',
        description: editingKb?.description ?? '',
      });
    }
  }, [open, editingKb, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      onOk({ name: values.name, description: values.description });
    } catch {
      /* 校验失败，由 Form 提示 */
    }
  };

  return (
    <Modal
      open={open}
      onCancel={onCancel}
      onOk={handleOk}
      confirmLoading={submitting}
      okText={editingKb ? t('common.save') : t('common.create')}
      cancelText={t('common.cancel')}
      width={520}
      destroyOnClose
      title={
        <span>
          {editingKb ? (
            <EditOutlined style={{ color: '#3b82f6', marginRight: 8 }} />
          ) : (
            <PlusOutlined style={{ color: '#3b82f6', marginRight: 8 }} />
          )}
          {editingKb ? t('domainKnowledge.editKnowledgeBase') : t('domainKnowledge.createKnowledgeBase')}
        </span>
      }
    >
      <Form form={form} layout="vertical" style={{ marginTop: 8 }}>
        <Form.Item
          name="name"
          label={t('domainKnowledge.knowledgeBaseName')}
          rules={[{ required: true, message: t('domainKnowledge.knowledgeBaseNameRequired') }]}
        >
          <Input placeholder={t('domainKnowledge.namePlaceholder')} />
        </Form.Item>
        <Form.Item name="description" label={t('domainKnowledge.description')}>
          <Input.TextArea rows={3} placeholder={t('domainKnowledge.descPlaceholder')} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
