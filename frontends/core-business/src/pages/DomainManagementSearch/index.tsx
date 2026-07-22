import React, { useState } from 'react'
import { Input, Button, Card, Tag, Space } from 'antd'
import { SearchOutlined, StarFilled } from '@ant-design/icons'

const resultList = [
  { title: '商业银行信用风险评估模型研究', source: '金融风控 · 金融产品知识库', date: '2026-03-15', relevance: 96, snippet: '本文探讨了基于机器学习的商业银行信用风险评估方法，对比了逻辑回归、随机森林和XGBoost等模型在信用评分中的表现...' },
  { title: '保险产品定价与风险控制的白皮书', source: '金融风控 · 金融产品知识库', date: '2026-02-20', relevance: 92, snippet: '本白皮书系统分析了保险产品定价中的风险因素，提出了基于大数据的动态定价策略和风险控制框架...' },
  { title: '医疗欺诈检测与风险预警系统设计', source: '医疗保险 · 医学文献知识库', date: '2026-04-10', relevance: 88, snippet: '针对医疗保险领域的欺诈行为，提出了一种基于知识图谱的异常检测方法，实现欺诈模式的智能识别和实时预警...' },
  { title: '金融监管政策解读与合规指南（2026年版）', source: '法律法规 · 法律法规知识库', date: '2026-01-08', relevance: 85, snippet: '全面解读2026年最新金融监管政策，包括资本充足率、流动性覆盖率等关键指标的要求变化及合规操作指南...' },
  { title: '供应链金融风险评估与控制方案', source: '金融风控 · 金融产品知识库', date: '2026-05-05', relevance: 82, snippet: '针对供应链金融中的核心企业信用风险、贸易真实性风险等关键问题，提出了多维度的风险评估与控制方案...' },
]

const domainChips = ['全部', '金融风控', '医疗保险', '智能制造', '教育培训', '法律法规']

export default function DomainManagementSearch() {
  const [query, setQuery] = useState('金融风险评估')
  const [activeChip, setActiveChip] = useState('全部')

  return (
    <div>
      <div className="yx-page-title">
        <h1>知识检索</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 14 }}>跨知识库智能检索</p>
      </div>

      <Card style={{ borderRadius: 16, marginBottom: 24, textAlign: 'center' }} bodyStyle={{ padding: 32 }}>
        <div style={{ fontSize: 15, color: '#64748b' }}>输入关键字，从所有知识库中检索相关内容</div>
        <div style={{ display: 'flex', maxWidth: 700, margin: '16px auto 0', gap: 8 }}>
          <Input
            value={query} onChange={(e) => setQuery(e.target.value)}
            placeholder="请输入搜索关键词..." style={{ flex: 1, padding: '14px 20px', border: '2px solid #e2e8f0', borderRadius: 12, fontSize: 16 }}
            onPressEnter={() => {}}
          />
          <Button type="primary" style={{ padding: '14px 32px', borderRadius: 12, fontSize: 15, height: 'auto' }} icon={<SearchOutlined />}>检索</Button>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center', marginTop: 16 }}>
          {domainChips.map((c) => (
            <Tag
              key={c}
              style={{ padding: '6px 16px', borderRadius: 20, fontSize: 13, cursor: 'pointer', border: `1px solid ${activeChip === c ? '#3b82f6' : '#d1d5db'}`, background: activeChip === c ? '#3b82f6' : '#fff', color: activeChip === c ? '#fff' : '#64748b' }}
              onClick={() => setActiveChip(c)}
            >{c}</Tag>
          ))}
        </div>
      </Card>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <span style={{ fontSize: 14, color: '#64748b' }}>找到约 <strong style={{ color: '#1e293b' }}>42</strong> 条结果（用时 0.35 秒）</span>
        <select style={{ padding: '6px 12px', border: '1px solid #d1d5db', borderRadius: 6, fontSize: 13 }}>
          <option>按相关度排序</option>
          <option>按时间排序</option>
        </select>
      </div>

      {resultList.map((r, i) => (
        <Card key={i} style={{ borderRadius: 12, marginBottom: 12, border: '1px solid #e2e8f0' }} bodyStyle={{ padding: 20 }} hoverable>
          <h3 style={{ margin: '0 0 8px', fontSize: 16 }}><a style={{ color: '#3b82f6' }}>{r.title}</a></h3>
          <p style={{ margin: '0 0 12px', color: '#64748b', fontSize: 14, lineHeight: 1.6 }}>{r.snippet}</p>
          <div style={{ display: 'flex', gap: 16, fontSize: 12, color: '#94a3b8', alignItems: 'center' }}>
            <Tag style={{ background: '#f1f5f9', border: 'none' }}>{r.source}</Tag>
            <span>{r.date}</span>
            <span style={{ color: '#22c55e', fontWeight: 600 }}><StarFilled style={{ fontSize: 10 }} /> 相关度 {r.relevance}%</span>
          </div>
        </Card>
      ))}

      <div className="yx-pagination" style={{ marginTop: 16 }}>
        <span className="yx-page-btn disabled">‹</span>
        <span className="yx-page-btn active">1</span>
        <span className="yx-page-btn">2</span>
        <span className="yx-page-btn">3</span>
        <span className="yx-page-btn">4</span>
        <span className="yx-page-btn">5</span>
        <span className="yx-page-btn">›</span>
        <span className="yx-page-info">共 42 条，1/9 页</span>
      </div>
    </div>
  )
}
