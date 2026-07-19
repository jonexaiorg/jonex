import React, { useState } from 'react'
import { Button, Card, Table, Tag, Input, Space } from 'antd'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'

const getConnStatusColor = (t: (k: string) => string, status: string): string => {
  if (status === t('dataSource.connected')) return 'success'
  if (status === t('dataSource.connecting')) return 'processing'
  if (status === t('dataSource.connectFailed')) return 'error'
  return 'default'
}

const getTypeColor = (t: (k: string) => string, type: string): string => {
  if (type === t('dataSource.typeDatabase')) return 'blue'
  if (type === t('dataSource.typeApi')) return 'green'
  if (type === t('dataSource.typeFile')) return 'orange'
  return 'default'
}

export default function DomainKnowledgeDataSource() {
  const { t } = useTranslation()
  const [search, setSearch] = useState('')

  const sources = [
    { name: '金融产品数据库', type: t('dataSource.typeDatabase'), status: t('dataSource.connected'), lastSync: '2026-05-21 14:30' },
    { name: '市场行情 API', type: t('dataSource.typeApi'), status: t('dataSource.connected'), lastSync: '2026-05-21 14:25' },
    { name: '医学文献 PDF', type: t('dataSource.typeFile'), status: t('dataSource.connected'), lastSync: '2026-05-20 18:00' },
    { name: '设备传感器数据', type: t('dataSource.typeApi'), status: t('dataSource.connecting'), lastSync: '2026-05-21 12:00' },
    { name: '法律法规文件存储', type: t('dataSource.typeFile'), status: t('dataSource.connectFailed'), lastSync: '2026-05-19 09:15' },
  ]

  const columns = [
    { title: t('dataSource.name'), dataIndex: 'name', key: 'name', width: 180, render: (v: string) => <a className="yx-table-action">{v}</a> },
    { title: t('knowledgeSearch.fileType'), dataIndex: 'type', key: 'type', width: 100, render: (v: string) => <Tag color={getTypeColor(t, v)}>{v}</Tag> },
    { title: t('dataSource.syncStatus'), dataIndex: 'status', key: 'status', width: 110, render: (v: string) => <Tag color={getConnStatusColor(t, v)}>{v}</Tag> },
    { title: t('dataSource.lastSyncTime'), dataIndex: 'lastSync', key: 'lastSync', width: 160 },
    { title: t('knowledgeSearch.actions'), key: 'actions', width: 160, render: () => <Space><a className="yx-table-action">{t('dataSource.edit')}</a><a className="yx-table-action">{t('dataSource.test')}</a><a className="yx-table-action">{t('dataSource.delete')}</a></Space> },
  ]

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('knowledgeSearch.dataSourceConfig')}</h1>
      </div>

      <Card className="yx-card">
        <div className="yx-toolbar">
          <Input prefix={<SearchOutlined />} placeholder="搜索数据源..." value={search} onChange={(e) => setSearch(e.target.value)} style={{ width: 240 }} />
          <Button type="primary" icon={<PlusOutlined />}>{t('dataSource.addDataSource')}</Button>
        </div>
        <Table columns={columns} dataSource={sources.filter((s) => s.name.includes(search))} rowKey="name" pagination={{ total: 12, pageSize: 5 }} size="middle" />
      </Card>
    </div>
  )
}
