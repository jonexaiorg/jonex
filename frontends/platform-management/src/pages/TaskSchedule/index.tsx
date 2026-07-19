import React from 'react'
import { Input, Button, Table, Tag, Select } from 'antd'
import { useTranslation } from 'react-i18next'
import { SearchOutlined, PlusOutlined } from '@ant-design/icons'

const tasks = [
  { name: '金融风控知识编译', type: '知识编译', strategy: '每天 02:00', status: 'running', lastRun: '2026-05-22 02:00', nextRun: '2026-05-23 02:00' },
  { name: '医学文献向量化', type: '向量化', strategy: '每小时', status: 'running', lastRun: '2026-05-22 15:00', nextRun: '2026-05-22 16:00' },
  { name: '设备数据同步', type: '数据同步', strategy: '每 30 分', status: 'running', lastRun: '2026-05-22 15:30', nextRun: '2026-05-22 16:00' },
  { name: '课程资源编译', type: '知识编译', strategy: '每周日 03:00', status: 'paused', lastRun: '2026-05-17 03:00', nextRun: '--' },
  { name: '法律法规图谱构建', type: '图谱构建', strategy: '手动触发', status: 'failed', lastRun: '2026-05-21 10:00', nextRun: '--' },
]

const statusColor: Record<string, string> = { running: 'success', paused: 'warning', failed: 'error' }
const statusKeys: Record<string, string> = { running: 'status.running', paused: 'status.paused', failed: 'status.failed' }

export default function TaskSchedule() {
  const { t } = useTranslation()

  const columns = [
    { title: t('taskSchedule.taskName'), dataIndex: 'name', key: 'name', render: (v: string) => <a className="yx-table-action">{v}</a> },
    { title: t('taskSchedule.taskType'), dataIndex: 'type', key: 'type' },
    { title: t('taskSchedule.schedule'), dataIndex: 'strategy', key: 'strategy' },
    { title: t('taskSchedule.status'), dataIndex: 'status', key: 'status', render: (v: string) => <Tag color={statusColor[v]}>{t(statusKeys[v] || v)}</Tag> },
    { title: t('taskSchedule.lastRunTime'), dataIndex: 'lastRun', key: 'lastRun' },
    { title: t('taskSchedule.nextRunTime'), dataIndex: 'nextRun', key: 'nextRun' },
    { title: t('taskSchedule.actions', '操作'), key: 'actions', render: () => <span><a className="yx-table-action">{t('taskSchedule.pause')}</a><a className="yx-table-action" style={{ marginLeft: 8 }}>{t('taskSchedule.edit')}</a></span> },
  ]

  return (
    <div>
      <div className="yx-page-title"><h1>{t('taskSchedule.title')}</h1></div>
      <div className="yx-card">
        <div className="yx-toolbar">
          <Input prefix={<SearchOutlined />} placeholder={t('taskSchedule.searchPlaceholder', '搜索任务...')} style={{ width: 240 }} />
          <Select
            defaultValue="all"
            style={{ width: 120 }}
            options={[
              { value: 'all', label: t('status.allStatus') },
              { value: 'running', label: t('status.running') },
              { value: 'paused', label: t('status.paused') },
              { value: 'completed', label: t('status.completed') },
            ]}
          />
          <Button type="primary" icon={<PlusOutlined />}>{t('taskSchedule.create')}</Button>
        </div>
        <Table columns={columns} dataSource={tasks} rowKey="name" pagination={{ total: 9, pageSize: 10 }} size="middle" />
      </div>
    </div>
  )
}
