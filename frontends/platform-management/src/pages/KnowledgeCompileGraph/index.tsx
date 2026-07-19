import React from 'react'
import { Card, Row, Col, Tag, Table } from 'antd'
import { useTranslation } from 'react-i18next'
import { ApartmentOutlined, NodeIndexOutlined, LinkOutlined } from '@ant-design/icons'
import { colors, radius } from '@jonex/platform-theme/tokens'

const graphStats = [
  { title: 'knowledgeCompile.totalEntities', value: '17,100', icon: <NodeIndexOutlined />, color: colors.accent },
  { title: 'knowledgeCompile.totalRelations', value: '47,900', icon: <ApartmentOutlined />, color: '#10b981' },
  { title: 'knowledgeCompile.relationTypes', value: '24', icon: <LinkOutlined />, color: '#8b5cf6' },
]

const mockEntities = [
  { id: '1', name: '心血管疾病', type: '疾病', relationCount: 156, updatedAt: '2026-06-01' },
  { id: '2', name: '阿司匹林', type: '药品', relationCount: 89, updatedAt: '2026-06-01' },
  { id: '3', name: '高血压', type: '症状', relationCount: 134, updatedAt: '2026-06-01' },
  { id: '4', name: '供应链金融', type: '业务', relationCount: 112, updatedAt: '2026-06-02' },
  { id: '5', name: '智能风控', type: '技术', relationCount: 98, updatedAt: '2026-06-02' },
]

export default function KnowledgeCompileGraph() {
  const { t } = useTranslation()

  const columns = [
    { title: t('knowledgeCompile.entityName', '实体名称'), dataIndex: 'name', key: 'name', render: (v: string) => <span style={{ fontWeight: 500, color: colors.textPrimary }}>{v}</span> },
    { title: t('knowledgeCompile.entityType', '类型'), dataIndex: 'type', key: 'type', render: (v: string) => <Tag>{v}</Tag> },
    { title: t('knowledgeCompile.relationCount'), dataIndex: 'relationCount', key: 'relationCount' },
    { title: t('operationLog.createdAt'), dataIndex: 'updatedAt', key: 'updatedAt' },
  ]

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('knowledgeCompile.graph')}</h1>
        <p style={{ color: colors.textSecondary, margin: '4px 0 0', fontSize: 14 }}>
          {t('knowledgeCompile.graphDesc', '查看和管理编译生成的知识图谱')}
        </p>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
        {graphStats.map((s) => (
          <Col xs={24} sm={8} key={s.title}>
            <Card style={{ borderRadius: radius.card, border: `1px solid ${colors.border}` }} styles={{ body: { padding: '20px 24px' } }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: 10,
                    background: `${s.color}15`,
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
                  <div style={{ fontSize: 12, color: colors.textMuted }}>{t(s.title)}</div>
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Card
        style={{ borderRadius: radius.card, border: `1px solid ${colors.border}`, marginBottom: 20 }}
        styles={{ body: { padding: 24 } }}
      >
        <div style={{
          height: 320,
          background: colors.overlay,
          borderRadius: 12,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
          gap: 12,
        }}>
          <ApartmentOutlined style={{ fontSize: 64, color: colors.textMuted }} />
          <div style={{ fontSize: 15, color: colors.textSecondary }}>{t('knowledgeCompile.graphVisualArea', '知识图谱可视化区域')}</div>
          <div style={{ fontSize: 12, color: colors.textMuted }}>{t('knowledgeCompile.graphVisualDesc', '将在此区域展示知识图谱的可视化渲染')}</div>
        </div>
      </Card>

      <Card style={{ borderRadius: radius.card, border: `1px solid ${colors.border}` }} styles={{ body: { padding: 24 } }}>
        <h3 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 600, color: colors.textPrimary, paddingBottom: 12, borderBottom: `1px solid ${colors.border}` }}>
          {t('knowledgeCompile.entityList', '实体列表')}
        </h3>
        <Table columns={columns} dataSource={mockEntities} rowKey="id" pagination={false} size="middle" />
      </Card>
    </div>
  )
}
