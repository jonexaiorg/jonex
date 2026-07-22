import React, { useState } from 'react'
import { Button, Card, Table, Tag, Input, Space } from 'antd'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons'

const sources = [
  { name: '金融产品数据库', type: '数据库', status: '已连接', lastSync: '2026-05-21 14:30' },
  { name: '市场行情 API', type: 'API', status: '已连接', lastSync: '2026-05-21 14:25' },
  { name: '医学文献 PDF', type: '文件', status: '已连接', lastSync: '2026-05-20 18:00' },
  { name: '设备传感器数据', type: 'API', status: '连接中', lastSync: '2026-05-21 12:00' },
  { name: '法律法规文件存储', type: '文件', status: '连接失败', lastSync: '2026-05-19 09:15' },
]

const connStatusColor: Record<string, string> = { '已连接': 'success', '连接中': 'processing', '连接失败': 'error' }
const typeColor: Record<string, string> = { '数据库': 'blue', 'API': 'green', '文件': 'orange' }

export default function DomainKnowledgeDataSource() {
  const [search, setSearch] = useState('')

  const columns = [
    { title: '数据源名称', dataIndex: 'name', key: 'name', width: 180, render: (v: string) => <a className="yx-table-action">{v}</a> },
    { title: '类型', dataIndex: 'type', key: 'type', width: 100, render: (v: string) => <Tag color={typeColor[v]}>{v}</Tag> },
    { title: '连接状态', dataIndex: 'status', key: 'status', width: 110, render: (v: string) => <Tag color={connStatusColor[v]}>{v}</Tag> },
    { title: '最近同步', dataIndex: 'lastSync', key: 'lastSync', width: 160 },
    { title: '操作', key: 'actions', width: 160, render: () => <Space><a className="yx-table-action">编辑</a><a className="yx-table-action">测试</a><a className="yx-table-action">删除</a></Space> },
  ]

  return (
    <div>
      <div className="yx-page-title">
        <h1>数据源配置</h1>
      </div>

      <Card className="yx-card">
        <div className="yx-toolbar">
          <Input prefix={<SearchOutlined />} placeholder="搜索数据源..." value={search} onChange={(e) => setSearch(e.target.value)} style={{ width: 240 }} />
          <Button type="primary" icon={<PlusOutlined />}>添加数据源</Button>
        </div>
        <Table columns={columns} dataSource={sources.filter((s) => s.name.includes(search))} rowKey="name" pagination={{ total: 12, pageSize: 5 }} size="middle" />
      </Card>
    </div>
  )
}
