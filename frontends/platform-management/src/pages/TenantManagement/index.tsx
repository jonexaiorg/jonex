import React from 'react'
import { Input, Button, Table, Tag, Select } from 'antd'
import { SearchOutlined, PlusOutlined, EditOutlined, UserOutlined } from '@ant-design/icons'

const tenants = [
  { name: '金融科技有限公司', contact: '李明', email: 'liming@fintech.com', spaces: 3, users: 25, status: '启用' },
  { name: '医疗健康集团', contact: '王芳', email: 'wangfang@med.com', spaces: 2, users: 18, status: '启用' },
  { name: '智造科技有限公司', contact: '赵强', email: 'zhaoq@smartmfg.com', spaces: 1, users: 12, status: '启用' },
  { name: '教育投资集团', contact: '孙丽', email: 'sunli@edu.com', spaces: 1, users: 8, status: '已欠费' },
  { name: '法律咨询服务所', contact: '周磊', email: 'zhoulei@law.com', spaces: 2, users: 15, status: '启用' },
  { name: '供应链管理集团', contact: '吴涛', email: 'wutao@scm.com', spaces: 1, users: 6, status: '启用' },
  { name: '人力资源服务中心', contact: '郑红', email: 'zhengh@hr.com', spaces: 1, users: 10, status: '已欠费' },
]

export default function TenantManagement() {
  const columns = [
    { title: '租户名称', dataIndex: 'name', key: 'name', render: (v: string) => <a className="yx-table-action">{v}</a> },
    { title: '联系人', dataIndex: 'contact', key: 'contact' },
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    { title: '空间数', dataIndex: 'spaces', key: 'spaces', width: 80 },
    { title: '用户数', dataIndex: 'users', key: 'users', width: 80 },
    { title: '状态', dataIndex: 'status', key: 'status', width: 90, render: (v: string) => <Tag color={v === '启用' ? 'success' : 'warning'}>{v}</Tag> },
    { title: '操作', key: 'actions', width: 120, render: () => <span><a className="yx-table-action">编辑</a><a className="yx-table-action" style={{ marginLeft: 8 }}>管理</a></span> },
  ]

  return (
    <div>
      <div className="yx-page-title"><h1>租户管理</h1></div>
      <div className="yx-card">
        <div className="yx-toolbar">
          <Input prefix={<SearchOutlined />} placeholder="搜索租户..." style={{ width: 240 }} />
          <Button type="primary" icon={<PlusOutlined />}>新建租户</Button>
        </div>
        <Table columns={columns} dataSource={tenants} rowKey="name" pagination={{ total: 7, pageSize: 10 }} size="middle" />
      </div>
    </div>
  )
}
