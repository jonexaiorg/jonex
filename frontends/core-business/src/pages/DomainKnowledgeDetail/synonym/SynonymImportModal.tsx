import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal, Input, Alert, Typography } from 'antd';
import type { SynonymImportResult } from '@/types/domainKnowledge';

const { Paragraph, Text } = Typography;

/**
 * 解析单行 CSV：支持双引号包裹与引号内逗号/转义双引号（""）。
 * 分隔符支持英文逗号与中文逗号（引号外）。
 */
export function parseCsvLine(line: string): string[] {
  const fields: string[] = [];
  let cur = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (inQuotes) {
      if (ch === '"') {
        if (line[i + 1] === '"') {
          cur += '"';
          i += 1;
        } else {
          inQuotes = false;
        }
      } else {
        cur += ch;
      }
    } else if (ch === '"') {
      inQuotes = true;
    } else if (ch === ',' || ch === '，') {
      fields.push(cur.trim());
      cur = '';
    } else {
      cur += ch;
    }
  }
  fields.push(cur.trim());
  return fields.filter((f) => f.length > 0);
}

/** 多行文本 → groups：每行一组，行内 CSV 解析；跳过空行。 */
export function parseGroups(text: string): string[][] {
  return (text || '')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map(parseCsvLine)
    .filter((group) => group.length > 0);
}

interface Props {
  open: boolean;
  submitting: boolean;
  onCancel: () => void;
  onImport: (groups: string[][]) => Promise<SynonymImportResult | null>;
}

export default function SynonymImportModal({ open, submitting, onCancel, onImport }: Props) {
  const { t } = useTranslation();
  const [text, setText] = useState('');
  const [result, setResult] = useState<SynonymImportResult | null>(null);

  const groups = parseGroups(text);

  async function handleOk() {
    setResult(null);
    const res = await onImport(groups);
    if (res) setResult(res);
  }

  function handleCancel() {
    setText('');
    setResult(null);
    onCancel();
  }

  return (
    <Modal
      title={t('synonym.importTitle')}
      open={open}
      onCancel={handleCancel}
      onOk={handleOk}
      okText={t('synonym.importOk', { count: groups.length })}
      cancelText={t('common.close')}
      confirmLoading={submitting}
      okButtonProps={{ disabled: groups.length === 0 }}
      width={640}
      destroyOnHidden
    >
      <Paragraph type="secondary" style={{ fontSize: 13 }}>
        {t('synonym.importHint')}
      </Paragraph>
      <Input.TextArea
        rows={8}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={t('synonym.importPlaceholder')}
      />
      {result && (
        <Alert
          style={{ marginTop: 12 }}
          type={result.failed.length > 0 ? 'warning' : 'success'}
          message={t('synonym.importResult', {
            created: result.created,
            skipped: result.skipped,
            failed: result.failed.length,
          })}
          description={
            result.failed.length > 0 ? (
              <div style={{ maxHeight: 160, overflow: 'auto' }}>
                {result.failed.map((f) => (
                  <div key={f.index} style={{ fontSize: 12 }}>
                    <Text type="danger">{t('synonym.importRowError', { index: f.index + 1, reason: f.reason })}</Text>
                  </div>
                ))}
              </div>
            ) : undefined
          }
          showIcon
        />
      )}
    </Modal>
  );
}
