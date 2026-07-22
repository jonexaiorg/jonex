import React from 'react'
import { Input, Button, Table, Tag, message, Card } from 'antd'
import { SearchOutlined, ThunderboltOutlined, ReloadOutlined } from '@ant-design/icons'
import { colors, radius } from '@jonex/platform-theme/tokens'
import type { CompileTask } from '../../types/management'

const initialTasks: CompileTask[] = []

const statusConfig: Record<string, { color: string; label: string }> = {
  running: { color: 'processing', label: '运行中' },
  completed: { color: 'success', label: '已完成' },
  failed: { color: 'error', label: '失败' },
  pending: { color: 'default', label: '等待中' },
}

export default function KnowledgeCompileCompile() {
  const [tasks, setTasks] = React.useState<CompileTask[]>(initialTasks)
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
    message.success('编译任务已触发')
  }

  const columns = [
    {
      title: '任务名称',
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
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (v: string) => {
        const cfg = statusConfig[v] || { color: 'default', label: v }
        return <span className="yx-status-badge"><Tag color={cfg.color}>{cfg.label}</Tag></span>
      },
    },
    {
      title: '实体数',
      dataIndex: 'entityCount',
      key: 'entityCount',
      render: (v: number) => v.toLocaleString(),
    },
    {
      title: '关系数',
      dataIndex: 'relationCount',
      key: 'relationCount',
      render: (v: number) => v.toLocaleString(),
    },
    {
      title: 'Chunk 数',
      dataIndex: 'chunkCount',
      key: 'chunkCount',
      render: (v: number) => v.toLocaleString(),
    },
    {
      title: '更新时间',
      dataIndex: 'updatedAt',
      key: 'updatedAt',
    },
    {
      title: '操作',
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
            触发编译
          </Button>
          <Button
            size="small"
            icon={<ReloadOutlined />}
            onClick={() => message.info(`重试「${record.name}」`)}
            disabled={record.status !== 'failed'}
          >
            重试
          </Button>
        </div>
      ),
    },
  ]

  return (
    <div>
      <div className="yx-page-title">
        <h1>编译管理</h1>
        <p style={{ color: colors.textSecondary, margin: '4px 0 0', fontSize: 14 }}>
          管理知识库编译任务，触发全量或增量编译
        </p>
      </div>

      <div className="yx-card">
        <div className="yx-toolbar" style={{ flexWrap: 'wrap' }}>
          <Input
            prefix={<SearchOutlined />}
            placeholder="搜索编译任务..."
            style={{ width: 240 }}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Button type="primary" icon={<ThunderboltOutlined />}>
            新建编译任务
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
