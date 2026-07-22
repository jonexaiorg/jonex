import React, { useState } from 'react'
import { Button, Card, Tag, Space } from 'antd'
import { ArrowLeftOutlined, DownloadOutlined, ExpandOutlined, PlusOutlined, MinusOutlined, ExpandAltOutlined, ReloadOutlined, FilterOutlined, SearchOutlined, InfoCircleOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'

interface GraphNode {
  id: string; label: string; icon: string; type: 'product' | 'org' | 'risk' | 'regulation' | 'root'
  x: number; y: number; size: 'lg' | 'sm' | 'xs'; badge?: number
}
interface GraphEdge { x1: number; y1: number; x2: number; y2: number; label?: string }

const nodes: GraphNode[] = [
  { id: 'product', label: '金融产品知识库', icon: '📊', type: 'root', x: 360, y: 0, size: 'lg' },
  { id: 'fund', label: '沪深300指数增强基金', icon: '💰', type: 'product', x: 200, y: 140, size: 'lg', badge: 12 },
  { id: 'bank', label: '中国工商银行', icon: '🏦', type: 'org', x: 360, y: 140, size: 'lg', badge: 9 },
  { id: 'fund2', label: '中证500指数基金', icon: '💰', type: 'product', x: 520, y: 140, size: 'lg', badge: 10 },
  { id: 'pingan', label: '中国平安', icon: '🏢', type: 'org', x: 80, y: 290, size: 'sm' },
  { id: 'volatility', label: '年化收益率波动率', icon: '📈', type: 'risk', x: 260, y: 320, size: 'sm' },
  { id: 'regulation', label: '资本管理办法', icon: '⚖️', type: 'regulation', x: 420, y: 330, size: 'sm' },
  { id: 'risk', label: '市场风险指标', icon: '⚠️', type: 'risk', x: 580, y: 320, size: 'sm' },
  { id: 'child1', label: '日添利理财', icon: '💰', type: 'product', x: 180, y: 420, size: 'xs' },
  { id: 'child2', label: '国泰基金', icon: '🏢', type: 'org', x: 340, y: 430, size: 'xs' },
  { id: 'child3', label: '流动性规定', icon: '⚖️', type: 'regulation', x: 500, y: 440, size: 'xs' },
  { id: 'child4', label: '稳健增益债基', icon: '💰', type: 'product', x: 540, y: 420, size: 'xs' },
  { id: 'child5', label: '中信证券', icon: '🏢', type: 'org', x: 80, y: 440, size: 'xs' },
  { id: 'child6', label: '信用风险', icon: '📊', type: 'risk', x: 620, y: 430, size: 'xs' },
]

const edges: GraphEdge[] = [
  { x1: 400, y1: 40, x2: 240, y2: 180, label: '发行' },
  { x1: 400, y1: 40, x2: 400, y2: 180, label: '管理' },
  { x1: 400, y1: 40, x2: 560, y2: 180, label: '托管' },
  { x1: 240, y1: 180, x2: 120, y2: 330, label: '投资' },
  { x1: 240, y1: 180, x2: 300, y2: 360, label: '控股' },
  { x1: 400, y1: 180, x2: 320, y2: 360, label: '关联' },
  { x1: 400, y1: 180, x2: 460, y2: 370 },
  { x1: 560, y1: 180, x2: 520, y2: 360 },
  { x1: 560, y1: 180, x2: 660, y2: 330, label: '约束' },
  { x1: 120, y1: 330, x2: 220, y2: 460 },
  { x1: 300, y1: 360, x2: 380, y2: 470, label: '合规' },
  { x1: 460, y1: 370, x2: 420, y2: 480 },
  { x1: 520, y1: 360, x2: 550, y2: 470 },
  { x1: 660, y1: 330, x2: 580, y2: 460 },
]

const detailData: Record<string, { icon: string; color: string; title: string; type: string; attr: string; rel: string; time: string; relations: { color: string; text: string }[] }> = {
  product: { icon: '📊', color: '#3b82f6', title: '金融产品知识库', type: '知识库', attr: '-', rel: '-', time: '-', relations: [] },
  fund: { icon: '💰', color: '#3b82f6', title: '沪深300指数增强基金', type: '金融产品', attr: '12', rel: '24', time: '2026-05-15', relations: [{ color: '#10b981', text: '发行机构：中国工商银行' }, { color: '#8b5cf6', text: '关联风险：年化收益率波动率' }, { color: '#f97316', text: '合规约束：商业银行资本管理办法' }] },
  fund2: { icon: '💰', color: '#3b82f6', title: '中证500指数基金', type: '金融产品', attr: '10', rel: '20', time: '2026-05-13', relations: [] },
  bank: { icon: '🏦', color: '#10b981', title: '中国工商银行', type: '金融机构', attr: '9', rel: '18', time: '2026-05-15', relations: [] },
  pingan: { icon: '🏢', color: '#10b981', title: '中国平安保险集团', type: '金融机构', attr: '8', rel: '15', time: '2026-05-12', relations: [] },
  volatility: { icon: '📈', color: '#8b5cf6', title: '年化收益率波动率', type: '风险指标', attr: '6', rel: '11', time: '2026-05-14', relations: [] },
  regulation: { icon: '⚖️', color: '#f97316', title: '《商业银行资本管理办法》', type: '监管条款', attr: '15', rel: '32', time: '2026-05-13', relations: [] },
  risk: { icon: '⚠️', color: '#8b5cf6', title: '市场风险指标', type: '风险指标', attr: '5', rel: '9', time: '2026-05-11', relations: [] },
}

const typeColors: Record<string, string> = {
  product: 'linear-gradient(135deg,#3b82f6,#1d4ed8)',
  org: 'linear-gradient(135deg,#10b981,#059669)',
  risk: 'linear-gradient(135deg,#8b5cf6,#7c3aed)',
  regulation: 'linear-gradient(135deg,#f97316,#ea580c)',
  root: 'linear-gradient(135deg,#64748b,#475569)',
}

const legendItems = [
  { color: '#3b82f6', label: '金融产品', count: '2,891' },
  { color: '#10b981', label: '金融机构', count: '1,934' },
  { color: '#8b5cf6', label: '风险指标', count: '1,245' },
  { color: '#f97316', label: '监管条款', count: '822' },
]

export default function DomainKnowledgeGraph() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const detail = selectedNode ? detailData[selectedNode] : null

  return (
    <div>
      <a onClick={() => navigate(`/domain-knowledge/${id}`)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginBottom: 16, fontSize: 14, color: '#64748b', cursor: 'pointer' }}>
        <ArrowLeftOutlined /> 返回知识库详情
      </a>

      <Card style={{ borderRadius: 14, marginBottom: 20, border: '1px solid #eef2f6', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }} bodyStyle={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{ width: 42, height: 42, borderRadius: 10, background: 'linear-gradient(135deg,#10b981,#059669)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: '#fff' }}>🔗</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#0b2b5c' }}>金融产品知识图谱</div>
          <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 2 }}>金融风控空间 · 共 6,892 个实体 · 24,156 条关系</div>
        </div>
        <Space>
          <Button type="primary" icon={<DownloadOutlined />} size="small">导出</Button>
          <Button icon={<ExpandOutlined />} size="small">全屏</Button>
        </Space>
      </Card>

      <div style={{ display: 'flex', gap: 20, minHeight: 600 }}>
        <div style={{ flex: 1, background: '#fff', borderRadius: 14, border: '1px solid #eef2f6', boxShadow: '0 1px 4px rgba(0,0,0,0.04)', padding: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
            <Space style={{ background: '#f1f5f9', borderRadius: 6, padding: 2 }}>
              {['图谱视图', '力导向', '层级视图'].map((v, i) => (
                <Button key={v} size="small" type={i === 0 ? 'default' : 'text'} style={{ borderRadius: 4, fontSize: 12, border: i === 0 ? '1px solid #e2e8f0' : 'none' }}>{v}</Button>
              ))}
            </Space>
            <Space>
              <Button size="small" icon={<PlusOutlined />} style={{ borderRadius: 8 }} />
              <Button size="small" icon={<MinusOutlined />} style={{ borderRadius: 8 }} />
              <Button size="small" icon={<ExpandAltOutlined />} style={{ borderRadius: 8 }} />
              <Button size="small" icon={<ReloadOutlined />} style={{ borderRadius: 8 }} />
            </Space>
          </div>

          <div style={{ position: 'relative', width: '100%', height: 520, background: 'radial-gradient(ellipse at center, #f8fafc 0%, #f0f4f8 100%)', borderRadius: 10, border: '1px solid #eef2f6', overflow: 'hidden' }} onClick={() => setSelectedNode(null)}>
            <svg style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none', zIndex: 1 }}>
              {edges.map((e, i) => (
                <g key={i}>
                  <line x1={e.x1} y1={e.y1 + 40} x2={e.x2} y2={e.y2 + 40} stroke="#d1d5db" strokeWidth={1.5} />
                  {e.label && <text x={(e.x1 + e.x2) / 2} y={(e.y1 + e.y2) / 2 + 30} textAnchor="middle" fontSize={9} fill="#94a3b8">{e.label}</text>}
                </g>
              ))}
            </svg>

            {nodes.map((n) => {
              const w = n.size === 'lg' ? 80 : n.size === 'sm' ? 56 : 40
              return (
                <div
                  key={n.id}
                  onClick={(e) => { e.stopPropagation(); setSelectedNode(n.id) }}
                  style={{
                    position: 'absolute', left: n.x - w / 2, top: n.y,
                    width: w, height: w, borderRadius: '50%', cursor: 'pointer',
                    background: typeColors[n.type], display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: n.size === 'xs' ? 11 : n.size === 'sm' ? 14 : 18, color: '#fff',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.08)', zIndex: 2, transition: 'all 0.3s',
                  }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.transform = 'scale(1.15)'; (e.currentTarget as HTMLElement).style.zIndex = '10'; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.transform = 'scale(1)'; (e.currentTarget as HTMLElement).style.zIndex = '2'; }}
                >
                  {n.icon}
                  {n.badge && <span style={{ position: 'absolute', top: -4, right: -4, width: 18, height: 18, borderRadius: '50%', background: '#fff', border: '2px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 8, color: '#64748b', fontWeight: 600 }}>{n.badge}</span>}
                  {n.size !== 'xs' && (
                    <span style={{
                      position: 'absolute', top: '100%', marginTop: 6, fontSize: n.size === 'sm' ? 10 : 11,
                      color: '#475569', whiteSpace: 'nowrap', fontWeight: 500,
                      background: 'rgba(255,255,255,0.9)', padding: '2px 8px', borderRadius: 4, border: '1px solid #eef2f6',
                    }}>{n.label}</span>
                  )}
                </div>
              )
            })}

            {detail && (
              <div style={{ position: 'absolute', bottom: 16, left: 16, right: 16, background: '#fff', borderRadius: 14, border: '1px solid #eef2f6', boxShadow: '0 1px 4px rgba(0,0,0,0.04)', padding: 20, zIndex: 10 }} onClick={(e) => e.stopPropagation()}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                  <div style={{ width: 36, height: 36, borderRadius: 8, background: detail.color, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, color: '#fff' }}>{detail.icon}</div>
                  <span style={{ fontSize: 15, fontWeight: 600, color: '#0b2b5c' }}>{detail.title}</span>
                  <Button size="small" type="text" style={{ marginLeft: 'auto' }} onClick={() => setSelectedNode(null)}>✕</Button>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                  <div><span style={{ fontSize: 11, color: '#94a3b8' }}>实体类型</span><div style={{ fontSize: 13, color: '#475569', fontWeight: 500 }}>{detail.type}</div></div>
                  <div><span style={{ fontSize: 11, color: '#94a3b8' }}>属性数</span><div style={{ fontSize: 13, color: '#475569', fontWeight: 500 }}>{detail.attr}</div></div>
                  <div><span style={{ fontSize: 11, color: '#94a3b8' }}>关系数</span><div style={{ fontSize: 13, color: '#475569', fontWeight: 500 }}>{detail.rel}</div></div>
                  <div><span style={{ fontSize: 11, color: '#94a3b8' }}>创建时间</span><div style={{ fontSize: 13, color: '#475569', fontWeight: 500 }}>{detail.time}</div></div>
                </div>
                {detail.relations.length > 0 && (
                  <div style={{ marginTop: 12 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: '#0b2b5c', marginBottom: 6 }}>关联关系</div>
                    {detail.relations.map((r, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 8px', borderRadius: 6, background: '#f8fafc', marginBottom: 4, fontSize: 12, color: '#64748b' }}>
                        <span style={{ background: r.color, width: 6, height: 6, borderRadius: '50%', display: 'inline-block' }} /> {r.text}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <Card style={{ width: 220, flexShrink: 0, borderRadius: 14, border: '1px solid #eef2f6', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }} bodyStyle={{ padding: 20 }}>
          <h4 style={{ fontSize: 14, fontWeight: 600, color: '#0b2b5c', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}><InfoCircleOutlined style={{ color: '#3b82f6' }} /> 图谱统计</h4>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '4px 0', color: '#64748b' }}><span>实体总数</span><span style={{ fontWeight: 600, color: '#0b2b5c' }}>6,892</span></div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '4px 0', color: '#64748b' }}><span>关系总数</span><span style={{ fontWeight: 600, color: '#0b2b5c' }}>24,156</span></div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '4px 0', color: '#64748b' }}><span>关系类型</span><span style={{ fontWeight: 600, color: '#0b2b5c' }}>18</span></div>
          <div style={{ height: 1, background: '#eef2f6', margin: '12px 0' }} />
          <h4 style={{ fontSize: 13, fontWeight: 600, color: '#0b2b5c', marginBottom: 10 }}>图例</h4>
          {legendItems.map((l) => (
            <div key={l.label} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 0', borderBottom: '1px solid #f1f5f9', fontSize: 13, color: '#475569' }}>
              <span style={{ width: 12, height: 12, borderRadius: '50%', background: l.color, flexShrink: 0 }} />
              {l.label}
              <span style={{ marginLeft: 'auto', fontSize: 12, color: '#94a3b8' }}>{l.count}</span>
            </div>
          ))}
          <div style={{ height: 1, background: '#eef2f6', margin: '12px 0' }} />
          <Space style={{ width: '100%' }}>
            <Button size="small" icon={<FilterOutlined />} block>筛选</Button>
            <Button size="small" icon={<SearchOutlined />} block>查找</Button>
          </Space>
        </Card>
      </div>
    </div>
  )
}
