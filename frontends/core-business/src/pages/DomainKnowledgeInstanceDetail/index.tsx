import React, { useMemo } from 'react'
import { Card, Table, Tag, Descriptions, Breadcrumb, Button } from 'antd'
import {
  ArrowLeftOutlined,
  NodeIndexOutlined,
  LinkOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import type { GraphInstance } from '@/types/viewModels'

const graphInstances: GraphInstance[] = []

export default function DomainKnowledgeInstanceDetail() {
  const { id, instanceId } = useParams<{ id: string; instanceId: string }>()
  const navigate = useNavigate()

  const instance: GraphInstance | undefined = useMemo(
    () => graphInstances.find((inst) => inst.id === instanceId),
    [instanceId],
  )

  if (!instance) {
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
          <div style={{ fontSize: 16, color: '#94a3b8' }}>未找到该实体实例</div>
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

  const relationColumns = [
    {
      title: '关系名称',
      dataIndex: 'name',
      key: 'name',
      width: 160,
      render: (v: string) => (
        <Tag color="processing" style={{ fontSize: 12 }}>
          {v}
        </Tag>
      ),
    },
    {
      title: '关联实体',
      dataIndex: 'target',
      key: 'target',
      render: (v: string) => (
        <span style={{ color: '#475569', fontSize: 13 }}>{v}</span>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_: unknown, record: { id: string }) => (
        <a
          className="yx-table-action"
          onClick={() =>
            navigate(`/domain-knowledge/${id}/graph/relations/${record.id}`)
          }
        >
          查看详情
        </a>
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
            { title: <span style={{ color: '#0b2b5c', fontWeight: 500 }}>实体实例详情</span> },
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
              background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 20,
              color: '#fff',
            }}
          >
            <NodeIndexOutlined />
          </div>
          {instance.name}
          <Tag color="blue" style={{ fontSize: 12, marginLeft: 8 }}>
            {instance.type}
          </Tag>
        </h2>
      </div>

      {/* Entity Info */}
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
                实体属性
              </span>
            </div>
          }
        >
          <Table
            columns={propertyColumns}
            dataSource={instance.properties}
            rowKey="key"
            pagination={false}
            size="middle"
            showHeader={false}
          />
        </Card>

        {/* Relations */}
        <Card
          className="yx-card"
          style={{ borderRadius: 14, border: '1px solid #eef2f6', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}
          styles={{ body: { padding: 24 } }}
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <LinkOutlined style={{ color: '#10b981' }} />
              <span style={{ fontSize: 15, fontWeight: 600, color: '#0b2b5c' }}>
                关联关系
              </span>
            </div>
          }
        >
          <Table
            columns={relationColumns}
            dataSource={instance.relations}
            rowKey="id"
            pagination={false}
            size="middle"
          />
        </Card>
      </div>

      {/* Source Documents */}
      <Card
        className="yx-card"
        style={{
          borderRadius: 14,
          border: '1px solid #eef2f6',
          boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
          marginTop: 20,
        }}
        styles={{ body: { padding: 24 } }}
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <FileTextOutlined style={{ color: '#f97316' }} />
            <span style={{ fontSize: 15, fontWeight: 600, color: '#0b2b5c' }}>
              来源文档
            </span>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {instance.sourceDocs.map((doc, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '10px 14px',
                borderRadius: 8,
                background: '#f8fafc',
                border: '1px solid #eef2f6',
                fontSize: 13,
                color: '#475569',
              }}
            >
              <FileTextOutlined style={{ color: '#94a3b8' }} />
              {doc}
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}