import React, { useState, useMemo } from 'react';
import { Card, Table, Tag, Input, Select } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { colors, radius } from '@jonex/platform-theme/tokens';
import type { TemplateRelation } from '../../data/mock';

const relationDefs = [
  { id: 'treats', source: 'drug', target: 'disease', relationType: '1:N' },
  { id: 'contains', source: 'drug', target: 'compound', relationType: 'N:M' },
  { id: 'controls', source: 'company', target: 'company', relationType: '1:N' },
];

export default function TemplateRelations() {
  const { t } = useTranslation();
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const relations = useMemo<TemplateRelation[]>(
    () =>
      relationDefs.map((relation) => ({
        id: `tr-${relation.id}`,
        name: t(`templateRelations.demo.relations.${relation.id}.name`),
        sourceObject: t(`templateRelations.demo.objects.${relation.source}`),
        targetObject: t(`templateRelations.demo.objects.${relation.target}`),
        relationType: relation.relationType,
        constraints: t(`templateRelations.demo.relations.${relation.id}.constraints`),
      })),
    [t],
  );

  const relationTypes = useMemo(() => [...new Set(relations.map((r) => r.relationType))], [relations]);

  const filtered = useMemo(() => {
    return relations.filter((r) => {
      if (search && !r.name.includes(search) && !r.sourceObject.includes(search) && !r.targetObject.includes(search))
        return false;
      if (typeFilter && r.relationType !== typeFilter) return false;
      return true;
    });
  }, [relations, search, typeFilter]);

  const columns = [
    { title: t('templateRelations.columnName'), dataIndex: 'name', key: 'name', width: 140 },
    {
      title: t('templateRelations.columnSource'),
      dataIndex: 'sourceObject',
      key: 'sourceObject',
      width: 120,
      render: (v: string) => <Tag color="blue">{v}</Tag>,
    },
    {
      title: t('templateRelations.columnTarget'),
      dataIndex: 'targetObject',
      key: 'targetObject',
      width: 120,
      render: (v: string) => <Tag color="green">{v}</Tag>,
    },
    {
      title: t('templateRelations.columnType'),
      dataIndex: 'relationType',
      key: 'relationType',
      width: 90,
      align: 'center' as const,
    },
    { title: t('templateRelations.columnConstraints'), dataIndex: 'constraints', key: 'constraints', ellipsis: true },
  ];

  return (
    <div>
      <div className="yx-page-title">
        <h1 style={{ fontSize: 24, fontWeight: 700, color: colors.brandDark, marginBottom: 4 }}>
          {t('templateRelations.pageTitle')}
        </h1>
        <p style={{ color: colors.textMuted, margin: '4px 0 0', fontSize: 14 }}>
          {t('templateRelations.pageSubtitle')}
        </p>
      </div>

      <div
        className="yx-toolbar"
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}
      >
        <div style={{ display: 'flex', gap: 12 }}>
          <Input
            className="yx-search-box"
            placeholder={t('templateRelations.searchPlaceholder')}
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            allowClear
            style={{ width: 320 }}
          />
          <Select
            placeholder={t('templateRelations.typeFilterPlaceholder')}
            value={typeFilter || undefined}
            onChange={(v) => setTypeFilter(v || '')}
            allowClear
            style={{ width: 160 }}
            options={relationTypes.map((t) => ({ label: t, value: t }))}
          />
        </div>
      </div>

      <Card style={{ borderRadius: radius.card }}>
        <Table dataSource={filtered} columns={columns} rowKey="id" pagination={{ pageSize: 10 }} />
      </Card>
    </div>
  );
}
