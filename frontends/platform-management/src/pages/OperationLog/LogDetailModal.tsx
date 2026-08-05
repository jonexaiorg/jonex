import React from 'react';
import { Modal, Tag } from 'antd';
import { useTranslation } from 'react-i18next';
import dayjs from 'dayjs';
import type { AuditLogItem, AuditActionOption, AuditResourceType } from '../../api/auditLogs';
import { getActionLabel, actionTagColor, getResourceLabel, formatDuration } from './index';

interface LogDetailModalProps {
  open: boolean;
  detailItem: AuditLogItem | null;
  onClose: () => void;
  actionOptions: AuditActionOption[];
  resourceOptions: AuditResourceType[];
  locale: string;
}

export default function LogDetailModal({
  open,
  detailItem,
  onClose,
  actionOptions,
  resourceOptions,
  locale,
}: LogDetailModalProps) {
  const { t } = useTranslation();

  return (
    <Modal title={t('operationLog.logDetail')} open={open} onCancel={onClose} footer={null} width={600}>
      {detailItem && (
        <div>
          <p>
            <strong>{t('operationLog.actionLabel')}</strong>
            <Tag color={actionTagColor(detailItem.action)}>
              {getActionLabel(locale, actionOptions, detailItem.action)}
            </Tag>
            · <strong>{t('operationLog.resourceLabel')}</strong>
            <span>
              {getResourceLabel(
                detailItem.resource,
                detailItem.resource_name,
                detailItem.resource_id,
                resourceOptions,
                locale,
              )}
              {detailItem.resource_name && (
                <span style={{ fontSize: 12, color: '#94a3b8' }}> · {detailItem.resource_name}</span>
              )}
              {detailItem.resource_id && (
                <span style={{ fontSize: 11, color: '#94a3b8', marginLeft: 8 }}>{detailItem.resource_id}</span>
              )}
            </span>
          </p>
          <p>
            <strong>{t('operationLog.userLabel')}</strong>
            {detailItem.username || '--'} · <strong>{t('operationLog.ipLabel')}</strong>
            {detailItem.ip || '--'} · <strong>{t('operationLog.durationLabel')}</strong>
            {formatDuration(detailItem.duration_ms)}
          </p>
          <p>
            <strong>{t('operationLog.traceIdLabel')}</strong>
            {detailItem.trace_id || '--'}
          </p>
          <p>
            <strong>{t('operationLog.timeLabel')}</strong>
            {detailItem.created_at ? dayjs(detailItem.created_at).format('YYYY-MM-DD HH:mm:ss') : '--'}
          </p>
          {detailItem.detail && (
            <pre
              style={{
                background: '#f8fafc',
                padding: 12,
                borderRadius: 8,
                fontSize: 12,
                maxHeight: 300,
                overflow: 'auto',
              }}
            >
              {typeof detailItem.detail === 'string' ? detailItem.detail : JSON.stringify(detailItem.detail, null, 2)}
            </pre>
          )}
        </div>
      )}
    </Modal>
  );
}
