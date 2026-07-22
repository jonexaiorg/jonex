import React from 'react'
import { Button, Tag } from 'antd'
import { ThunderboltOutlined, ShakeOutlined, CloudOutlined, CodepenOutlined, CarryOutOutlined, ExperimentOutlined } from '@ant-design/icons'

const adapters = [
  { name: 'ADP 适配器', desc: 'ADP 人力资源数据接入', icon: <ThunderboltOutlined />, color: '#3b82f6', status: '已连接', enabled: true },
  { name: 'HiAgent 适配器', desc: 'HiAgent 智能体平台集成', icon: <ShakeOutlined />, color: '#8b5cf6', status: '已连接', enabled: true },
  { name: 'AWS QuickSight', desc: 'AWS 数据分析平台集成', icon: <CloudOutlined />, color: '#94a3b8', status: '待接入', enabled: false },
  { name: 'Gemini 适配器', desc: 'Google Gemini 模型接入', icon: <CodepenOutlined />, color: '#94a3b8', status: '待接入', enabled: false },
  { name: 'WorkBuddy', desc: 'WorkBuddy 工作流集成', icon: <CarryOutOutlined />, color: '#94a3b8', status: '待接入', enabled: false },
  { name: 'Claw 适配器', desc: 'Claw 数据抓取平台集成', icon: <ExperimentOutlined />, color: '#94a3b8', status: '待接入', enabled: false },
]

export default function AdapterManagement() {
  return (
    <div>
      <div className="yx-page-title">
        <h1>适配器列表</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 14 }}>管理第三方生态适配器</p>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 20 }}>
        {adapters.map((a, i) => (
          <div
            key={i}
            style={{
              background: '#fff', border: '1px solid #e2e8f0', borderRadius: 12, padding: 24,
              textAlign: 'center', opacity: a.enabled ? 1 : 0.5, transition: 'box-shadow 0.2s',
            }}
          >
            {!a.enabled && <Tag style={{ marginBottom: 8, background: '#f1f5f9', color: '#94a3b8', border: 'none' }}>即将上线</Tag>}
            <div style={{ width: 64, height: 64, borderRadius: 16, background: a.color, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 28, color: '#fff', margin: '0 auto 16px' }}>{a.icon}</div>
            <h3 style={{ margin: '0 0 4px', fontSize: 16 }}>{a.name}</h3>
            <div style={{ fontSize: 13, color: '#64748b', marginBottom: 12 }}>{a.desc}</div>
            <Tag color={a.status === '已连接' ? 'success' : 'warning'} style={{ marginBottom: 12 }}>{a.status}</Tag>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
              {a.enabled ? (
                <>
                  <Button type="primary" size="small">配置</Button>
                  <Button size="small">监控</Button>
                </>
              ) : (
                <Button size="small" disabled>配置</Button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
