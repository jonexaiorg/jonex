import React from 'react'
import { Input, Button, Table, Tag, Select } from 'antd'
import { SearchOutlined, PlusOutlined } from '@ant-design/icons'

const users = [
  { username: 'zhangmy', name: '张明远', email: 'zhangmy@jonex.com', role: '系统管理员', tenant: '--', status: '启用', lastLogin: '2026-05-22 09:15' },
  { username: 'lim', name: '李明', email: 'lim@fintech.com', role: '领域服务管理员', tenant: '金融科技', status: '启用', lastLogin: '2026-05-21 16:30' },
  { username: 'wangf', name: '王芳', email: 'wangf@med.com', role: '领域服务管理员', tenant: '医疗健康', status: '启用', lastLogin: '2026-05-21 14:20' },
  { username: 'zhaoq', name: '赵强', email: 'zhaoq@smartmfg.com', role: '知识编辑者', tenant: '智造科技', status: '启用', lastLogin: '2026-05-20 11:45' },
  { username: 'sunl', name: '孙丽', email: 'sunl@edu.com', role: '知识编辑者', tenant: '教育投资', status: '已停用', lastLogin: '2026-05-15 09:00' },
  { username: 'zhoul', name: '周磊', email: 'zhoul@law.com', role: '领域服务管理员', tenant: '法律咨询', status: '启用', lastLogin: '2026-05-22 08:30' },
  { username: 'chenwei', name: '陈伟', email: 'chenw@fintech.com', role: '观察者', tenant: '金融科技', status: '启用', lastLogin: '2026-05-19 10:00' },
  { username: 'liuyan', name: '刘艳', email: 'liuy@med.com', role: '观察者', tenant: '医疗健康', status: '已停用', lastLogin: '2026-05-10 15:20' },
]

export default function UserManagement() {
  const columns = [
    { title: '用户名', dataIndex: 'username', key: 'username', render: (v: string) => <a className="yx-table-action">{v}</a> },
    { title: '姓名', dataIndex: 'name', key: 'name' },
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    { title: '角色', dataIndex: 'role', key: 'role' },
    { title: '所属租户', dataIndex: 'tenant', key: 'tenant' },
    { title: '状态', dataIndex: 'status', key: 'status', width: 90, render: (v: string) => <Tag color={v === '启用' ? 'success' : 'error'}>{v}</Tag> },
    { title: '最后登录', dataIndex: 'lastLogin', key: 'lastLogin', width: 150 },
    { title: '操作', key: 'actions', width: 140, render: () => <span><a className="yx-table-action">编辑</a><a className="yx-table-action" style={{ marginLeft: 8 }}>重置密码</a></span> },
  ]

  return (
    <div>
      <div className="yx-page-title"><h1>用户管理</h1></div>
      <div className="yx-card">
        <div className="yx-toolbar">
          <Input prefix={<SearchOutlined />} placeholder="搜索用户..." style={{ width: 240 }} />
          <Select defaultValue="全部角色" style={{ width: 140 }} options={['全部角色', '系统管理员', '领域服务管理员', '知识编辑者'].map(s => ({ value: s, label: s }))} />
          <Button type="primary" icon={<PlusOutlined />}>新建用户</Button>
        </div>
        <Table columns={columns} dataSource={users} rowKey="username" pagination={{ total: 16, pageSize: 10 }} size="middle" />
      </div>
    </div>
  )
}
