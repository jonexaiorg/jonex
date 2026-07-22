import React from 'react'
import { Button, Card, Table, Tag, Input, Space } from 'antd'
import { ArrowLeftOutlined, CloudOutlined, SyncOutlined, SettingOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'

const dsInfo = {
  name: '金融产品API', type: 'API同步', space: '金融风控空间', url: 'https://api.finance.internal/products', docs: 856,
}

const syncStats = [
  { label: '总文档数', value: '1,284', color: '#10b981' },
  { label: '同步状态', value: '运行中', color: '#10b981' },
  { label: '同步频率', value: '每日 02:00', color: '#3b82f6' },
  { label: '上次同步时间', value: '2026-05-21 02:00' },
]

const docList = [
  { name: '2026年5月信贷产品报告.pdf', type: 'PDF', size: '2.8 MB', syncMethod: 'API同步', lastSync: '2026-05-21 02:00', status: '入库·解析·编译' },
  { name: '理财产品收益率统计.docx', type: 'DOCX', size: '1.2 MB', syncMethod: 'API同步', lastSync: '2026-05-21 02:00', status: '入库·解析·编译' },
  { name: '风险监控数据-2026-05.xlsx', type: 'XLSX', size: '856 KB', syncMethod: 'API同步', lastSync: '2026-05-21 02:00', status: '入库·解析·编译' },
  { name: '客户风险评估模型说明.pdf', type: 'PDF', size: '4.5 MB', syncMethod: 'API同步', lastSync: '2026-05-20 02:00', status: '入库·解析' },
  { name: '不良贷款分析报告-2026Q1.pptx', type: 'PPTX', size: '6.2 MB', syncMethod: 'API同步', lastSync: '2026-05-20 02:00', status: '入库·解析·编译' },
  { name: '金融监管政策解读文档.docx', type: 'DOCX', size: '1.8 MB', syncMethod: 'API同步', lastSync: '2026-05-19 02:00', status: '入库·解析中' },
  { name: '资产负债数据表.xlsx', type: 'XLSX', size: '624 KB', syncMethod: 'API同步', lastSync: '2026-05-19 02:00', status: '入库·解析·编译' },
]

export default function DomainKnowledgeDatasourceSync() {
  const { id } = useParams()
  const navigate = useNavigate()

  const columns = [
    { title: '文档名称', dataIndex: 'name', key: 'name', width: 260, render: (v: string) => <a className="yx-table-action">{v}</a> },
    { title: '类型', dataIndex: 'type', key: 'type', width: 80 },
    { title: '大小', dataIndex: 'size', key: 'size', width: 90 },
    { title: '同步方式', dataIndex: 'syncMethod', key: 'syncMethod', width: 110, render: (v: string) => <span style={{ fontSize: 12, color: '#10b981' }}><CloudOutlined /> {v}</span> },
    { title: '上次同步', dataIndex: 'lastSync', key: 'lastSync', width: 150 },
    { title: '状态', dataIndex: 'status', key: 'status', width: 160, render: (v: string) => {
      const steps = v.split('·')
      return (
        <Space size={4}>
          {steps.map((s, i) => (
            <React.Fragment key={i}>
              <Tag color={s.includes('中') ? 'processing' : s === '编译' ? 'default' : 'success'} style={{ fontSize: 11, padding: '2px 8px' }}>{s}</Tag>
              {i < steps.length - 1 && <span style={{ color: '#d1d5db', fontSize: 10 }}>·</span>}
            </React.Fragment>
          ))}
        </Space>
      )
    }},
    { title: '操作', key: 'actions', width: 80, render: () => <a className="yx-table-action">查看</a> },
  ]

  return (
    <div>
      <a onClick={() => navigate(`/domain-knowledge/${id}`)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginBottom: 16, fontSize: 14, color: '#64748b', cursor: 'pointer' }}>
        <ArrowLeftOutlined /> 返回知识库详情
      </a>

      <Card style={{ borderRadius: 14, marginBottom: 24, border: '1px solid #eef2f6', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }} bodyStyle={{ padding: '20px 24px', display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{ width: 48, height: 48, borderRadius: 12, background: '#ecfdf5', color: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, flexShrink: 0 }}><CloudOutlined /></div>
        <div style={{ flex: 1 }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: '#0b2b5c', margin: 0 }}>{dsInfo.name}</h2>
          <div style={{ display: 'flex', gap: 16, marginTop: 4, fontSize: 13, color: '#64748b', flexWrap: 'wrap' }}>
            <span>{dsInfo.type}</span><span>{dsInfo.space}</span><span>{dsInfo.url}</span><span>{dsInfo.docs} 文档</span>
          </div>
        </div>
        <Space>
          <Button type="primary" icon={<SyncOutlined />}>立即同步</Button>
          <Button icon={<SettingOutlined />}>配置</Button>
        </Space>
      </Card>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16, marginBottom: 20 }}>
        {syncStats.map((s) => (
          <Card key={s.label} style={{ borderRadius: 10, textAlign: 'center' }} bodyStyle={{ padding: 16 }}>
            <div style={{ fontSize: 16, fontWeight: 600, color: s.color || '#0b2b5c' }}>{s.value}</div>
            <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>{s.label}</div>
          </Card>
        ))}
      </div>

      <Card style={{ borderRadius: 14, border: '1px solid #eef2f6', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }} bodyStyle={{ padding: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid #eef2f6' }}>
          <Space>
            <span style={{ fontSize: 14, fontWeight: 600, color: '#0b2b5c' }}>同步文档列表</span>
            <Input prefix={<span style={{ color: '#94a3b8' }}>🔍</span>} placeholder="搜索文档名称..." style={{ width: 240 }} />
          </Space>
          <span style={{ fontSize: 12, color: '#94a3b8' }}>自动同步，无需手动上传</span>
        </div>
        <Table columns={columns} dataSource={docList} rowKey="name" pagination={{ total: 856, pageSize: 7 }} size="middle" />
      </Card>
    </div>
  )
}
