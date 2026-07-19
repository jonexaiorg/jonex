import React from 'react'
import { Input, Button, Table, Tag, message, Card } from 'antd'
import { useTranslation } from 'react-i18next'
import { SearchOutlined, ThunderboltOutlined, ReloadOutlined } from '@ant-design/icons'
import { colors, radius } from '@jonex/platform-theme/tokens'
import { MOCK_COMPILE_TASKS, type CompileTask } from '../../data/mock'

const statusConfig: Record<string, { color: string; label: string }> = {
  running: { color: 'processing', label: 'status.running' },
  completed: { color: 'success', label: 'status.completed' },
  failed: { color: 'error', label: 'status.failed' },
  pending: { color: 'default', label: 'status.waiting' },
}

export default function KnowledgeCompileCompile() {
  const { t } = useTranslation()
  const [tasks, setTasks] = React.useState<CompileTask[]>(MOCK_COMPILE_TASKS)
  const [search, setSearch] = React.useState('')

  const filtered = tasks.filter(
    (t) => t.name.includes(search) || t.type.includes(search),
  )

  const handleTrigger = (id: string) => {
    setTasks((prev) =>
      prev.map((t) =>
        t.id === id ? { ...t, status: 'running' as const, updatedAt: new Date().toISOString().slice(0, 16).replace('T', ' ') } : t,
      ),
    )
    message.success(t('knowledgeCompile.compileSuccess'))
  }

  const columns = [
    {
      title: t('taskSchedule.taskName'),
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
      title: t('knowledgeCompile.compileStatus'),
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (v: string) => {
        const cfg = statusConfig[v] || { color: 'default', label: v }
        return <span className="yx-status-badge"><Tag color={cfg.color}>{t(cfg.label)}</Tag></span>
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
      title: t('knowledgeCompile.chunkCount', 'Chunk 数'),
      dataIndex: 'chunkCount',
      key: 'chunkCount',
      render: (v: number) => v.toLocaleString(),
    },
    {
      title: t('operationLog.createdAt'),
      dataIndex: 'updatedAt',
      key: 'updatedAt',
    },
    {
      title: t('taskSchedule.actions', '操作'),
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
            {t('knowledgeCompile.startCompile')}
          </Button>
          <Button
            size="small"
            icon={<ReloadOutlined />}
            onClick={() => message.info(t('knowledgeCompile.retry', { name: record.name }))}
            disabled={record.status !== 'failed'}
          >
            {t('common.retry', '重试')}
          </Button>
        </div>
      ),
    },
  ]

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('knowledgeCompile.compile')}</h1>
        <p style={{ color: colors.textSecondary, margin: '4px 0 0', fontSize: 14 }}>
          {t('knowledgeCompile.compileDesc', '管理知识库编译任务，触发全量或增量编译')}
        </p>
      </div>

      <div className="yx-card">
        <div className="yx-toolbar" style={{ flexWrap: 'wrap' }}>
          <Input
            prefix={<SearchOutlined />}
            placeholder={t('knowledgeCompile.searchPlaceholder2', '搜索编译任务...')}
            style={{ width: 240 }}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Button type="primary" icon={<ThunderboltOutlined />}>
            {t('knowledgeCompile.newTask', '新建编译任务')}
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
  )
}
