import React, { useEffect, useRef, useState, useCallback } from 'react'
import {
  Button, Card, Tag, Space, Breadcrumb, Spin, Empty, Input, message, Select, Tooltip,
} from 'antd'
import {
  ArrowLeftOutlined, SearchOutlined, ReloadOutlined,
  ZoomInOutlined, ZoomOutOutlined, ExpandAltOutlined,
  InfoCircleOutlined, FilterOutlined, NodeExpandOutlined,
} from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  getOntologyGraph,
  getOntologyStatistics,
  expandOntologyNeighbors,
} from '@/api/domainKnowledge'
import type {
  OntologyGraphNode,
  OntologyGraphEdge,
  OntologyGraphData,
  OntologyStatistics,
} from '@/types/domainKnowledge'


const TYPE_COLORS: Record<string, string> = {}
const COLOR_PALETTE = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
  '#8b5cf6', '#ec4899', '#06b6d4', '#f97316',
  '#14b8a6', '#6366f1', '#84cc16', '#d946ef',
]
let _colorIdx = 0
function getTypeColor(type: string): string {
  if (!TYPE_COLORS[type]) {
    TYPE_COLORS[type] = COLOR_PALETTE[_colorIdx % COLOR_PALETTE.length]
    _colorIdx++
  }
  return TYPE_COLORS[type]
}




const NODE_LABEL_LIMIT = 500
const EDGE_LABEL_LIMIT = 1000

const LARGE_GRAPH_THRESHOLD = 200

const WEBGL_RENDER_THRESHOLD = 200

function mapNode(n: OntologyGraphNode, showLabel = true) {
  const label = n.name.length > 12 ? n.name.slice(0, 12) + '…' : n.name
  const style: Record<string, any> = {
    fill: getTypeColor(n.type),
    size: 30 + Math.min((n.doc_ids?.length || 0) * 3, 30),
    lineWidth: 2,
    stroke: getTypeColor(n.type),
  }

  if (showLabel) {
    style.labelText = label
    style.labelFill = '#475569'
    style.labelFontSize = 11
    style.labelOffsetY = 8
  }
  return {
    id: n.id,
    data: {
      label,
      fullLabel: n.name,
      type: n.type,
      description: n.description || '',
      aliases: n.aliases || [],
      attributes: n.attributes || {},
      confidence: n.confidence ?? 1,
      docIds: n.doc_ids || [],
    },
    style,
  }
}

function mapEdge(e: OntologyGraphEdge, showLabel = true) {
  const style: Record<string, any> = {
    stroke: '#cbd5e1',
    lineWidth: 1,
    endArrow: true,
  }

  if (showLabel) {
    style.labelText = e.label
    style.labelFill = '#94a3b8'
    style.labelFontSize = 9
  }
  return {
    id: edgeKey(e),
    source: `${e.source_type}:${e.source}`,
    target: `${e.target_type}:${e.target}`,
    data: {
      label: e.label,
      confidence: e.confidence ?? 1,
    },
    style,
  }
}


function edgeKey(e: OntologyGraphEdge): string {
  return `${e.source_type}:${e.source}__${e.label}__${e.target_type}:${e.target}`
}

function buildGraphData(raw: { nodes: OntologyGraphNode[]; edges: OntologyGraphEdge[] }) {
  const showNodeLabels = raw.nodes.length <= NODE_LABEL_LIMIT
  const showEdgeLabels = raw.edges.length <= EDGE_LABEL_LIMIT


  const seenNodes = new Set<string>()
  const nodes = raw.nodes
    .filter((n) => {
      if (seenNodes.has(n.id)) return false
      seenNodes.add(n.id)
      return true
    })
    .map((n) => mapNode(n, showNodeLabels))


  const seenEdges = new Set<string>()
  const edges = raw.edges
    .filter((e) => {
      const k = edgeKey(e)
      if (seenEdges.has(k)) return false
      seenEdges.add(k)
      return true
    })
    .map((e) => mapEdge(e, showEdgeLabels))

  return { nodes, edges }
}

