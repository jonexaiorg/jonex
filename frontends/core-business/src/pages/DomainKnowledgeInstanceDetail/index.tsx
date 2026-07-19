import React, { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, Table, Tag, Descriptions, Breadcrumb, Button } from 'antd'
import {
  ArrowLeftOutlined,
  NodeIndexOutlined,
  LinkOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import { MOCK_GRAPH_INSTANCES } from '@/data/mock'
import type { GraphInstance } from '@/data/mock'

export default function DomainKnowledgeInstanceDetail() {
  const { t } = useTranslation()
  const { id, instanceId } = useParams<{ id: string; instanceId: string }>()
  const navigate = useNavigate()

  const instance: GraphInstance | undefined = useMemo(
    () => MOCK_GRAPH_INSTANCES.find((inst) => inst.id === instanceId),
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
          <ArrowLeftOutlined /> {t('knowledgeSearch.knowledgeGraph')}
        </a>
        <Card
          className="yx-card"
          style={{ borderRadius: 14, border: '1px solid #eef2f6', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}
          styles={{ body: { padding: 48, textAlign: 'center' as const } }}
        >
          <div style={{ fontSize: 16, color: '#94a3b8' }}>Entity instance not found</div>
          <Button
            type="primary"
            style={{ marginTop: 16 }}
            onClick={() => navigate(`/domain-knowledge/${id}/graph`)}
          >
            {t('knowledgeSearch.knowledgeGraph')}
          </Button>
        </Card>
      </div>
    )
  }

  const propertyColumns = [
    {
      title: t('ontology.attributeName'),
      dataIndex: 'key',
      key: 'key',
      width: 160,
      render: (v: string) => (
        <span style={{ fontWeight: 600, color: '#0b2b5c', fontSize: 13 }}>{v}</span>
      ),
    },
    {
      title: t('ontology.attributeValue'),
      dataIndex: 'value',
      key: 'value',
      render: (v: string) => (
        <span style={{ color: '#475569', fontSize: 13 }}>{v}</span>
      ),
    },
  ]

  const relationColumns = [
    {
      title: t('ontology.relationName'),
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
      title: t('ontology.relatedEntity'),
      dataIndex: 'target',
      key: 'target',
      render: (v: string) => (
        <span style={{ color: '#475569', fontSize: 13 }}>{v}</span>
      ),
    },
    {
      title: t('knowledgeSearch.actions'),
      key: 'actions',
      width: 100,
      render: (_: unknown, record: { id: string }) => (
        <a
          className="yx-table-action"
          onClick={() =>
            navigate(`/domain-knowledge/${id}/graph/relations/${record.id}`)
          }
        >
            {t('domainKnowledge.detail')}
        </a>
      ),
    },
  ]

  return (
    <div>
      { }
      <div style={{ marginBottom: 16 }}>
        <Breadcrumb
          items={[
            {
              title: (
                <a onClick={() => navigate('/domain-knowledge')} style={{ color: '#64748b' }}>
                  {t('domainKnowledge.title')}
                </a>
              ),
            },
            {
              title: (
                <a onClick={() => navigate(`/domain-knowledge/${id}`)} style={{ color: '#64748b' }}>
                  {t('domainKnowledge.detail')}
                </a>
              ),
            },
            {
              title: (
                <a onClick={() => navigate(`/domain-knowledge/${id}/graph`)} style={{ color: '#64748b' }}>
                  {t('knowledgeSearch.knowledgeGraph')}
                </a>
              ),
            },
            { title: <span style={{ color: '#0b2b5c', fontWeight: 500 }}>{t('knowledgeSearch.entityInstance')}</span> },
          ]}
        />
      </div>

      { }
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
        <ArrowLeftOutlined style={{ fontSize: 12 }} /> {t('knowledgeSearch.knowledgeGraph')}
      </a>

      { }
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

      { }
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        { }
        <Card
          className="yx-card"
          style={{ borderRadius: 14, border: '1px solid #eef2f6', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}
          styles={{ body: { padding: 24 } }}
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <FileTextOutlined style={{ color: '#3b82f6' }} />
              <span style={{ fontSize: 15, fontWeight: 600, color: '#0b2b5c' }}>
                {t('ontology.entity')}
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

        { }
        <Card
          className="yx-card"
          style={{ borderRadius: 14, border: '1px solid #eef2f6', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}
          styles={{ body: { padding: 24 } }}
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <LinkOutlined style={{ color: '#10b981' }} />
              <span style={{ fontSize: 15, fontWeight: 600, color: '#0b2b5c' }}>
                {t('ontology.relation')}
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

      { }
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
              Source Documents
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