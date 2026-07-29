import React, { useState, useMemo } from 'react';
import { Card, Table, Tag, Input, Select } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { colors, radius } from '@jonex/platform-theme/tokens';
import type { TemplateObject } from '../../data/mock';

const objectDefs = [
  {
    id: 'disease',
    domainId: 'healthcare',
    fields: [
      { id: 'diseaseName', type: 'string', required: true },
      { id: 'icdCode', type: 'string', required: true },
      { id: 'symptomDescription', type: 'text', required: false },
    ],
    status: 'active' as const,
  },
  {
    id: 'drug',
    domainId: 'healthcare',
    fields: [
      { id: 'drugName', type: 'string', required: true },
      { id: 'approvalNumber', type: 'string', required: true },
      { id: 'manufacturer', type: 'string', required: false },
    ],
    status: 'active' as const,
  },
  {
    id: 'company',
    domainId: 'fintech',
    fields: [
      { id: 'companyName', type: 'string', required: true },
      { id: 'creditCode', type: 'string', required: true },
      { id: 'industry', type: 'string', required: false },
    ],
    status: 'active' as const,
  },
];

export default function TemplateObjects() {
  const { t } = useTranslation();
  const [search, setSearch] = useState('');
  const [domainFilter, setDomainFilter] = useState<string>('');
  const objects = useMemo<TemplateObject[]>(
    () =>
      objectDefs.map((object) => ({
        id: `to-${object.id}`,
        name: t(`templateObjects.demo.objects.${object.id}`),
        domainId: object.domainId,
        domainName: t(`templateObjects.demo.domains.${object.domainId}`),
        fields: object.fields.map((field) => ({
          name: t(`templateObjects.demo.fields.${field.id}`),
          type: field.type,
          required: field.required,
        })),
        status: object.status,
      })),
    [t],
  );

  const domains = useMemo(
    () => [...new Map(objects.map((object) => [object.domainId, object.domainName])).entries()],
    [objects],
  );

  const filtered = useMemo(() => {
    return objects.filter((o) => {
      if (search && !o.name.includes(search)) return false;
      if (domainFilter && o.domainId !== domainFilter) return false;
      return true;
    });
  }, [objects, search, domainFilter]);

  const statusLabelMap: Record<string, string> = {
    active: t('status.active'),
    draft: t('status.draft'),
  };
  const statusClsMap: Record<string, string> = {
    active: 'active',
    draft: 'pending',
  };

  const columns = [
    { title: t('templateObjects.columnName'), dataIndex: 'name', key: 'name', width: 140 },
    {
      title: t('templateObjects.columnDomain'),
      dataIndex: 'domainName',
      key: 'domainName',
      width: 120,
      render: (v: string) => <Tag>{v}</Tag>,
    },
    {
      title: t('templateObjects.columnFieldCount'),
      key: 'fieldCount',
      width: 80,
      align: 'center' as const,
      render: (_: unknown, record: TemplateObject) => record.fields.length,
    },
    {
      title: t('templateObjects.columnStatus'),
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (v: string) => (
        <span className={`yx-status-badge ${statusClsMap[v] || v}`}>{statusLabelMap[v] || v}</span>
      ),
    },
  ];

  return (
    <div>
      <div className="yx-page-title">
        <h1 style={{ fontSize: 24, fontWeight: 700, color: colors.brandDark, marginBottom: 4 }}>
          {t('templateObjects.pageTitle')}
        </h1>
        <p style={{ color: colors.textMuted, margin: '4px 0 0', fontSize: 14 }}>{t('templateObjects.pageSubtitle')}</p>
      </div>

      <div
        className="yx-toolbar"
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}
      >
        <div style={{ display: 'flex', gap: 12 }}>
          <Input
            className="yx-search-box"
            placeholder={t('templateObjects.searchPlaceholder')}
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            allowClear
            style={{ width: 260 }}
          />
          <Select
            placeholder={t('templateObjects.domainFilterPlaceholder')}
            value={domainFilter || undefined}
            onChange={(v) => setDomainFilter(v || '')}
            allowClear
            style={{ width: 160 }}
            options={domains.map(([value, label]) => ({ label, value }))}
          />
        </div>
      </div>

      <Card style={{ borderRadius: radius.card }}>
        <Table
          dataSource={filtered}
          columns={columns}
          rowKey="id"
          expandable={{
            expandedRowRender: (record: TemplateObject) => (
              <div style={{ padding: '8px 0' }}>
                <h4 style={{ marginBottom: 8, fontSize: 13, color: colors.brandDark }}>
                  {t('templateObjects.fieldDefSection')}
                </h4>
                <Table
                  dataSource={record.fields.map((f, i) => ({ ...f, key: i }))}
                  columns={[
                    { title: t('templateObjects.fieldName'), dataIndex: 'name', key: 'name' },
                    { title: t('templateObjects.fieldType'), dataIndex: 'type', key: 'type', width: 100 },
                    {
                      title: t('templateObjects.fieldRequired'),
                      dataIndex: 'required',
                      key: 'required',
                      width: 80,
                      render: (v: boolean) => (
                        <Tag color={v ? 'red' : 'default'}>
                          {v ? t('templateObjects.required') : t('templateObjects.optional')}
                        </Tag>
                      ),
                    },
                  ]}
                  rowKey="key"
                  pagination={false}
                  size="small"
                  showHeader={true}
                />
              </div>
            ),
            rowExpandable: () => true,
          }}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
}
