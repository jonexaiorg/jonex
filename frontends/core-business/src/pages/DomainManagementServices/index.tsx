import React, { useState } from 'react'
import { Input, Select, Button, Card, Table, Tag, Space } from 'antd'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons'

const mockServices = [
  { name: '智能问答服务', domain: '金融风控', type: '推理服务', callType: 'REST API', status: '运行中' },
  { name: '知识检索服务', domain: '金融风控', type: '检索服务', callType: 'gRPC', status: '运行中' },
  { name: '病历分析服务', domain: '医疗保险', type: '分析服务', callType: 'REST API', status: '运行中' },
  { name: '设备诊断服务', domain: '智能生产', type: '推理服务', callType: 'REST API', status: '维护中' },
  { name: '课程推荐服务', domain: '在线教育', type: '分析服务', callType: 'gRPC', status: '运行中' },
]

export default function DomainManagementServices() {
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('全部类型')

  const columns = [
    { title: '服务名称', dataIndex: 'name', key: 'name', width: 160, render: (v: string) => <a className="yx-table-action">{v}</a> },
    { title: '所属领域', dataIndex: 'domain', key: 'domain', width: 120 },
    { title: '服务类型', dataIndex: 'type', key: 'type', width: 110 },
    { title: '调用方式', dataIndex: 'callType', key: 'callType', width: 110 },
    { title: '状态', dataIndex: 'status', key: 'status', width: 90, render: (v: string) => <Tag color={v === '运行中' ? 'success' : 'warning'}>{v}</Tag> },
    { title: '操作', key: 'actions', width: 120, render: () => <Space><a className="yx-table-action">编辑</a><a className="yx-table-action">监控</a></Space> },
  ]

  const filtered = mockServices.filter((s) =>
    s.name.includes(search) && (typeFilter === '全部类型' || s.type === typeFilter)
  )

  return (
    <div>
      <div className="yx-page-title"><h1>服务管理</h1></div>

      <Card className="yx-card">
        <div className="yx-toolbar">
          <Input prefix={<SearchOutlined />} placeholder="搜索服务名称..." value={search} onChange={(e) => setSearch(e.target.value)} style={{ width: 240 }} />
          <Select value={typeFilter} onChange={setTypeFilter} style={{ width: 140 }}
            options={['全部类型', '检索服务', '推理服务', '分析服务'].map((s) => ({ value: s, label: s }))} />
          <Button type="primary" icon={<PlusOutlined />}>新建服务</Button>
        </div>
        <Table columns={columns} dataSource={filtered} rowKey="name" pagination={{ total: 10, pageSize: 5 }} size="middle" />
      </Card>
    </div>
  )
}
