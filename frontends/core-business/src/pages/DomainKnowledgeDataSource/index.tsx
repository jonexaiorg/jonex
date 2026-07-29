import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button, Card, Table, Tag, Input, Space } from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';

const sourceDefs = [
  { nameKey: 'dataSource.demo.financeDatabase', type: 'database', status: 'connected', lastSync: '2026-05-21 14:30' },
  { nameKey: 'dataSource.demo.marketApi', type: 'api', status: 'connected', lastSync: '2026-05-21 14:25' },
  { nameKey: 'dataSource.demo.medicalPdf', type: 'file', status: 'connected', lastSync: '2026-05-20 18:00' },
  { nameKey: 'dataSource.demo.sensorData', type: 'api', status: 'connecting', lastSync: '2026-05-21 12:00' },
  { nameKey: 'dataSource.demo.legalStorage', type: 'file', status: 'failed', lastSync: '2026-05-19 09:15' },
];

const connStatusColor: Record<string, string> = { connected: 'success', connecting: 'processing', failed: 'error' };
const typeColor: Record<string, string> = { database: 'blue', api: 'green', file: 'orange' };

const typeLabelKeys: Record<string, string> = {
  database: 'dataSource.typeDatabase',
  api: 'dataSource.typeApi',
  file: 'dataSource.typeFile',
};
const statusLabelKeys: Record<string, string> = {
  connected: 'dataSource.statusConnected',
  connecting: 'dataSource.statusConnecting',
  failed: 'dataSource.statusFailed',
};

export default function DomainKnowledgeDataSource() {
  const { t } = useTranslation();
  const [search, setSearch] = useState('');
  const sources = sourceDefs.map((source) => ({ ...source, name: t(source.nameKey) }));

  const columns = [
    {
      title: t('dataSource.columnName'),
      dataIndex: 'name',
      key: 'name',
      width: 180,
      render: (v: string) => <a className="yx-table-action">{v}</a>,
    },
    {
      title: t('common.type'),
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (v: string) => <Tag color={typeColor[v]}>{t(typeLabelKeys[v] || 'common.unknown')}</Tag>,
    },
    {
      title: t('dataSource.columnStatus'),
      dataIndex: 'status',
      key: 'status',
      width: 110,
      render: (v: string) => <Tag color={connStatusColor[v]}>{t(statusLabelKeys[v] || 'common.unknown')}</Tag>,
    },
    { title: t('dataSource.columnLastSync'), dataIndex: 'lastSync', key: 'lastSync', width: 160 },
    {
      title: t('common.actions'),
      key: 'actions',
      width: 160,
      render: () => (
        <Space>
          <a className="yx-table-action">{t('common.edit')}</a>
          <a className="yx-table-action">{t('dataSource.test')}</a>
          <a className="yx-table-action">{t('common.delete')}</a>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('dataSource.pageTitle')}</h1>
      </div>

      <Card className="yx-card">
        <div className="yx-toolbar">
          <Input
            prefix={<SearchOutlined />}
            placeholder={t('dataSource.searchPlaceholder')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 240 }}
          />
          <Button type="primary" icon={<PlusOutlined />}>
            {t('dataSource.addDataSource')}
          </Button>
        </div>
        <Table
          columns={columns}
          dataSource={sources.filter((s) => s.name.includes(search))}
          rowKey="name"
          pagination={{ total: 12, pageSize: 5 }}
          size="middle"
        />
      </Card>
    </div>
  );
}
