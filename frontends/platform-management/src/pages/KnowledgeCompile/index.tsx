import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Table, Tag, Row, Col } from 'antd'
import {
  SearchOutlined,
  ApartmentOutlined,
  BlockOutlined,
  BuildOutlined,
  FileTextOutlined,
  NodeIndexOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { colors, radius } from '@jonex/platform-theme/tokens'
import type { CompileTask } from '../../types/management'

const compileTasks: CompileTask[] = []

const statusConfig: Record<string, { color: string; label: string }> = {
  running: { color: 'processing', label: '运行中' },
  completed: { color: 'success', label: '已完成' },
  failed: { color: 'error', label: '失败' },
  pending: { color: 'default', label: '等待中' },
}

const stats = [
  {
    title: '编译任务总数',
    value: compileTasks.length,
    icon: <BuildOutlined />,
    color: colors.accent,
    bg: `${colors.accent}15`,
  },
  {
    title: '实体总数',
    value: compileTasks.reduce((s, t) => s + t.entityCount, 0).toLocaleString(),
    icon: <NodeIndexOutlined />,
    color: '#10b981',
    bg: '#ecfdf5',
  },
  {
    title: '关系总数',
    value: compileTasks.reduce((s, t) => s + t.relationCount, 0).toLocaleString(),
    icon: <ApartmentOutlined />,
    color: '#8b5cf6',
    bg: '#f5f3ff',
  },
  {
    title: 'Chunk 总数',
    value: compileTasks.reduce((s, t) => s + t.chunkCount, 0).toLocaleString(),
    icon: <BlockOutlined />,
    color: '#f59e0b',
    bg: '#fffbeb',
  },
]

const subPages = [
  { title: '编译检索', desc: '搜索已编译的知识内容', path: '/knowledge-compile/search', icon: <SearchOutlined />, color: '#3b82f6' },
  { title: '知识图谱', desc: '查看编译生成的知识图谱', path: '/knowledge-compile/graph', icon: <ApartmentOutlined />, color: '#8b5cf6' },
  { title: '向量检索', desc: '向量相似度搜索与召回测试', path: '/knowledge-compile/vector', icon: <BlockOutlined />, color: '#10b981' },
  { title: '编译管理', desc: '管理编译任务与调度', path: '/knowledge-compile/compile', icon: <ThunderboltOutlined />, color: '#f59e0b' },
]

export default function KnowledgeCompile() {
  const navigate = useNavigate()

  const columns = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      render: (v: string) => (
        <a className="yx-table-action" onClick={() => navigate('/knowledge-compile/compile')}>{v}</a>
      ),
    },
    { title: '类型', dataIndex: 'type', key: 'type' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (v: string) => {
        const cfg = statusConfig[v] || { color: 'default', label: v }
        return <Tag color={cfg.color}>{cfg.label}</Tag>
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
    { title: '更新时间', dataIndex: 'updatedAt', key: 'updatedAt' },
  ]

  return (
    <div>
      <div className="yx-page-title">
        <h1>知识编译</h1>
        <p style={{ color: colors.textSecondary, margin: '4px 0 0', fontSize: 14 }}>
          管理知识库的编译、图谱构建和向量化
        </p>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {stats.map((s) => (
          <Col xs={24} sm={12} md={6} key={s.title}>
            <Card
              style={{ borderRadius: radius.card, border: `1px solid ${colors.border}` }}
              styles={{ body: { padding: '20px 24px' } }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: 10,
                    background: s.bg,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 20,
                    color: s.color,
                  }}
                >
                  {s.icon}
                </div>
                <div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: colors.textPrimary }}>{s.value}</div>
                  <div style={{ fontSize: 12, color: colors.textMuted }}>{s.title}</div>
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
        {subPages.map((p) => (
          <Col xs={24} sm={12} md={6} key={p.title}>
            <div
              onClick={() => navigate(p.path)}
              style={{
                background: colors.white,
                border: `1px solid ${colors.border}`,
                borderRadius: radius.card,
                padding: '18px 20px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                transition: 'all 0.2s',
              }}
            >
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 10,
                  background: `${p.color}15`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 18,
                  color: p.color,
                }}
              >
                {p.icon}
              </div>
              <div>
                <div style={{ fontSize: 14, fontWeight: 500, color: colors.textPrimary }}>{p.title}</div>
                <div style={{ fontSize: 12, color: colors.textMuted }}>{p.desc}</div>
              </div>
            </div>
          </Col>
        ))}
      </Row>

      <div className="yx-card">
        <h3 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 600, color: colors.textPrimary, paddingBottom: 12, borderBottom: `1px solid ${colors.border}` }}>
          <FileTextOutlined style={{ marginRight: 8, color: colors.accent }} />
          最近编译任务
        </h3>
        <Table
          columns={columns}
          dataSource={compileTasks}
          rowKey="id"
          pagination={false}
          size="middle"
        />
      </div>
    </div>
  )
}
