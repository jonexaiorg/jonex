import React, { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Input, Table, Breadcrumb, message } from 'antd'
import { ArrowLeftOutlined, SearchOutlined, LinkOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import type { RelationInstanceRow } from '@/types/domainKnowledge'
import { getOntologyRelationInstances, getOntologyEntityTypes, getOntologyRelationTypes } from '@/api/domainKnowledge'

const PAGE_SIZE = 10

export default function DomainKnowledgeRelationList() {
  const { t } = useTranslation()
  const { id, relationName } = useParams<{ id: string; relationName: string }>()
  const navigate = useNavigate()
  const decodedName = decodeURIComponent(relationName || '')

  const [instances, setInstances] = useState<RelationInstanceRow[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [typeNameMap, setTypeNameMap] = useState<Record<string, string>>({})
  const [relTypeNameMap, setRelTypeNameMap] = useState<Record<string, string>>({})


  useEffect(() => {
    if (!id) return
    getOntologyEntityTypes(id).then((res) => {
      const map: Record<string, string> = {}
      res.items.forEach((et) => { map[et.name] = et.display_name || et.name })
      setTypeNameMap(map)
    }).catch(() => {})
  }, [id])


  useEffect(() => {
    if (!id) return
    getOntologyRelationTypes(id).then((res) => {
      const map: Record<string, string> = {}
      res.items.forEach((rt) => { map[rt.name] = rt.display_name || rt.name })
      setRelTypeNameMap(map)
    }).catch(() => {})
  }, [id])

  const fetchData = useCallback(async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const result = await getOntologyRelationInstances({
        kbId: id,
        relationType: decodedName || undefined,
        sourceName: keyword || undefined,
        targetName: keyword || undefined,
        page,
        pageSize: PAGE_SIZE,
      })
      setInstances(result.items)
      setTotal(result.total)
    } catch (err: any) {
      setError(err?.message || t('domainKnowledge.loadFailed'))
      message.error(err?.message || t('domainKnowledge.loadFailed'))
    } finally {
      setLoading(false)
    }
  }, [id, decodedName, keyword, page])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  const breadcrumbItems = [
    { title: <a onClick={() => navigate('/domain-knowledge')} style={{ color: '#64748b' }}>{t('domainKnowledge.title')}</a> },
    { title: <a onClick={() => navigate(`/domain-knowledge/${id}`)} style={{ color: '#64748b' }}>{t('domainKnowledge.detail')}</a> },
    { title: <span style={{ color: '#0b2b5c', fontWeight: 500 }}>{decodedName} Instances</span> },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Breadcrumb items={breadcrumbItems} />
      </div>

      <a
        onClick={() => navigate(`/domain-knowledge/${id}`)}
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 6,
          fontSize: 14, color: '#64748b', cursor: 'pointer', padding: '4px 0',
        }}
      >
        <ArrowLeftOutlined style={{ fontSize: 12 }} /> {t('domainKnowledge.title')}
      </a>

      <div
        style={{
          display: 'flex', alignItems: 'center', gap: 16,
          marginTop: 20, marginBottom: 24, padding: '20px 24px',
          background: '#fff', borderRadius: 14, border: '1px solid #eef2f6',
        }}
      >
        <div
          style={{
            width: 52, height: 52, borderRadius: 12, display: 'flex',
            alignItems: 'center', justifyContent: 'center', fontSize: 24,
            background: '#f0f9ff', color: '#8b5cf6', flexShrink: 0,
          }}
        >
          <LinkOutlined />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#0b2b5c', margin: 0 }}>
            {decodedName} - Relation Instances
          </h2>
          <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 4 }}>
            All AI-extracted relation instances for this relation type.
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#8b5cf6' }}>
            {total.toLocaleString()}
          </div>
          <div style={{ fontSize: 12, color: '#94a3b8' }}>{t('domainKnowledge.relationCount')}</div>
        </div>
      </div>

      <div
        style={{
          background: '#fff', borderRadius: 14, border: '1px solid #eef2f6',
          padding: 24, boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#0b2b5c', display: 'flex', alignItems: 'center', gap: 8 }}>
            <LinkOutlined style={{ color: '#8b5cf6' }} /> {t('knowledgeSearch.relationList')}
          </h3>
          <Input
            prefix={<SearchOutlined />}
            placeholder="Search source or target names..."
            style={{ width: 200 }}
            value={keyword}
            onChange={(e) => { setKeyword(e.target.value); setPage(1) }}
          />
        </div>

        {error && instances.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 48, color: '#94a3b8' }}>{error}</div>
        ) : (
          <>
            <Table
              columns={[
                {
                  title: t('ontology.relatedEntity'), dataIndex: 'source', key: 'source', width: 200,
                  render: (v: string, r: RelationInstanceRow) => (
                    <div>
                      <span style={{ padding: '2px 8px', borderRadius: 6, background: '#eff6ff', color: '#3b82f6', fontSize: 12, fontWeight: 500 }}>{v}</span>
                      {r.source_type && <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{typeNameMap[r.source_type] || r.source_type}</div>}
                    </div>
                  ),
                },
                {
                  title: t('ontology.relationName'), dataIndex: 'relation_type', key: 'relation_type', width: 120,
                  render: (v: string) => (
                    <span style={{ padding: '2px 8px', borderRadius: 6, background: '#eff6ff', color: '#3b82f6', fontSize: 12, fontWeight: 500 }}>{relTypeNameMap[v] || v}</span>
                  ),
                },
                {
                  title: 'Target Object', dataIndex: 'target', key: 'target', width: 200,
                  render: (v: string, r: RelationInstanceRow) => (
                    <div>
                      <span style={{ padding: '2px 8px', borderRadius: 6, background: '#ecfdf5', color: '#059669', fontSize: 12, fontWeight: 500 }}>{v}</span>
                      {r.target_type && <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{typeNameMap[r.target_type] || r.target_type}</div>}
                    </div>
                  ),
                },
                {
                  title: 'Confidence', dataIndex: 'confidence', key: 'confidence', width: 80,
                  render: (v: number | null) => v != null ? `${(v * 100).toFixed(0)}%` : '—',
                },
              ]}
              dataSource={instances}
              rowKey={(r, i) => `${r.source}-${r.target}-${r.relation_type}-${i}`}
              pagination={false}
              size="middle"
              loading={loading}
              locale={{ emptyText: <span style={{ color: '#94a3b8' }}>No relation instance data</span> }}
            />

            <div
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 6,
                padding: '12px 0 0', borderTop: '1px solid #eef2f6', marginTop: 12,
              }}
            >
              <span
                className={`yx-page-btn${page <= 1 ? ' disabled' : ''}`}
                onClick={() => page > 1 && setPage((p) => p - 1)}
                style={{
                  width: 34, height: 34, display: 'inline-flex', alignItems: 'center',
                  justifyContent: 'center', borderRadius: 8, border: '1px solid #e2e8f0',
                  cursor: page <= 1 ? 'not-allowed' : 'pointer', color: '#94a3b8', fontSize: 12,
                  opacity: page <= 1 ? 0.4 : 1,
                }}
              >
                {'<'}
              </span>
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                const n = i + 1
                return (
                  <span key={n} className={`yx-page-btn${n === page ? ' active' : ''}`} onClick={() => setPage(n)}
                    style={{
                      width: 34, height: 34, display: 'inline-flex', alignItems: 'center',
                      justifyContent: 'center', borderRadius: 8,
                      background: n === page ? '#3b82f6' : 'transparent',
                      color: n === page ? '#fff' : '#64748b',
                      fontWeight: n === page ? 600 : 400, fontSize: 13, cursor: 'pointer',
                      border: n === page ? 'none' : '1px solid #e2e8f0',
                    }}
                  >{n}</span>
                )
              })}
              <span
                className={`yx-page-btn${page >= totalPages ? ' disabled' : ''}`}
                onClick={() => page < totalPages && setPage((p) => p + 1)}
                style={{
                  width: 34, height: 34, display: 'inline-flex', alignItems: 'center',
                  justifyContent: 'center', borderRadius: 8, border: '1px solid #e2e8f0',
                  cursor: page >= totalPages ? 'not-allowed' : 'pointer', color: '#94a3b8', fontSize: 12,
                  opacity: page >= totalPages ? 0.4 : 1,
                }}
              >
                {'>'}
              </span>
              <span style={{ fontSize: 13, color: '#94a3b8', marginLeft: 12 }}>
                {t('common.totalPage', { total: total.toLocaleString(), page, totalPages })}
              </span>
            </div>
          </>
        )}
      </div>

      <div style={{ marginTop: 12 }}>
        <a
          onClick={() => navigate(`/domain-knowledge/${id}`)}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            padding: '8px 20px', borderRadius: 8, border: '1px solid #d1d5db',
            background: '#fff', color: '#64748b', cursor: 'pointer',
            fontSize: 13, textDecoration: 'none',
          }}
        >
          <ArrowLeftOutlined /> {t('domainKnowledge.title')}
        </a>
      </div>
    </div>
  )
}