export default function DomainKnowledgeGraph() {
  const { id: kbId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const containerRef = useRef<HTMLDivElement>(null)
  const graphRef = useRef<any>(null)

  const currentDataRef = useRef<OntologyGraphData | null>(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState<OntologyStatistics | null>(null)
  const [selectedNode, setSelectedNode] = useState<any>(null)
  const [typeDistribution, setTypeDistribution] = useState<{ type: string; count: number }[]>([])
  const [searchKeyword, setSearchKeyword] = useState('')

  const [selectedTypes, setSelectedTypes] = useState<string[]>([])

  const [meta, setMeta] = useState<{
    total_nodes: number
    total_relations: number
    returned_nodes: number
    returned_edges: number
    truncated: boolean
  } | null>(null)

  const [expanding, setExpanding] = useState(false)

  const [degraded, setDegraded] = useState(false)
  const [degradedReason, setDegradedReason] = useState('')
  const { t } = useTranslation()

  const NODE_LIMIT = 500


  const loadData = useCallback(async () => {
    if (!kbId) return
    setLoading(true)
    setError(null)
    try {
      const [graphData, statsData] = await Promise.all([
        getOntologyGraph(kbId, {
          limit: NODE_LIMIT,
          entityTypes: selectedTypes.length ? selectedTypes : undefined,
        }),
        getOntologyStatistics(kbId),
      ])
      currentDataRef.current = graphData
      setStats(statsData)
      setDegraded(!!graphData.degraded)
      setDegradedReason(graphData.degraded_reason || '')
      setMeta({
        total_nodes: graphData.total_nodes,
        total_relations: graphData.total_relations,
        returned_nodes: graphData.returned_nodes,
        returned_edges: graphData.returned_edges,
        truncated: graphData.truncated,
      })


      const dist = Object.entries(graphData.type_counts || {})
        .map(([type, count]) => ({ type, count }))
        .sort((a, b) => b.count - a.count)
      setTypeDistribution(dist)

      await renderGraph(graphData)
    } catch (e: any) {
      setError(e?.message || t('domainGraph.loadFailed'))
    } finally {
      setLoading(false)
    }
  }, [kbId, selectedTypes])


  const renderGraph = useCallback(async (raw: OntologyGraphData) => {
    if (!containerRef.current) {
      console.warn('[Graph] containerRef.current is null')
      return
    }


    if (graphRef.current) {
      graphRef.current.destroy()
      graphRef.current = null
    }

    const gData = buildGraphData(raw)
    console.log('[Graph] rendering with', gData.nodes.length, 'nodes,', gData.edges.length, 'edges')


    const isLarge = gData.nodes.length > LARGE_GRAPH_THRESHOLD
    const layout = isLarge
      ? {
          type: 'd3-force',
          linkDistance: 80,
          manyBody: { strength: -80 },
          animate: false,
        }
      : {
          type: 'd3-force',
          linkDistance: 120,
          collide: { radius: 40 },
          manyBody: { strength: -400 },
          animate: false,
        }

    try {
      const { Graph: G6Graph } = await import('@antv/g6')



      let renderer: (() => any) | undefined
      if (gData.nodes.length > WEBGL_RENDER_THRESHOLD) {
        try {

          const webgl: any = await import('@antv/g-webgl')
          const WebGLRenderer = webgl.Renderer

          renderer = () => new WebGLRenderer()
          console.log('[Graph] using WebGL renderer for', gData.nodes.length, 'nodes')
        } catch (err) {
          console.warn('[Graph] WebGL 渲染器加载失败，回退默认 Canvas:', err)
        }
      }

      const graph = new G6Graph({
        container: containerRef.current,
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight,
        data: gData,
        ...(renderer ? { renderer } : {}),
        layout,
        node: {
          type: 'circle',
          style: { cursor: 'pointer' },
        },
        edge: {
          type: 'line',
          style: { cursor: 'default', endArrow: true },
        },
        behaviors: ['zoom-canvas', 'drag-canvas', 'drag-element'],
        autoFit: 'view',
        animation: false,
      })


      graph.on('node:click', (evt: any) => {
        const nodeId = evt?.target?.id
        if (!nodeId) return
        const data = currentDataRef.current
        if (!data) return
        const nodeData = data.nodes.find((n) => n.id === nodeId)
        if (!nodeData) return

        const connectedEdges = data.edges.filter(
          (e) => `${e.source_type}:${e.source}` === nodeId || `${e.target_type}:${e.target}` === nodeId,
        )
        const neighborIds = new Set<string>()
        connectedEdges.forEach((e) => {
          const srcCid = `${e.source_type}:${e.source}`
          const tgtCid = `${e.target_type}:${e.target}`
          if (srcCid !== nodeId) neighborIds.add(srcCid)
          if (tgtCid !== nodeId) neighborIds.add(tgtCid)
        })

        setSelectedNode({
          ...nodeData,
          neighbors: Array.from(neighborIds),
          connectedEdges,
          typeColor: getTypeColor(nodeData.type),
        })
      })


      graph.on('node:dblclick', (evt: any) => {
        const nodeId = evt?.target?.id
        if (!nodeId) return
        const nodeData = currentDataRef.current?.nodes.find((n) => n.id === nodeId)
        if (nodeData) void expandNode(nodeData)
      })

      graph.on('canvas:click', () => setSelectedNode(null))

      graphRef.current = graph

      await graph.render()
      console.log('[Graph] render complete')
    } catch (e: any) {
      console.error('[Graph] render failed:', e)
      setError(`图谱渲染失败: ${e?.message || e}`)
    }
  }, [])


  const expandNode = useCallback(async (node: OntologyGraphNode) => {
    if (!kbId || !graphRef.current) return
    setExpanding(true)
    try {
      const res = await expandOntologyNeighbors(kbId, node.type, node.name)
      if (res.degraded) {
        message.warning(res.degraded_reason || t('domainGraph.expandFailed'))
        return
      }
      const cur = currentDataRef.current
      if (!cur) return

      const existIds = new Set(cur.nodes.map((n) => n.id))
      const newNodes = res.nodes.filter((n) => {
        if (existIds.has(n.id)) return false
        existIds.add(n.id)
        return true
      })
      const existEdgeKeys = new Set(cur.edges.map(edgeKey))
      const newEdges = res.edges.filter((e) => {
        const k = edgeKey(e)
        if (existEdgeKeys.has(k)) return false
        existEdgeKeys.add(k)
        return true
      })
      if (newNodes.length === 0 && newEdges.length === 0) {
        message.info(t('domainGraph.noMoreNeighbors'))
        return
      }
      cur.nodes.push(...newNodes)
      cur.edges.push(...newEdges)
      const showNodeLabels = cur.nodes.length <= NODE_LABEL_LIMIT
      const showEdgeLabels = cur.edges.length <= EDGE_LABEL_LIMIT
      if (newNodes.length) graphRef.current.addNodeData(newNodes.map((n) => mapNode(n, showNodeLabels)))
      if (newEdges.length) graphRef.current.addEdgeData(newEdges.map((e) => mapEdge(e, showEdgeLabels)))

      await graphRef.current.render()
      setMeta((m) => (m ? { ...m, returned_nodes: cur.nodes.length, returned_edges: cur.edges.length } : m))
      message.success(`展开 ${newNodes.length} 个邻居、${newEdges.length} 条关系`)
    } catch (e: any) {
      message.error(e?.message || t('domainGraph.expandFailed'))
    } finally {
      setExpanding(false)
    }
  }, [kbId])


  useEffect(() => {
    loadData()
    return () => {
      if (graphRef.current) {
        graphRef.current.destroy()
        graphRef.current = null
      }
    }
  }, [loadData])


  const handleZoomIn = () => graphRef.current?.zoomTo(graphRef.current.getZoom() * 1.3)
  const handleZoomOut = () => graphRef.current?.zoomTo(graphRef.current.getZoom() * 0.7)
  const handleFitView = () => graphRef.current?.fitView()


  const handleSearch = () => {
    if (!searchKeyword.trim() || !currentDataRef.current) return
    const kw = searchKeyword.toLowerCase()
    const found = currentDataRef.current.nodes.find(
      (n) => n.name.toLowerCase().includes(kw) || n.id.toLowerCase().includes(kw),
    )
    if (found && graphRef.current) {
      graphRef.current.focusElement(found.id, { duration: 500 })
    } else {
      message.info(t('domainGraph.noMatchingNode'))
    }
  }

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
                <a onClick={() => navigate(`/domain-knowledge/${kbId}`)} style={{ color: '#64748b' }}>
                  {t('domainKnowledge.detail')}
                </a>
              ),
            },
            { title: <span style={{ color: '#0b2b5c', fontWeight: 500 }}>{t('knowledgeSearch.knowledgeGraph')}</span> },
          ]}
        />
      </div>

      { }
      <a
        onClick={() => navigate(`/domain-knowledge/${kbId}`)}
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 6,
          marginBottom: 16, fontSize: 14, color: '#64748b', cursor: 'pointer',
        }}
      >
        <ArrowLeftOutlined /> {t('domainKnowledge.list')}
      </a>

      { }
      <Card
        style={{
          borderRadius: 14, marginBottom: 20,
          border: '1px solid #eef2f6', boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
        }}
        styles={{ body: { padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 16 } }}
      >
        <div
          style={{
            width: 42, height: 42, borderRadius: 10,
            background: 'linear-gradient(135deg,#8b5cf6,#7c3aed)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 18, color: '#fff',
          }}
        >
          🔗
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#0b2b5c' }}>{t('knowledgeSearch.knowledgeGraph')}</div>
          <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 2 }}>
            {stats
              ? `${stats.knowledge_base_name || ''} · 共 ${stats.ontology_instance_count} 个实体 · ${stats.ontology_relation_count} 条关系`
              : t('domainGraph.loading')}
          </div>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} size="small" onClick={loadData}>
            刷新
          </Button>
          <Button icon={<ExpandAltOutlined />} size="small" onClick={handleFitView}>
            适应视图
          </Button>
        </Space>
      </Card>

      { }
      <div style={{ display: 'flex', gap: 20, minHeight: 600 }}>
        { }
        <div
          style={{
            flex: 1, background: '#fff', borderRadius: 14,
            border: '1px solid #eef2f6', boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
            padding: 20, display: 'flex', flexDirection: 'column',
          }}
        >
          { }
          <div
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              marginBottom: 12, flexWrap: 'wrap', gap: 8,
            }}
          >
            <Space wrap>
              <Input.Search
                placeholder="搜索实体…"
                size="small"
                style={{ width: 180 }}
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                onSearch={handleSearch}
                enterButton={<SearchOutlined />}
              />
              <Select
                mode="multiple"
                allowClear
                size="small"
                placeholder="按实体类型筛选"
                style={{ minWidth: 200, maxWidth: 320 }}
                value={selectedTypes}
                onChange={(vals) => setSelectedTypes(vals)}
                maxTagCount="responsive"
                suffixIcon={<FilterOutlined />}
                options={typeDistribution.map((t) => ({
                  label: `${t.type} (${t.count})`,
                  value: t.type,
                }))}
              />
            </Space>
            <Space>
              <Button size="small" icon={<ZoomInOutlined />} style={{ borderRadius: 8 }} onClick={handleZoomIn} />
              <Button size="small" icon={<ZoomOutOutlined />} style={{ borderRadius: 8 }} onClick={handleZoomOut} />
              <Button size="small" icon={<ExpandAltOutlined />} style={{ borderRadius: 8 }} onClick={handleFitView} />
              <Button size="small" icon={<ReloadOutlined />} style={{ borderRadius: 8 }} onClick={loadData} />
            </Space>
          </div>

          { }
          {meta && (
            <div
              style={{
                display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap',
                marginBottom: 10, fontSize: 12, color: '#94a3b8',
              }}
            >
              <span>
                已显示 <b style={{ color: '#475569' }}>{meta.returned_nodes}</b> / 共{' '}
                <b style={{ color: '#475569' }}>{meta.total_nodes}</b> {t('ontology.entity')}
              </span>
              <span>
                {t('ontology.relation')} <b style={{ color: '#475569' }}>{meta.returned_edges}</b> / {meta.total_relations}
              </span>
              {meta.truncated && (
                <Tooltip title={`图谱较大，仅按连接度展示前 ${NODE_LIMIT} 个节点。可用类型筛选缩小范围，或双击节点展开邻居。`}>
                  <Tag color="orange" style={{ margin: 0, cursor: 'help' }}>
                    已截断显示
                  </Tag>
                </Tooltip>
              )}
              <span style={{ marginLeft: 'auto', color: '#cbd5e1' }}>
                <NodeExpandOutlined /> 双击节点展开邻居
              </span>
              {expanding && <Spin size="small" />}
            </div>
          )}

          { }
          <div
            style={{
              flex: 1, borderRadius: 10, border: '1px solid #eef2f6',
              background: 'radial-gradient(ellipse at center, #f8fafc 0%, #f0f4f8 100%)',
              overflow: 'hidden', position: 'relative', minHeight: 480,
            }}
          >
            { }
            <div
              ref={containerRef}
              style={{ position: 'absolute', inset: 0 }}
            />
            { }
            {loading && (
              <div style={{
                position: 'absolute', inset: 0, display: 'flex',
                alignItems: 'center', justifyContent: 'center', background: 'rgba(255,255,255,0.6)', zIndex: 10,
              }}>
                <Spin tip={t('domainGraph.loading')}>
                  <div style={{ padding: 16 }} />
                </Spin>
              </div>
            )}
            {error && !loading && (
              <div style={{
                position: 'absolute', inset: 0, display: 'flex',
                alignItems: 'center', justifyContent: 'center', zIndex: 10,
              }}>
                <Empty description={error}>
                  <Button type="primary" onClick={loadData}>{t('domainKnowledge.retry')}</Button>
                </Empty>
              </div>
            )}
            {!loading && !error && degraded && (
              <div style={{
                position: 'absolute', inset: 0, display: 'flex',
                alignItems: 'center', justifyContent: 'center', zIndex: 10,
              }}>
                <Empty description={degradedReason || t('domainGraph.unavailable')}>
                  <Button type="primary" onClick={loadData}>{t('domainKnowledge.retry')}</Button>
                </Empty>
              </div>
            )}
            {!loading && !error && !degraded && currentDataRef.current?.nodes.length === 0 && (
              <div style={{
                position: 'absolute', inset: 0, display: 'flex',
                alignItems: 'center', justifyContent: 'center', zIndex: 10,
              }}>
                <Empty description="暂无图谱数据，请先上传文档并完成解析编译" />
              </div>
            )}
          </div>

          { }
          {selectedNode && (
            <div
              style={{
                marginTop: 12, background: '#fff', borderRadius: 14,
                border: '1px solid #eef2f6', boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
                padding: 20,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                <div
                  style={{
                    width: 36, height: 36, borderRadius: 8,
                    background: selectedNode.typeColor || '#8b5cf6',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 16, color: '#fff',
                  }}
                >
                  {selectedNode.name?.charAt(0) || '?'}
                </div>
                <span style={{ fontSize: 15, fontWeight: 600, color: '#0b2b5c' }}>
                  {selectedNode.name}
                </span>
                <Tag color={selectedNode.typeColor} style={{ margin: 0 }}>
                  {selectedNode.type}
                </Tag>
                <Button
                  size="small"
                  type="primary"
                  ghost
                  icon={<NodeExpandOutlined />}
                  loading={expanding}
                  style={{ marginLeft: 'auto' }}
                  onClick={() => expandNode(selectedNode)}
                >
                  展开邻居
                </Button>
                <Button
                  size="small"
                  type="text"
                  onClick={() => setSelectedNode(null)}
                >
                  ✕
                </Button>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
                <div>
                  <span style={{ fontSize: 11, color: '#94a3b8' }}>{t('ontology.entity')}</span>
                  <div style={{ fontSize: 13, color: '#475569', fontWeight: 500 }}>
                    {selectedNode.type}
                  </div>
                </div>
                <div>
                  <span style={{ fontSize: 11, color: '#94a3b8' }}>别名</span>
                  <div style={{ fontSize: 13, color: '#475569', fontWeight: 500 }}>
                    {(selectedNode.aliases || []).length > 0
                      ? selectedNode.aliases.join(', ')
                      : '-'}
                  </div>
                </div>
                <div>
                  <span style={{ fontSize: 11, color: '#94a3b8' }}>{t('domainKnowledge.relationCount')}</span>
                  <div style={{ fontSize: 13, color: '#475569', fontWeight: 500 }}>
                    {selectedNode.connectedEdges?.length || 0}
                  </div>
                </div>
                <div>
                  <span style={{ fontSize: 11, color: '#94a3b8' }}>置信度</span>
                  <div style={{ fontSize: 13, color: '#475569', fontWeight: 500 }}>
                    {selectedNode.confidence != null
                      ? `${(selectedNode.confidence * 100).toFixed(0)}%`
                      : '-'}
                  </div>
                </div>
                <div>
                  <span style={{ fontSize: 11, color: '#94a3b8' }}>属性数</span>
                  <div style={{ fontSize: 13, color: '#475569', fontWeight: 500 }}>
                    {selectedNode.attributes
                      ? Object.keys(selectedNode.attributes).length
                      : 0}
                  </div>
                </div>
                <div>
                  <span style={{ fontSize: 11, color: '#94a3b8' }}>来源文档</span>
                  <div style={{ fontSize: 13, color: '#475569', fontWeight: 500 }}>
                    {(selectedNode.doc_ids || []).length}
                  </div>
                </div>
              </div>
              {selectedNode.description && (
                <div style={{ marginTop: 8 }}>
                  <span style={{ fontSize: 11, color: '#94a3b8' }}>{t('domainService.description')}</span>
                  <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>
                    {selectedNode.description}
                  </div>
                </div>
              )}
              {selectedNode.connectedEdges?.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <span style={{ fontSize: 11, color: '#94a3b8' }}>{t('ontology.relation')}</span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 4 }}>
                    {selectedNode.connectedEdges.map((e: any, i: number) => (
                      <Tag key={i} style={{ fontSize: 11 }}>
                        {`${e.source_type}:${e.source}` === selectedNode.id ? '→' : '←'} {e.label} {`${e.source_type}:${e.source}` === selectedNode.id ? e.target : e.source}
                      </Tag>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        { }
        <Card
          style={{
            width: 220, flexShrink: 0, borderRadius: 14,
            border: '1px solid #eef2f6', boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
          }}
          styles={{ body: { padding: 20 } }}
        >
          <h4
            style={{
              fontSize: 14, fontWeight: 600, color: '#0b2b5c',
              marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8,
            }}
          >
            <InfoCircleOutlined style={{ color: '#3b82f6' }} /> 图谱统计
          </h4>
          {stats ? (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '4px 0', color: '#64748b' }}>
                <span>{t('domainKnowledge.entityCount')}</span>
                <span style={{ fontWeight: 600, color: '#0b2b5c' }}>{stats.ontology_instance_count}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '4px 0', color: '#64748b' }}>
                <span>{t('domainKnowledge.relationCount')}</span>
                <span style={{ fontWeight: 600, color: '#0b2b5c' }}>{stats.ontology_relation_count}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '4px 0', color: '#64748b' }}>
                <span>来源文档</span>
                <span style={{ fontWeight: 600, color: '#0b2b5c' }}>{stats.source_file_count}</span>
              </div>
            </>
          ) : (
            <div style={{ fontSize: 12, color: '#94a3b8', textAlign: 'center', padding: 20 }}>
              {t('domainGraph.loading')}
            </div>
          )}
          <div style={{ height: 1, background: '#eef2f6', margin: '12px 0' }} />
          <h4 style={{ fontSize: 13, fontWeight: 600, color: '#0b2b5c', marginBottom: 10 }}>
            {t('ontology.entity')}
            <span style={{ fontSize: 11, fontWeight: 400, color: '#cbd5e1', marginLeft: 6 }}>点击筛选</span>
          </h4>
          {typeDistribution.map((item) => {
            const active = selectedTypes.includes(item.type)
            return (
              <div
                key={item.type}
                onClick={() =>
                  setSelectedTypes((prev) =>
                    prev.includes(item.type)
                      ? prev.filter((t) => t !== item.type)
                      : [...prev, item.type],
                  )
                }
                style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '6px 8px', borderBottom: '1px solid #f1f5f9',
                  fontSize: 13, color: active ? '#0b2b5c' : '#475569',
                  cursor: 'pointer', borderRadius: 6,
                  background: active ? '#eff6ff' : 'transparent',
                  fontWeight: active ? 600 : 400,
                }}
              >
                <span
                  style={{
                    width: 12, height: 12, borderRadius: '50%',
                    background: getTypeColor(item.type), flexShrink: 0,
                    outline: active ? '2px solid #3b82f6' : 'none', outlineOffset: 1,
                  }}
                />
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {item.type}
                </span>
                <span style={{ fontSize: 12, color: '#94a3b8' }}>{item.count}</span>
              </div>
            )
          })}
          {selectedTypes.length > 0 && (
            <Button
              type="link"
              size="small"
              style={{ padding: 0, marginTop: 6, fontSize: 12 }}
              onClick={() => setSelectedTypes([])}
            >
              清除筛选（{selectedTypes.length}）
            </Button>
          )}
          {typeDistribution.length === 0 && !loading && (
            <div style={{ fontSize: 12, color: '#94a3b8', textAlign: 'center', padding: 8 }}>
              暂无实体
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
