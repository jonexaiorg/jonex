import React from 'react';
import { Modal, Input } from 'antd';

interface FolderNameModalProps {
  title: string;
  placeholder: string;
  open: boolean;
  value: string;
  confirmLoading: boolean;
  onOk: () => void;
  onCancel: () => void;
  onChange: (value: string) => void;
}

export default function FolderNameModal({
  title,
  placeholder,
  open,
  value,
  confirmLoading,
  onOk,
  onCancel,
  onChange,
}: FolderNameModalProps) {
  return (
    <Modal title={title} open={open} onOk={onOk} onCancel={onCancel} confirmLoading={confirmLoading} destroyOnHidden>
      <Input placeholder={placeholder} value={value} onChange={(e) => onChange(e.target.value)} onPressEnter={onOk} />
    </Modal>
  );
}
