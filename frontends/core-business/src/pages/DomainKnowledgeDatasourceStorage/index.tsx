import React from 'react'
import { Button, Card, Table, Tag, Input, Space } from 'antd'
import { ArrowLeftOutlined, FolderOpenOutlined, SyncOutlined, SettingOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'

const dsInfo = {
  name: '产品文件存储', type: '文件存储直连', space: '金融风控空间', path: '//nas.finance.internal/product-files', docs: 86,
}

const syncStats = [
  { label: '总文档数', value: '86', color: '#10b981' },
  { label: '同步状态', value: '已暂停', color: '#f97316' },
  { label: '同步频率', value: '每日 04:00', color: '#3b82f6' },
  { label: '上次同步时间', value: '2026-05-20 04:00' },
]

const docList = [
  { name: '产品设计规范-v3.pdf', type: 'PDF', size: '4.2 MB', syncMethod: '文件存储直连', lastSync: '2026-05-20 04:00', status: '入库·解析·编译' },
  { name: '技术架构文档.docx', type: 'DOCX', size: '1.8 MB', syncMethod: '文件存储直连', lastSync: '2026-05-20 04:00', status: '入库·解析·编译' },
  { name: 'API接口文档.html', type: 'HTML', size: '256 KB', syncMethod: '文件存储直连', lastSync: '2026-05-20 04:00', status: '入库·解析' },
  { name: '数据库设计说明书.pdf', type: 'PDF', size: '3.2 MB', syncMethod: '文件存储直连', lastSync: '2026-05-19 04:00', status: '入库·解析·编译' },
  { name: '测试报告-2026Q1.xlsx', type: 'XLSX', size: '890 KB', syncMethod: '文件存储直连', lastSync: '2026-05-19 04:00', status: '入库·解析中' },
  { name: '项目部署指南.md', type: 'MD', size: '128 KB', syncMethod: '文件存储直连', lastSync: '2026-05-18 04:00', status: '入库·解析中' },
  { name: '需求规格说明书-v2.docx', type: 'DOCX', size: '2.1 MB', syncMethod: '文件存储直连', lastSync: '2026-05-18 04:00', status: '入库·解析·编译' },
]

export default function DomainKnowledgeDatasourceStorage() {
  const { id } = useParams()
  const navigate = useNavigate()

  const columns = [
    { title: '文档名称', dataIndex: 'name', key: 'name', width: 240, render: (v: string) => <a className="yx-table-action">{v}</a> },
    { title: '类型', dataIndex: 'type', key: 'type', width: 80 },
    { title: '大小', dataIndex: 'size', key: 'size', width: 90 },
    { title: '同步方式', dataIndex: 'syncMethod', key: 'syncMethod', width: 130, render: (v: string) => <span style={{ fontSize: 12, color: '#f97316' }}><FolderOpenOutlined /> {v}</span> },
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
        <div style={{ width: 48, height: 48, borderRadius: 12, background: '#fff7ed', color: '#f97316', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, flexShrink: 0 }}><FolderOpenOutlined /></div>
        <div style={{ flex: 1 }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: '#0b2b5c', margin: 0 }}>{dsInfo.name}</h2>
          <div style={{ display: 'flex', gap: 16, marginTop: 4, fontSize: 13, color: '#64748b', flexWrap: 'wrap' }}>
            <span>{dsInfo.type}</span><span>{dsInfo.space}</span><span>{dsInfo.path}</span><span>{dsInfo.docs} 文档</span>
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
          <span style={{ fontSize: 12, color: '#94a3b8' }}>文件存储直连同步，无需手动上传</span>
        </div>
        <Table columns={columns} dataSource={docList} rowKey="name" pagination={{ total: 86, pageSize: 7 }} size="middle" />
      </Card>
    </div>
  )
}
