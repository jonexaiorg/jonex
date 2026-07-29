import React, { useState } from 'react';
import { Modal, Button, Table } from 'antd';
import { KeyOutlined, PlusOutlined, CopyOutlined, CheckOutlined, DeleteOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { ColumnsType } from 'antd/es/table';
import type { DomainServiceItem, ServiceApiKeyItem } from '../../types/domainService';

interface SrvConfigModalProps {
  open: boolean;
  srvConfigTarget: DomainServiceItem | null;
  apiKeys: ServiceApiKeyItem[];
  apiKeysLoading: boolean;
  creatingKey: boolean;
  onCreateKey: () => void;
  onDeleteKey: (keyId: string) => void;
  onCancel: () => void;
}

export default function SrvConfigModal({
  open,
  srvConfigTarget,
  apiKeys,
  apiKeysLoading,
  creatingKey,
  onCreateKey,
  onDeleteKey,
  onCancel,
}: SrvConfigModalProps) {
  const { t } = useTranslation();
  const [copiedKeyId, setCopiedKeyId] = useState<string | null>(null);

  const handleCopyKey = async (keyId: string, key: string) => {
    try {
      await navigator.clipboard.writeText(key);
      setCopiedKeyId(keyId);
      setTimeout(() => setCopiedKeyId(null), 2000);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = key;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopiedKeyId(keyId);
      setTimeout(() => setCopiedKeyId(null), 2000);
    }
  };

  const formatDate = (dateStr: string | null): string => {
    if (!dateStr) return '—';
    try {
      return new Date(dateStr).toISOString().slice(0, 10);
    } catch {
      return dateStr;
    }
  };

  return (
    <Modal
      wrapClassName="yx-domain-space-modal"
      title={
        <span>
          <KeyOutlined style={{ color: '#f97316', marginRight: 8 }} />
          {t('domainManagement.srvConfigTitle')}
        </span>
      }
      open={open}
      onCancel={onCancel}
      footer={<Button onClick={onCancel}>{t('common.cancel')}</Button>}
      width={760}
    >
      <p style={{ fontSize: 14, color: '#475569', marginBottom: 16 }}>
        {t('domainManagement.srvConfigDesc', {
          name: srvConfigTarget?.name || '',
        })}
      </p>
      <div style={{ textAlign: 'right', marginBottom: 12 }}>
        <Button type="primary" size="small" icon={<PlusOutlined />} loading={creatingKey} onClick={onCreateKey}>
          {t('domainManagement.addApiKey')}
        </Button>
      </div>
      <Table<ServiceApiKeyItem>
        columns={[
          {
            title: t('domainManagement.apiKey'),
            dataIndex: 'key_encrypted',
            key: 'key_encrypted',
            width: 360,
            render: (val: string, record: ServiceApiKeyItem) => (
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span className="yx-key-text">{val || '—'}</span>
                {val && (
                  <Button
                    type="text"
                    className={`yx-copy-btn${copiedKeyId === record.id ? ' copied' : ''}`}
                    title={copiedKeyId === record.id ? t('common.copySuccess') : t('domainManagement.copyApiKey')}
                    onClick={() => handleCopyKey(record.id, val)}
                  >
                    {copiedKeyId === record.id ? <CheckOutlined /> : <CopyOutlined />}
                  </Button>
                )}
              </span>
            ),
          },
          {
            title: t('domainManagement.expiresAt'),
            dataIndex: 'expires_at',
            key: 'expires_at',
            width: 120,
            render: (val: string | null) => formatDate(val),
          },
          {
            title: t('domainManagement.srvConfigActions'),
            key: 'actions',
            width: 100,
            render: (_: unknown, record: ServiceApiKeyItem) => (
              <Button type="text" danger onClick={() => onDeleteKey(record.id)}>
                <DeleteOutlined /> {t('common.delete')}
              </Button>
            ),
          },
        ]}
        dataSource={apiKeys}
        rowKey="id"
        pagination={false}
        size="small"
        loading={apiKeysLoading}
        locale={{ emptyText: t('common.noApiKey') }}
      />
    </Modal>
  );
}
