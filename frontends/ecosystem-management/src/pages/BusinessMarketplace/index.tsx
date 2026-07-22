import React from 'react'
import { Tag } from 'antd'
import { ShopOutlined, BlockOutlined, InboxOutlined, CodepenOutlined, NodeIndexOutlined } from '@ant-design/icons'

const previewCards = [
  { icon: <BlockOutlined />, title: '领域模板', desc: '各行业领域知识管理模板' },
  { icon: <InboxOutlined />, title: '知识包', desc: '预构建的行业知识库包' },
  { icon: <CodepenOutlined />, title: '预训练模型', desc: '领域专用预训练 AI 模型' },
  { icon: <NodeIndexOutlined />, title: '行业解决方案', desc: '端到端的行业知识管理方案' },
]

export default function BusinessMarketplace() {
  return (
    <div>
      <div style={{ textAlign: 'center', padding: '60px 20px' }}>
        <ShopOutlined style={{ fontSize: 72, color: '#3b82f6', opacity: 0.3, marginBottom: 20, display: 'block' }} />
        <h2 style={{ fontSize: 28, color: '#1e293b', margin: '0 0 8px' }}>业务领域商场</h2>
        <p style={{ color: '#94a3b8', fontSize: 15, margin: '0 0 40px' }}>领域模板、知识包、预训练模型与行业解决方案即将上线，敬请期待</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 20 }}>
          {previewCards.map((c, i) => (
            <div key={i} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 12, padding: 24, textAlign: 'center', opacity: 0.5 }}>
              <div style={{ fontSize: 36, color: '#94a3b8', marginBottom: 12 }}>{c.icon}</div>
              <h4 style={{ margin: '0 0 6px', fontSize: 15, color: '#64748b' }}>{c.title}</h4>
              <p style={{ margin: 0, fontSize: 13, color: '#94a3b8' }}>{c.desc}</p>
              <Tag style={{ marginTop: 10, background: '#f1f5f9', color: '#94a3b8', border: 'none' }}>即将上线</Tag>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
