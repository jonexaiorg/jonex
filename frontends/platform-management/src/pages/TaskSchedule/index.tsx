import React from 'react';
import { Input, Button, Table, Tag, Select } from 'antd';
import { SearchOutlined, PlusOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const taskDefs = [
  { id: 'financialRisk', status: 'running', lastRun: '2026-05-22 02:00', nextRun: '2026-05-23 02:00' },
  { id: 'medicalVector', status: 'running', lastRun: '2026-05-22 15:00', nextRun: '2026-05-22 16:00' },
  { id: 'equipmentSync', status: 'running', lastRun: '2026-05-22 15:30', nextRun: '2026-05-22 16:00' },
  { id: 'courseCompile', status: 'paused', lastRun: '2026-05-17 03:00', nextRun: '--' },
  { id: 'legalGraph', status: 'failed', lastRun: '2026-05-21 10:00', nextRun: '--' },
];

const statusColor: Record<string, string> = { running: 'success', paused: 'warning', failed: 'error' };

export default function TaskSchedule() {
  const { t } = useTranslation();
  const tasks = taskDefs.map((task) => ({
    ...task,
    name: t(`taskSchedule.demo.${task.id}.name`),
    type: t(`taskSchedule.demo.${task.id}.type`),
    strategy: t(`taskSchedule.demo.${task.id}.strategy`),
  }));

  const columns = [
    {
      title: t('knowledgeCompile.taskName'),
      dataIndex: 'name',
      key: 'name',
      render: (v: string) => <a className="yx-table-action">{v}</a>,
    },
    { title: t('common.type'), dataIndex: 'type', key: 'type' },
    { title: t('taskSchedule.strategy'), dataIndex: 'strategy', key: 'strategy' },
    {
      title: t('common.status'),
      dataIndex: 'status',
      key: 'status',
      render: (v: string) => <Tag color={statusColor[v] || 'default'}>{t(`status.${v}`)}</Tag>,
    },
    { title: t('taskSchedule.lastRun'), dataIndex: 'lastRun', key: 'lastRun' },
    { title: t('taskSchedule.nextRun'), dataIndex: 'nextRun', key: 'nextRun' },
    {
      title: t('common.actions'),
      key: 'actions',
      render: () => (
        <span>
          <a className="yx-table-action">{t('status.paused')}</a>
          <a className="yx-table-action" style={{ marginLeft: 8 }}>
            {t('common.edit')}
          </a>
        </span>
      ),
    },
  ];

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('taskSchedule.title')}</h1>
      </div>
      <div className="yx-card">
        <div className="yx-toolbar">
          <Input prefix={<SearchOutlined />} placeholder={t('common.search')} style={{ width: 240 }} />
          <Select
            defaultValue={t('status.allStatus')}
            style={{ width: 120 }}
            options={[
              { value: 'all', label: t('status.allStatus') },
              { value: 'running', label: t('status.running') },
              { value: 'paused', label: t('status.paused') },
              { value: 'completed', label: t('status.completed') },
            ]}
          />
          <Button type="primary" icon={<PlusOutlined />}>
            {t('taskSchedule.newTask')}
          </Button>
        </div>
        <Table columns={columns} dataSource={tasks} rowKey="id" pagination={{ total: 9, pageSize: 10 }} size="middle" />
      </div>
    </div>
  );
}
