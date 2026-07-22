import React from 'react'
import { Button, Card, Select, Tag, Input, Space } from 'antd'
import { SaveOutlined, ReloadOutlined, ThunderboltOutlined, RocketOutlined, NodeIndexOutlined, SearchOutlined } from '@ant-design/icons'

const engines = [
  {
    key: 'parser', title: '解析引擎', icon: <ThunderboltOutlined />, status: '运行中',
    fields: [
      { label: '引擎版本', value: 'v3.2.1 (最新)', type: 'select', options: ['v3.2.1 (最新)', 'v3.1.0'] },
      { label: '并发线程数', value: '8', type: 'input' },
      { label: '内存限制', value: '8 GB', type: 'select', options: ['4 GB', '8 GB', '16 GB'] },
      { label: '超时时间', value: '300 秒', type: 'input' },
    ],
  },
  {
    key: 'compile', title: '编译引擎', icon: <RocketOutlined />, status: '运行中',
    fields: [
      { label: '引擎版本', value: 'v2.5.0 (最新)', type: 'select', options: ['v2.5.0 (最新)', 'v2.4.2'] },
      { label: '编译批次大小', value: '1000 条/批', type: 'input' },
      { label: '最大实体数', value: '50000', type: 'input' },
      { label: '关系深度', value: '3 层', type: 'select', options: ['1 层', '3 层', '5 层', '10 层'] },
    ],
  },
  {
    key: 'vector', title: '向量化引擎', icon: <NodeIndexOutlined />, status: '运行中',
    fields: [
      { label: '引擎版本', value: 'v1.8.3', type: 'select', options: ['v1.8.3'] },
      { label: '向量维度', value: '768', type: 'select', options: ['256', '768', '1024'] },
      { label: '批处理大小', value: '64 条/批', type: 'input' },
      { label: 'GPU 加速', value: '启用', type: 'select', options: ['启用', '禁用'] },
    ],
  },
  {
    key: 'search', title: '检索引擎', icon: <SearchOutlined />, status: '运行中',
    fields: [
      { label: '引擎版本', value: 'v2.1.0', type: 'select', options: ['v2.1.0'] },
      { label: '检索算法', value: 'HNSW', type: 'select', options: ['HNSW', 'IVF', 'FLAT'] },
      { label: 'Top-K 默认值', value: '10', type: 'input' },
      { label: '缓存策略', value: 'LRU', type: 'select', options: ['LRU', 'LFU', 'TTL'] },
    ],
  },
]

export default function DomainKnowledgeEngine() {
  return (
    <div>
      <div className="yx-page-title">
        <h1>引擎配置</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 14 }}>管理各引擎的参数与运行配置</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 20 }}>
        {engines.map((engine) => (
          <Card key={engine.key} style={{ borderRadius: 12, border: '1px solid #e2e8f0' }} bodyStyle={{ padding: 24 }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
              {engine.icon} {engine.title}
              <Tag color="success" style={{ marginLeft: 'auto', fontSize: 11 }}>{engine.status}</Tag>
            </h3>
            {engine.fields.map((f) => (
              <div className="yx-form-row" key={f.label}>
                <label>{f.label}</label>
                {f.type === 'select' ? (
                  <Select defaultValue={f.value} style={{ width: '100%' }} options={(f.options!).map((o) => ({ value: o, label: o }))} />
                ) : (
                  <Input defaultValue={f.value} />
                )}
              </div>
            ))}
          </Card>
        ))}
      </div>

      <div style={{ marginTop: 20, display: 'flex', gap: 12 }}>
        <Button type="primary" icon={<SaveOutlined />}>保存配置</Button>
        <Button icon={<ReloadOutlined />}>重启引擎</Button>
      </div>
    </div>
  )
}
