import React, { useState } from 'react'
import { Button, Card, Table, Tag, Input, Select, Space } from 'antd'
import { PlayCircleOutlined, SearchOutlined } from '@ant-design/icons'

const compileList = [
  { kb: '金融产品知识库', version: 'v2.5.1', status: '成功', entities: 12845, relations: 45672, duration: '3分28秒' },
  { kb: '医学文献知识库', version: 'v2.4.0', status: '成功', entities: 35621, relations: 128430, duration: '8分15秒' },
  { kb: '设备故障知识库', version: 'v1.9.2', status: '进行中', entities: 8234, relations: 0, duration: '--' },
  { kb: '课程资源知识库', version: 'v2.1.0', status: '成功', entities: 24310, relations: 89256, duration: '5分42秒' },
  { kb: '法律法规知识库', version: 'v3.0.1', status: '失败', entities: 0, relations: 0, duration: '1分05秒' },
]

const statusColor: Record<string, string> = { '成功': 'success', '进行中': 'processing', '失败': 'error' }

export default function DomainKnowledgeCompileResults() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('全部状态')

  const columns = [
    { title: '知识库', dataIndex: 'kb', key: 'kb', width: 180, render: (v: string) => <a className="yx-table-action">{v}</a> },
    { title: '编译版本', dataIndex: 'version', key: 'version', width: 100 },
    { title: '状态', dataIndex: 'status', key: 'status', width: 90, render: (v: string) => <Tag color={statusColor[v]}>{v}</Tag> },
    { title: '实体数', dataIndex: 'entities', key: 'entities', width: 100, render: (v: number) => v ? v.toLocaleString() : '--' },
    { title: '关系数', dataIndex: 'relations', key: 'relations', width: 100, render: (v: number) => v ? v.toLocaleString() : '--' },
    { title: '耗时', dataIndex: 'duration', key: 'duration', width: 100 },
    { title: '操作', key: 'actions', width: 100, render: (_: any, r: any) => (
      <Space>
        <a className="yx-table-action">详情</a>
        {r.status === '成功' ? <a className="yx-table-action">回滚</a> : r.status === '失败' ? <a className="yx-table-action">重试</a> : null}
      </Space>
    )},
  ]

  const filtered = compileList.filter((c) =>
    c.kb.includes(search) && (statusFilter === '全部状态' || c.status === statusFilter)
  )

  return (
    <div>
      <div className="yx-page-title">
        <h1>编译结果查看</h1>
      </div>

      <Card className="yx-card">
        <div className="yx-toolbar">
          <Input
            prefix={<SearchOutlined />} placeholder="搜索知识库..." value={search}
            onChange={(e) => setSearch(e.target.value)} style={{ width: 240 }}
          />
          <Select value={statusFilter} onChange={setStatusFilter} style={{ width: 140 }}
            options={['全部状态', '成功', '进行中', '失败'].map((s) => ({ value: s, label: s }))}
          />
          <Button type="primary" icon={<PlayCircleOutlined />}>执行编译</Button>
        </div>
        <Table columns={columns} dataSource={filtered} rowKey="kb" pagination={{ total: 15, pageSize: 5 }} size="middle" />
      </Card>
    </div>
  )
}
