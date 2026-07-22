import React, { useState } from 'react'
import { Input, Button, Card, Table, Tag, Modal, Select, Space, message } from 'antd'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons'

const mockSpaces = [
  { name: '金融风控空间', code: 'finance-risk', desc: '金融风控领域相关知识管理与检索', createdAt: '2026-05-22', status: '启用' },
  { name: '医疗健康空间', code: 'medical-health', desc: '医疗健康领域知识库与诊断方案', createdAt: '2026-05-20', status: '启用' },
  { name: '智能制造空间', code: 'smart-manufacturing', desc: '智能制造设备故障诊断与预测性维护', createdAt: '2026-05-18', status: '维护中' },
  { name: '教育培训空间', code: 'edu-training', desc: '在线教育内容管理与课程推荐', createdAt: '2026-05-15', status: '启用' },
  { name: '法律咨询空间', code: 'legal-consult', desc: '法律法规数据库与合规审查', createdAt: '2026-05-10', status: '启用' },
]

const mockUsers = [
  { name: '张明远', dept: '系统管理部', avatar: '张' },
  { name: '李思雨', dept: '业务运营部', avatar: '李' },
  { name: '王浩', dept: '数据管理部', avatar: '王' },
  { name: '陈雪', dept: '知识工程部', avatar: '陈' },
  { name: '赵一鸣', dept: '技术开发部', avatar: '赵' },
]

export default function DomainSpace() {
  const [search, setSearch] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [permOpen, setPermOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [currentSpace, setCurrentSpace] = useState<any>(null)
  const [spaces, setSpaces] = useState(mockSpaces)

  const toggleStatus = (code: string) => {
    setSpaces((prev) => prev.map((s) => s.code === code ? { ...s, status: s.status === '启用' ? '维护中' : '启用' } : s))
  }

  const columns = [
    { title: '空间名称', dataIndex: 'name', key: 'name', width: 160 },
    { title: '编码', dataIndex: 'code', key: 'code', width: 150, render: (v: string) => <code>{v}</code> },
    { title: '描述', dataIndex: 'desc', key: 'desc', ellipsis: true },
    { title: '创建时间', dataIndex: 'createdAt', key: 'createdAt', width: 130 },
    { title: '状态', dataIndex: 'status', key: 'status', width: 90, render: (v: string, r: any) => (
      <Tag color={v === '启用' ? 'success' : 'warning'} style={{ cursor: 'pointer' }} onClick={() => toggleStatus(r.code)}>{v}</Tag>
    )},
    { title: '权限设置', key: 'perm', width: 90, render: (_: any, r: any) => <Button type="link" size="small" onClick={() => { setCurrentSpace(r); setPermOpen(true) }}>设置权限</Button> },
    { title: '操作', key: 'actions', width: 140, render: (_: any, r: any) => (
      <Space><a className="yx-table-action" onClick={() => { setCurrentSpace(r); setEditOpen(true) }}>编辑</a><a className="yx-table-action" style={{ color: '#dc2626' }} onClick={() => { setCurrentSpace(r); setDeleteOpen(true) }}>删除</a></Space>
    )},
  ]

  return (
    <div>
      <div className="yx-page-title"><h1>领域空间管理</h1></div>
      <Card className="yx-card">
        <div className="yx-toolbar">
          <Input prefix={<SearchOutlined />} placeholder="搜索空间名称..." value={search} onChange={(e) => setSearch(e.target.value)} style={{ width: 240 }} />
          <Button type="primary" icon={<PlusOutlined />} onClick={() => { setCurrentSpace(null); setCreateOpen(true) }}>新建领域空间</Button>
        </div>
        <Table columns={columns} dataSource={spaces.filter((s) => s.name.includes(search))} rowKey="code" pagination={{ total: 23, pageSize: 5 }} size="middle" />
      </Card>

      <Modal title={currentSpace ? '编辑领域空间' : '新建领域空间'} open={createOpen || editOpen} onCancel={() => { setCreateOpen(false); setEditOpen(false) }} onOk={() => { message.success(currentSpace ? '保存成功' : '创建成功'); setCreateOpen(false); setEditOpen(false) }}>
        <div className="yx-form-row"><label>空间名称</label><input type="text" className="ant-input" defaultValue={currentSpace?.name || ''} /></div>
        <div className="yx-form-row"><label>空间编码</label><input type="text" className="ant-input" defaultValue={currentSpace?.code || ''} /></div>
        <div className="yx-form-row"><label>空间描述</label><textarea className="ant-input" defaultValue={currentSpace?.desc || ''} rows={3} /></div>
      </Modal>

      <Modal title="确认删除" open={deleteOpen} onCancel={() => setDeleteOpen(false)} onOk={() => { message.success('已删除'); setDeleteOpen(false) }} okButtonProps={{ danger: true }} okText="确认删除" cancelText="取消">
        <p>确定要删除空间 <strong>{currentSpace?.name}</strong> 吗？<br /><span style={{ color: '#94a3b8', fontSize: 13 }}>此操作不可恢复，请谨慎操作。</span></p>
      </Modal>

      <Modal title="权限设置" open={permOpen} onCancel={() => setPermOpen(false)} onOk={() => { message.success('权限保存成功'); setPermOpen(false) }} width={600}>
        <Input prefix={<SearchOutlined />} placeholder="搜索用户或角色..." style={{ marginBottom: 16 }} />
        {mockUsers.map((u) => (
          <div key={u.name} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0', borderBottom: '1px solid #f1f5f9' }}>
            <div style={{ width: 34, height: 34, borderRadius: 9, background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 14, fontWeight: 600, flexShrink: 0 }}>{u.avatar}</div>
            <div style={{ flex: 1 }}><div style={{ fontSize: 14, fontWeight: 500 }}>{u.name}</div><div style={{ fontSize: 12, color: '#94a3b8' }}>{u.dept}</div></div>
            <Select defaultValue="查看" style={{ width: 100 }} options={[{ value: '查看', label: '查看' }, { value: '管理', label: '管理' }]} />
          </div>
        ))}
      </Modal>
    </div>
  )
}
