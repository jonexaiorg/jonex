import React, { useMemo } from 'react'
import { Card, Table, Tag, Breadcrumb, Button } from 'antd'
import {
  ArrowLeftOutlined,
  LinkOutlined,
  FileTextOutlined,
  NodeIndexOutlined,
} from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import type { GraphRelation } from '@/types/viewModels'

const graphRelations: GraphRelation[] = []

export default function DomainKnowledgeRelationDetail() {
  const { id, relationId } = useParams<{ id: string; relationId: string }>()
  const navigate = useNavigate()

  const relation: GraphRelation | undefined = useMemo(
    () => graphRelations.find((rel) => rel.id === relationId),
    [relationId],
  )

  if (!relation) {
    return (
      <div>
        <a
          onClick={() => navigate(`/domain-knowledge/${id}/graph`)}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            marginBottom: 16,
            fontSize: 14,
            color: '#64748b',
            cursor: 'pointer',
          }}
        >
          <ArrowLeftOutlined /> 返回知识图谱
        </a>
        <Card
          className="yx-card"
          style={{ borderRadius: 14, border: '1px solid #eef2f6', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}
          styles={{ body: { padding: 48, textAlign: 'center' as const } }}
        >
          <div style={{ fontSize: 16, color: '#94a3b8' }}>未找到该关系</div>
          <Button
            type="primary"
            style={{ marginTop: 16 }}
            onClick={() => navigate(`/domain-knowledge/${id}/graph`)}
          >
            返回知识图谱
          </Button>
        </Card>
      </div>
    )
  }

  const propertyColumns = [
    {
      title: '属性名',
      dataIndex: 'key',
      key: 'key',
      width: 160,
      render: (v: string) => (
        <span style={{ fontWeight: 600, color: '#0b2b5c', fontSize: 13 }}>{v}</span>
      ),
    },
    {
      title: '属性值',
      dataIndex: 'value',
      key: 'value',
      render: (v: string) => (
        <span style={{ color: '#475569', fontSize: 13 }}>{v}</span>
      ),
    },
  ]

  return (
    <div>
      {/* Breadcrumb */}
      <div style={{ marginBottom: 16 }}>
        <Breadcrumb
          items={[
            {
              title: (
                <a onClick={() => navigate('/domain-knowledge')} style={{ color: '#64748b' }}>
                  领域知识管理
                </a>
              ),
            },
            {
              title: (
                <a onClick={() => navigate(`/domain-knowledge/${id}`)} style={{ color: '#64748b' }}>
                  知识库详情
                </a>
              ),
            },
            {
              title: (
                <a onClick={() => navigate(`/domain-knowledge/${id}/graph`)} style={{ color: '#64748b' }}>
                  知识图谱
                </a>
              ),
            },
            { title: <span style={{ color: '#0b2b5c', fontWeight: 500 }}>关系详情</span> },
          ]}
        />
      </div>

      {/* Back Button */}
      <a
        onClick={() => navigate(`/domain-knowledge/${id}/graph`)}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          marginBottom: 20,
          fontSize: 14,
          color: '#64748b',
          cursor: 'pointer',
        }}
      >
        <ArrowLeftOutlined style={{ fontSize: 12 }} /> 返回知识图谱
      </a>

      {/* Page Title */}
      <div className="yx-page-title" style={{ marginBottom: 20 }}>
        <h2
          style={{
            fontSize: 20,
            fontWeight: 700,
            color: '#0b2b5c',
            margin: 0,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <div
            style={{
              width: 42,
              height: 42,
              borderRadius: 10,
              background: 'linear-gradient(135deg, #10b981, #059669)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 20,
              color: '#fff',
            }}
          >
            <LinkOutlined />
          </div>
          {relation.name}
          <Tag color="green" style={{ fontSize: 12, marginLeft: 8 }}>
            {relation.type}
          </Tag>
        </h2>
      </div>

      {/* Relation Overview */}
      <Card
        className="yx-card"
        style={{
          borderRadius: 14,
          border: '1px solid #eef2f6',
          boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
          marginBottom: 20,
        }}
        styles={{ body: { padding: 24 } }}
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <LinkOutlined style={{ color: '#10b981' }} />
            <span style={{ fontSize: 15, fontWeight: 600, color: '#0b2b5c' }}>
              关系概览
            </span>
          </div>
        }
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '10px 18px',
              borderRadius: 10,
              background: '#eff6ff',
              border: '1px solid #dbeafe',
            }}
          >
            <NodeIndexOutlined style={{ color: '#3b82f6', fontSize: 16 }} />
            <div>
              <div style={{ fontSize: 11, color: '#94a3b8' }}>源实体</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#0b2b5c' }}>
                {relation.sourceEntity}
              </div>
            </div>
          </div>

          <div style={{ fontSize: 20, color: '#94a3b8', fontWeight: 700 }}>
            <ArrowLeftOutlined style={{ transform: 'rotate(180deg)' }} />
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '10px 18px',
              borderRadius: 10,
              background: '#ecfdf5',
              border: '1px solid #bbf7d0',
            }}
          >
            <NodeIndexOutlined style={{ color: '#10b981', fontSize: 16 }} />
            <div>
              <div style={{ fontSize: 11, color: '#94a3b8' }}>目标实体</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#0b2b5c' }}>
                {relation.targetEntity}
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Properties and Source Snippets */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Properties */}
        <Card
          className="yx-card"
          style={{ borderRadius: 14, border: '1px solid #eef2f6', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}
          styles={{ body: { padding: 24 } }}
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <FileTextOutlined style={{ color: '#3b82f6' }} />
              <span style={{ fontSize: 15, fontWeight: 600, color: '#0b2b5c' }}>
                关系属性
              </span>
            </div>
          }
        >
          <Table
            columns={propertyColumns}
            dataSource={relation.properties}
            rowKey="key"
            pagination={false}
            size="middle"
            showHeader={false}
          />
        </Card>

        {/* Source Text Snippets */}
        <Card
          className="yx-card"
          style={{ borderRadius: 14, border: '1px solid #eef2f6', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}
          styles={{ body: { padding: 24 } }}
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <FileTextOutlined style={{ color: '#f97316' }} />
              <span style={{ fontSize: 15, fontWeight: 600, color: '#0b2b5c' }}>
                原文片段
              </span>
            </div>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {relation.sourceSnippets.map((snippet, idx) => (
              <div
                key={idx}
                style={{
                  padding: '14px 16px',
                  borderRadius: 8,
                  background: '#fffbeb',
                  border: '1px solid #fef3c7',
                  fontSize: 13,
                  color: '#475569',
                  lineHeight: 1.7,
                  borderLeft: '3px solid #f59e0b',
                }}
              >
                <FileTextOutlined
                  style={{ color: '#f59e0b', marginRight: 8, fontSize: 12 }}
                />
                "{snippet}"
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}