import React from 'react'
import { Input, Button, Table, Tag, Select } from 'antd'
import { SearchOutlined, PlusOutlined } from '@ant-design/icons'

const tasks = [
  { name: '金融风控知识编译', type: '知识编译', strategy: '每天 02:00', status: '运行中', lastRun: '2026-05-22 02:00', nextRun: '2026-05-23 02:00' },
  { name: '医学文献向量化', type: '向量化', strategy: '每小时', status: '运行中', lastRun: '2026-05-22 15:00', nextRun: '2026-05-22 16:00' },
  { name: '设备数据同步', type: '数据同步', strategy: '每 30 分', status: '运行中', lastRun: '2026-05-22 15:30', nextRun: '2026-05-22 16:00' },
  { name: '课程资源编译', type: '知识编译', strategy: '每周日 03:00', status: '已暂停', lastRun: '2026-05-17 03:00', nextRun: '--' },
  { name: '法律法规图谱构建', type: '图谱构建', strategy: '手动触发', status: '已失败', lastRun: '2026-05-21 10:00', nextRun: '--' },
]

const statusColor: Record<string, string> = { '运行中': 'success', '已暂停': 'warning', '已失败': 'error' }

export default function TaskSchedule() {
  const columns = [
    { title: '任务名称', dataIndex: 'name', key: 'name', render: (v: string) => <a className="yx-table-action">{v}</a> },
    { title: '类型', dataIndex: 'type', key: 'type' },
    { title: '调度策略', dataIndex: 'strategy', key: 'strategy' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => <Tag color={statusColor[v]}>{v}</Tag> },
    { title: '上次执行', dataIndex: 'lastRun', key: 'lastRun' },
    { title: '下次执行', dataIndex: 'nextRun', key: 'nextRun' },
    { title: '操作', key: 'actions', render: () => <span><a className="yx-table-action">暂停</a><a className="yx-table-action" style={{ marginLeft: 8 }}>编辑</a></span> },
  ]

  return (
    <div>
      <div className="yx-page-title"><h1>任务调度</h1></div>
      <div className="yx-card">
        <div className="yx-toolbar">
          <Input prefix={<SearchOutlined />} placeholder="搜索任务..." style={{ width: 240 }} />
          <Select defaultValue="全部状态" style={{ width: 120 }} options={['全部状态', '运行中', '已暂停', '已完成'].map(s => ({ value: s, label: s }))} />
          <Button type="primary" icon={<PlusOutlined />}>新建任务</Button>
        </div>
        <Table columns={columns} dataSource={tasks} rowKey="name" pagination={{ total: 9, pageSize: 10 }} size="middle" />
      </div>
    </div>
  )
}
