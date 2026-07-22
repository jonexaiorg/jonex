import React from 'react'
import { Input, Tag, Button, message } from 'antd'
import { SearchOutlined, PlusOutlined, PlayCircleOutlined, SettingOutlined, BarChartOutlined, RobotOutlined, CodepenOutlined, BlockOutlined, SortDescendingOutlined } from '@ant-design/icons'

const models = [
  { name: 'GPT-4o', vendor: 'OpenAI', type: '对话模型', icon: <RobotOutlined />, color: '#10b981', latency: '1.2s', tokenLimit: '128K', calls: '12,458', successRate: '99.2%' },
  { name: 'Claude Opus 4', vendor: 'Anthropic', type: '对话模型', icon: <CodepenOutlined />, color: '#8b5cf6', latency: '1.8s', tokenLimit: '200K', calls: '8,234', successRate: '99.5%' },
  { name: 'text2vec-large', vendor: '本地部署', type: '向量模型', icon: <BlockOutlined />, color: '#3b82f6', latency: '0.3s', dims: '768', calls: '56,892', successRate: '100%' },
  { name: 'bge-reranker', vendor: '本地部署', type: '重排序模型', icon: <SortDescendingOutlined />, color: '#f59e0b', latency: '0.5s', batchSize: '64', calls: '23,456', successRate: '99.8%' },
]

export default function ModelAdapterPage() {
  return (
    <div>
      <div className="yx-page-title">
        <h1>模型适配</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 14 }}>管理接入的 AI 模型与适配器</p>
      </div>
      <div className="yx-toolbar" style={{ marginBottom: 20 }}>
        <Input prefix={<SearchOutlined />} placeholder="搜索模型..." style={{ width: 240 }} />
        <Button type="primary" icon={<PlusOutlined />}>添加模型</Button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 20 }}>
        {models.map((m, i) => (
          <div key={i} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 12, padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <div style={{ width: 48, height: 48, borderRadius: 12, background: m.color, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, color: '#fff' }}>{m.icon}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: 16 }}>{m.name}</div>
                <div style={{ fontSize: 12, color: '#94a3b8' }}>{m.vendor} · {m.type}</div>
              </div>
              <Tag color="success">已连接</Tag>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 16 }}>
              <div style={{ fontSize: 13 }}><span style={{ color: '#94a3b8' }}>延迟: </span>{m.latency}</div>
              <div style={{ fontSize: 13 }}><span style={{ color: '#94a3b8' }}>{m.tokenLimit ? 'Token 限额: ' : m.dims ? '向量维度: ' : '批量大小: '}</span>{m.tokenLimit || m.dims || m.batchSize}</div>
              <div style={{ fontSize: 13 }}><span style={{ color: '#94a3b8' }}>调用次数: </span>{m.calls}</div>
              <div style={{ fontSize: 13 }}><span style={{ color: '#94a3b8' }}>成功率: </span>{m.successRate}</div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <Button type="primary" size="small" icon={<PlayCircleOutlined />} onClick={() => message.success('测试成功')}>测试</Button>
              <Button size="small" icon={<SettingOutlined />}>配置</Button>
              <Button size="small" icon={<BarChartOutlined />}>监控</Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
