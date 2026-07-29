import React, { useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal, Form, Input, Select } from 'antd';
import type { SynonymGroup } from '@/types/domainKnowledge';

/** 逗号（中英文）分隔 → 去空去重（保序）。 */
export function splitTerms(raw: string): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const part of (raw || '').split(/[,，]/)) {
    const t = part.trim();
    if (!t) continue;
    const key = t.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(t);
  }
  return out;
}

interface FormValues {
  termsText: string;
  canonical?: string;
}

interface Props {
  open: boolean;
  editing: SynonymGroup | null;
  submitting: boolean;
  onCancel: () => void;
  onSubmit: (terms: string[], canonical?: string) => void;
}

export default function SynonymFormModal({ open, editing, submitting, onCancel, onSubmit }: Props) {
  const { t } = useTranslation();
  const [form] = Form.useForm<FormValues>();
  const termsText = Form.useWatch('termsText', form);

  useEffect(() => {
    if (!open) return;
    if (editing) {
      form.setFieldsValue({ termsText: (editing.terms || []).join(', '), canonical: editing.canonical || undefined });
    } else {
      form.setFieldsValue({ termsText: '', canonical: undefined });
    }
  }, [editing, form, open]);

  const parsedTerms = useMemo(() => splitTerms(termsText || ''), [termsText]);

  async function handleOk() {
    const values = await form.validateFields();
    const terms = splitTerms(values.termsText);
    onSubmit(terms, values.canonical);
  }

  return (
    <Modal
      title={editing ? t('synonym.editGroup') : t('synonym.newGroup')}
      open={open}
      onCancel={onCancel}
      onOk={handleOk}
      okText={t('common.confirm')}
      cancelText={t('common.cancel')}
      confirmLoading={submitting}
      width={560}
      destroyOnHidden
    >
      <Form form={form} layout="vertical" preserve={false}>
        <Form.Item
          label={t('synonym.formLabel')}
          name="termsText"
          extra={t('synonym.formExtra')}
          rules={[
            {
              validator: () => {
                const terms = splitTerms(form.getFieldValue('termsText') || '');
                return terms.length >= 2 ? Promise.resolve() : Promise.reject(new Error(t('synonym.minTermsError')));
              },
            },
          ]}
        >
          <Input.TextArea rows={3} placeholder={t('synonym.termsPlaceholder')} />
        </Form.Item>
        <Form.Item label={t('synonym.canonicalLabel')} name="canonical">
          <Select
            allowClear
            placeholder={t('synonym.canonicalPlaceholder')}
            options={parsedTerms.map((t) => ({ label: t, value: t }))}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}
