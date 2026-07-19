import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Table, Tag, Row, Col } from 'antd'
import { useTranslation } from 'react-i18next'
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
import { MOCK_COMPILE_TASKS, type CompileTask } from '../../data/mock'

const statusConfig: Record<string, { color: string; label: string }> = {
  running: { color: 'processing', label: 'status.running' },
  completed: { color: 'success', label: 'status.completed' },
  failed: { color: 'error', label: 'status.failed' },
  pending: { color: 'default', label: 'status.waiting' },
}

export default function KnowledgeCompile() {
  const navigate = useNavigate()
  const { t } = useTranslation()

  const stats = [
    {
      title: t('knowledgeCompile.totalTasks', '编译任务总数'),
      value: MOCK_COMPILE_TASKS.length.toString(),
      icon: <BuildOutlined />,
      color: colors.accent,
      bg: `${colors.accent}15`,
    },
    {
      title: t('knowledgeCompile.entityCount'),
      value: MOCK_COMPILE_TASKS.reduce((s, t) => s + t.entityCount, 0).toLocaleString(),
      icon: <NodeIndexOutlined />,
      color: '#10b981',
      bg: '#ecfdf5',
    },
    {
      title: t('knowledgeCompile.relationCount'),
      value: MOCK_COMPILE_TASKS.reduce((s, t) => s + t.relationCount, 0).toLocaleString(),
      icon: <ApartmentOutlined />,
      color: '#8b5cf6',
      bg: '#f5f3ff',
    },
    {
      title: t('knowledgeCompile.chunkCount', 'Chunk 总数'),
      value: MOCK_COMPILE_TASKS.reduce((s, t) => s + t.chunkCount, 0).toLocaleString(),
      icon: <BlockOutlined />,
      color: '#f59e0b',
      bg: '#fffbeb',
    },
  ]

  const subPages = [
    { title: t('knowledgeCompile.search'), desc: t('knowledgeCompile.searchDesc', '搜索已编译的知识内容'), path: '/knowledge-compile/search', icon: <SearchOutlined />, color: '#3b82f6' },
    { title: t('knowledgeCompile.graph'), desc: t('knowledgeCompile.graphDesc', '查看编译生成的知识图谱'), path: '/knowledge-compile/graph', icon: <ApartmentOutlined />, color: '#8b5cf6' },
    { title: t('knowledgeCompile.vector'), desc: t('knowledgeCompile.vectorDesc', '向量相似度搜索与召回测试'), path: '/knowledge-compile/vector', icon: <BlockOutlined />, color: '#10b981' },
    { title: t('knowledgeCompile.compile'), desc: t('knowledgeCompile.compileDesc', '管理编译任务与调度'), path: '/knowledge-compile/compile', icon: <ThunderboltOutlined />, color: '#f59e0b' },
  ]

  const columns = [
    {
      title: t('taskSchedule.taskName'),
      dataIndex: 'name',
      key: 'name',
      render: (v: string) => (
        <a className="yx-table-action" onClick={() => navigate('/knowledge-compile/compile')}>{v}</a>
      ),
    },
    { title: t('taskSchedule.taskType'), dataIndex: 'type', key: 'type' },
    {
      title: t('knowledgeCompile.compileStatus'),
      dataIndex: 'status',
      key: 'status',
      render: (v: string) => {
        const cfg = statusConfig[v] || { color: 'default', label: v }
        return <Tag color={cfg.color}>{t(cfg.label)}</Tag>
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
    { title: t('operationLog.createdAt'), dataIndex: 'updatedAt', key: 'updatedAt' },
  ]

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('knowledgeCompile.title')}</h1>
        <p style={{ color: colors.textSecondary, margin: '4px 0 0', fontSize: 14 }}>
          {t('knowledgeCompile.description', '管理知识库的编译、图谱构建和向量化')}
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
          {t('knowledgeCompile.recentTasks', '最近编译任务')}
        </h3>
        <Table
          columns={columns}
          dataSource={MOCK_COMPILE_TASKS}
          rowKey="id"
          pagination={false}
          size="middle"
        />
      </div>
    </div>
  )
}
