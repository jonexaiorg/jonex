import React from 'react';
import { Modal } from 'antd';
import { useTranslation } from 'react-i18next';
import dayjs from 'dayjs';
import type { AuditLogItem } from '../../api/auditLogs';

interface LogDetailModalProps {
  open: boolean;
  detailItem: AuditLogItem | null;
  onClose: () => void;
}

export default function LogDetailModal({ open, detailItem, onClose }: LogDetailModalProps) {
  const { t } = useTranslation();

  return (
    <Modal title={t('operationLog.logDetail')} open={open} onCancel={onClose} footer={null} width={600}>
      {detailItem && (
        <div>
          <p>
            <strong>{t('operationLog.actionLabel')}</strong>
            {detailItem.action} · <strong>{t('operationLog.resourceLabel')}</strong>
            {detailItem.resource}/{detailItem.resource_id}
          </p>
          <p>
            <strong>{t('operationLog.userLabel')}</strong>
            {detailItem.username || '--'} · <strong>{t('operationLog.ipLabel')}</strong>
            {detailItem.ip || '--'} · <strong>{t('operationLog.durationLabel')}</strong>
            {detailItem.duration_ms ? `${detailItem.duration_ms}ms` : '--'}
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
