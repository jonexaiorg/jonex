import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Row, Col } from 'antd'
import { ApiOutlined, ShopOutlined } from '@ant-design/icons'

const actions = [
  { label: '适配器列表', desc: '生态适配器管理与配置', path: '/adapter-management', icon: <ApiOutlined />, color: '#3b82f6' },
  { label: '业务领域商场', desc: '领域模板、知识包、预训练模型', path: '/business-marketplace', icon: <ShopOutlined />, color: '#10b981', future: true },
]

export default function Home() {
  const navigate = useNavigate()
  return (
    <div>
      <div className="yx-page-title">
        <h1>生态管理</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 14 }}>生态适配器与业务商场管理</p>
      </div>
      <Row gutter={[16, 16]}>
        {actions.map((a) => (
          <Col xs={24} sm={12} key={a.label}>
            <a onClick={() => navigate(a.path)} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '18px 20px', background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', textDecoration: 'none', cursor: 'pointer', transition: 'all 0.2s', opacity: a.future ? 0.6 : 1 }}>
              <span style={{ fontSize: 22, color: a.color, background: `${a.color}15`, width: 44, height: 44, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{a.icon}</span>
              <div><div style={{ fontSize: 14, fontWeight: 500, color: '#1e293b' }}>{a.label}{a.future ? ' (未来)' : ''}</div><div style={{ fontSize: 12, color: '#94a3b8' }}>{a.desc}</div></div>
            </a>
          </Col>
        ))}
      </Row>
    </div>
  )
}
