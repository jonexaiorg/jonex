import React, { useEffect } from 'react';
import { Form, Input, Modal } from 'antd';

interface FolderNameModalProps {
  title: string;
  placeholder: string;
  open: boolean;
  initialValue?: string;
  confirmLoading: boolean;
  onOk: (value: string) => void;
  onCancel: () => void;
}

export default function FolderNameModal({
  title,
  placeholder,
  open,
  initialValue,
  confirmLoading,
  onOk,
  onCancel,
}: FolderNameModalProps) {
  const [form] = Form.useForm();

  useEffect(() => {
    if (open) {
      form.setFieldsValue({ name: initialValue ?? '' });
    }
  }, [open, initialValue, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      onOk(values.name);
    } catch {
      /* 校验失败，由 Form 提示 */
    }
  };

  return (
    <Modal
      title={title}
      open={open}
      onOk={handleOk}
      onCancel={onCancel}
      confirmLoading={confirmLoading}
      destroyOnHidden
    >
      <Form form={form} layout="vertical" style={{ marginTop: 8 }}>
        <Form.Item name="name" rules={[{ required: true, message: placeholder || 'Required' }]}>
          <Input placeholder={placeholder} onPressEnter={handleOk} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
