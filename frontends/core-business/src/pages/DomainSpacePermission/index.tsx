import React from 'react'
import { Input, Card, Table, Button } from 'antd'
import { SearchOutlined, PlusOutlined, CheckCircleFilled, CloseCircleFilled } from '@ant-design/icons'

const permissions = [
  { role: '管理员', read: true, write: true, manage: true, delete: true },
  { role: '编辑者', read: true, write: true, manage: false, delete: false },
  { role: '观察者', read: true, write: false, manage: false, delete: false },
  { role: '访客', read: true, write: false, manage: false, delete: false },
]

const columns = [
  { title: '角色', dataIndex: 'role', key: 'role', width: 120 },
  { title: '可读', dataIndex: 'read', key: 'read', width: 80, render: (v: boolean) => v ? <CheckCircleFilled style={{ color: '#059669' }} /> : <CloseCircleFilled style={{ color: '#dc2626' }} /> },
  { title: '可写', dataIndex: 'write', key: 'write', width: 80, render: (v: boolean) => v ? <CheckCircleFilled style={{ color: '#059669' }} /> : <CloseCircleFilled style={{ color: '#dc2626' }} /> },
  { title: '可管理', dataIndex: 'manage', key: 'manage', width: 80, render: (v: boolean) => v ? <CheckCircleFilled style={{ color: '#059669' }} /> : <CloseCircleFilled style={{ color: '#dc2626' }} /> },
  { title: '可删除', dataIndex: 'delete', key: 'delete', width: 80, render: (v: boolean) => v ? <CheckCircleFilled style={{ color: '#059669' }} /> : <CloseCircleFilled style={{ color: '#dc2626' }} /> },
  { title: '操作', key: 'actions', width: 80, render: () => <a className="yx-table-action">编辑</a> },
]

export default function DomainSpacePermission() {
  return (
    <div>
      <div className="yx-page-title">
        <h1>权限管理</h1>
      </div>
      <Card className="yx-card">
        <div className="yx-toolbar">
          <Input prefix={<SearchOutlined />} placeholder="搜索角色..." style={{ width: 240 }} />
          <Button type="primary" icon={<PlusOutlined />}>添加角色</Button>
        </div>
        <Table columns={columns} dataSource={permissions} rowKey="role" pagination={false} size="middle" />
        <div style={{ marginTop: 16, padding: '10px 14px', background: '#eff6ff', borderRadius: 8, fontSize: 13, color: '#64748b' }}>
          权限设置将同步应用到该空间下的所有领域和知识库
        </div>
      </Card>
    </div>
  )
}
