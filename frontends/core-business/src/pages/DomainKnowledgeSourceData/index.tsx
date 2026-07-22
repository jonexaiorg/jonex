import React, { useState } from 'react'
import { Button, Card, Select, Space } from 'antd'
import { DownloadOutlined, SyncOutlined } from '@ant-design/icons'

const stats = [
  { label: '总文档数', value: '1,284' },
  { label: '数据总量', value: '3.2 GB' },
  { label: '最近 7 天新增', value: '256' },
  { label: '解析成功率', value: '99.8%' },
]

const jsonPreview = `{
  "knowledge_base": "金融产品知识库",
  "last_sync": "2026-05-21T14:30:00+08:00",
  "total_docs": 1284,
  "status": "synced",
  "documents": [
    {
      "id": "DOC-001",
      "title": "2026年Q1基金产品报告",
      "type": "PDF",
      "size": 2457600,
      "pages": 32,
      "parsed": true,
      "created_at": "2026-01-15T09:30:00Z"
    },
    {
      "id": "DOC-002",
      "title": "理财产品风险评估白皮书",
      "type": "DOCX",
      "size": 1048576,
      "pages": 18,
      "parsed": true,
      "created_at": "2026-02-20T14:00:00Z"
    }
  ],
  "categories": [
    { "name": "基金产品", "count": 452 },
    { "name": "理财保险", "count": 328 },
    { "name": "信贷业务", "count": 504 }
  ]
}`

const kbs = ['金融产品知识库', '医学文献知识库', '设备故障知识库']

const tabs = ['原始数据', '结构化数据', '元数据']

export default function DomainKnowledgeSourceData() {
  const [activeTab, setActiveTab] = useState('原始数据')
  const [selectedKb, setSelectedKb] = useState(kbs[0])

  return (
    <div>
      <div className="yx-page-title">
        <h1>源数据查看</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 14 }}>查看各知识库的原始数据内容</p>
      </div>

      <Card style={{ borderRadius: 14, marginBottom: 20, border: '1px solid #eef2f6' }} bodyStyle={{ padding: '0 20px' }}>
        <div style={{ display: 'flex', borderBottom: '2px solid #e2e8f0' }}>
          {tabs.map((t) => (
            <div
              key={t}
              onClick={() => setActiveTab(t)}
              style={{
                padding: '10px 24px', cursor: 'pointer', fontSize: 14, color: activeTab === t ? '#3b82f6' : '#64748b',
                borderBottom: activeTab === t ? '2px solid #3b82f6' : '2px solid transparent',
                marginBottom: -2, fontWeight: activeTab === t ? 600 : 400, transition: 'all 0.2s',
              }}
            >{t}</div>
          ))}
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center' }}>
            <Select value={selectedKb} onChange={setSelectedKb} style={{ width: 180 }} options={kbs.map((k) => ({ value: k, label: k }))} />
          </div>
        </div>
      </Card>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16, marginBottom: 20 }}>
        {stats.map((s) => (
          <Card key={s.label} style={{ borderRadius: 8, textAlign: 'center', border: '1px solid #e2e8f0' }} bodyStyle={{ padding: 16 }}>
            <div style={{ fontSize: 24, fontWeight: 700, color: '#3b82f6' }}>{s.value}</div>
            <div style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>{s.label}</div>
          </Card>
        ))}
      </div>

      <Card style={{ borderRadius: 14, overflow: 'hidden', border: '1px solid #eef2f6' }} bodyStyle={{ padding: 0 }}>
        <div style={{ padding: '12px 20px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: 600, fontSize: 14, color: '#0b2b5c' }}>数据预览</span>
          <Space>
            <Button size="small" icon={<DownloadOutlined />}>导出</Button>
            <Button size="small" icon={<SyncOutlined />}>刷新</Button>
          </Space>
        </div>
        <div style={{ padding: 20 }}>
          <pre style={{
            background: '#1e293b', color: '#e2e8f0', borderRadius: 8, padding: 20,
            fontFamily: "'Consolas','Courier New',monospace", fontSize: 13, lineHeight: 1.7,
            overflowX: 'auto', whiteSpace: 'pre-wrap', margin: 0,
          }}>{jsonPreview}</pre>
        </div>
      </Card>
    </div>
  )
}
