import React from 'react'
import { Input, Button, Table, Tag, message } from 'antd'
import { SearchOutlined, EditOutlined, ExperimentOutlined } from '@ant-design/icons'
import { colors, radius } from '@jonex/platform-theme/tokens'
import type { ParserInfo } from '../../types/management'

const parsers: ParserInfo[] = []

const statusConfig: Record<string, { color: string; label: string }> = {
  active: { color: 'success', label: '运行中' },
  inactive: { color: 'default', label: '未激活' },
  error: { color: 'error', label: '异常' },
}

export default function ParserManagement() {
  const [search, setSearch] = React.useState('')

  const filtered = parsers.filter(
    (p) =>
      p.name.includes(search) ||
      p.description.includes(search) ||
      p.version.includes(search),
  )

  const columns = [
    {
      title: '解析器名称',
      dataIndex: 'name',
      key: 'name',
      render: (v: string, record: ParserInfo) => (
        <div>
          <div style={{ fontWeight: 500, color: colors.textPrimary }}>{v}</div>
          <div style={{ fontSize: 12, color: colors.textMuted }}>{record.version}</div>
        </div>
      ),
    },
    {
      title: '支持格式',
      dataIndex: 'fileTypes',
      key: 'fileTypes',
      render: (types: string[]) => (
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {types.map((t) => (
            <Tag key={t} style={{ borderRadius: radius.tag, fontSize: 12 }}>{t}</Tag>
          ))}
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
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      render: (v: string) => (
        <span style={{ color: colors.textSecondary, fontSize: 13 }}>{v}</span>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 160,
      render: (_: unknown, record: ParserInfo) => (
        <div style={{ display: 'flex', gap: 8 }}>
          <Button
            type="primary"
            size="small"
            icon={<ExperimentOutlined />}
            onClick={() => message.success(`「${record.name}」测试解析已提交`)}
          >
            测试解析
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => message.info(`编辑「${record.name}」`)}
          >
            编辑
          </Button>
        </div>
      ),
    },
  ]

  return (
    <div>
      <div className="yx-page-title">
        <h1>解析器管理</h1>
        <p style={{ color: colors.textSecondary, margin: '4px 0 0', fontSize: 14 }}>
          管理系统内所有文档解析器，支持配置、测试和切换
        </p>
      </div>

      <div className="yx-card">
        <div className="yx-toolbar" style={{ flexWrap: 'wrap' }}>
          <Input
            prefix={<SearchOutlined />}
            placeholder="搜索解析器..."
            style={{ width: 240 }}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
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
