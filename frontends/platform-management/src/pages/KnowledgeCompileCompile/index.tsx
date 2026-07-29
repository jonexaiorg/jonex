import React from 'react';
import { Input, Button, Table, Tag, message, Card } from 'antd';
import { SearchOutlined, ThunderboltOutlined, ReloadOutlined } from '@ant-design/icons';
import { colors, radius } from '@jonex/platform-theme/tokens';
import { MOCK_COMPILE_TASKS, type CompileTask } from '../../data/mock';
import { useTranslation } from 'react-i18next';

export default function KnowledgeCompileCompile() {
  const { t } = useTranslation();
  const [tasks, setTasks] = React.useState<CompileTask[]>(MOCK_COMPILE_TASKS);
  const [search, setSearch] = React.useState('');

  const statusConfig: Record<string, { color: string; label: string }> = {
    running: { color: 'processing', label: t('status.running') },
    completed: { color: 'success', label: t('status.completed') },
    failed: { color: 'error', label: t('status.failed') },
    pending: { color: 'default', label: t('status.pending') },
  };

  const filtered = tasks.filter((t) => t.name.includes(search) || t.type.includes(search));

  const handleTrigger = (id: string) => {
    setTasks((prev) =>
      prev.map((t) =>
        t.id === id
          ? { ...t, status: 'running' as const, updatedAt: new Date().toISOString().slice(0, 16).replace('T', ' ') }
          : t,
      ),
    );
    message.success(t('knowledgeCompile.compileTriggered'));
  };

  const columns = [
    {
      title: t('knowledgeCompile.taskName'),
      dataIndex: 'name',
      key: 'name',
      render: (v: string, record: CompileTask) => (
        <div>
          <div style={{ fontWeight: 500, color: colors.textPrimary }}>{v}</div>
          <div style={{ fontSize: 12, color: colors.textMuted }}>{record.type}</div>
        </div>
      ),
    },
    {
      title: t('common.status'),
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (v: string) => {
        const cfg = statusConfig[v] || { color: 'default', label: v };
        return (
          <span className="yx-status-badge">
            <Tag color={cfg.color}>{cfg.label}</Tag>
          </span>
        );
      },
    },
    {
      title: t('knowledgeCompile.entityCount'),
      dataIndex: 'entityCount',
      key: 'entityCount',
      render: (v: number) => v.toLocaleString(),
    },
    {
      title: t('knowledgeCompile.relationCount'),
      dataIndex: 'relationCount',
      key: 'relationCount',
      render: (v: number) => v.toLocaleString(),
    },
    {
      title: t('knowledgeCompile.chunkCount'),
      dataIndex: 'chunkCount',
      key: 'chunkCount',
      render: (v: number) => v.toLocaleString(),
    },
    {
      title: t('knowledgeCompile.updatedAt'),
      dataIndex: 'updatedAt',
      key: 'updatedAt',
    },
    {
      title: t('common.actions'),
      key: 'actions',
      width: 180,
      render: (_: unknown, record: CompileTask) => (
        <div style={{ display: 'flex', gap: 8 }}>
          <Button
            type="primary"
            size="small"
            icon={<ThunderboltOutlined />}
            onClick={() => handleTrigger(record.id)}
            disabled={record.status === 'running'}
          >
            {t('knowledgeCompile.triggerCompile')}
          </Button>
          <Button
            size="small"
            icon={<ReloadOutlined />}
            onClick={() => message.info(t('knowledgeCompile.compileRetry', { name: record.name }))}
            disabled={record.status !== 'failed'}
          >
            {t('common.retry')}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('knowledgeCompile.compileTitle')}</h1>
        <p style={{ color: colors.textSecondary, margin: '4px 0 0', fontSize: 14 }}>
          {t('knowledgeCompile.compileDesc')}
        </p>
      </div>

      <div className="yx-card">
        <div className="yx-toolbar" style={{ flexWrap: 'wrap' }}>
          <Input
            prefix={<SearchOutlined />}
            placeholder={t('knowledgeCompile.searchTasks')}
            style={{ width: 240 }}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Button type="primary" icon={<ThunderboltOutlined />}>
            {t('knowledgeCompile.newCompileTask')}
          </Button>
        </div>
        <Table
          columns={columns}
          dataSource={filtered}
          rowKey="id"
          pagination={{ total: filtered.length, pageSize: 10 }}
          size="middle"
        />
      </div>
    </div>
  );
}
