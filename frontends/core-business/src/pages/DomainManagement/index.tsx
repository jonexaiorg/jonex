import React, { useState } from 'react'
import { Input, Select, Button, Card, Table, Tag, Modal, Space, message } from 'antd'
import { PlusOutlined, SearchOutlined, SettingOutlined, KeyOutlined } from '@ant-design/icons'

const mockDomains = [
  { name: '金融风控', space: '金融风控空间', kbs: ['金融产品知识库', '客户服务知识库'], status: '启用' },
  { name: '医疗保险', space: '医疗健康空间', kbs: ['医学文献知识库'], status: '启用' },
  { name: '智能生产', space: '智能制造空间', kbs: ['设备故障知识库'], status: '启用' },
  { name: '在线教育', space: '教育培训空间', kbs: ['课程资源知识库'], status: '维护中' },
  { name: '法律法规', space: '法律咨询空间', kbs: ['法律法规知识库', '合规文书知识库'], status: '启用' },
  { name: '智能客服', space: '金融风控空间', kbs: ['客户服务知识库'], status: '已停用' },
  { name: '质量检测', space: '智能制造空间', kbs: ['质量检测知识库'], status: '启用' },
  { name: '合规审查', space: '法律咨询空间', kbs: ['法律法规知识库'], status: '启用' },
]

const allKbs = ['金融产品知识库', '医学文献知识库', '设备故障知识库', '课程资源知识库', '法律法规知识库', '客户服务知识库', '合规文书知识库', '质量检测知识库']

const mockUsers = [
  { name: '张明远', dept: '系统管理员', avatar: '张', bg: '#3b82f6' },
  { name: '李思雨', dept: '金融风控部 · 分析师', avatar: '李', bg: '#10b981' },
  { name: '王浩', dept: '风险管理部 · 经理', avatar: '王', bg: '#8b5cf6' },
  { name: '陈雪', dept: '合规审查部 · 专员', avatar: '陈', bg: '#f97316' },
  { name: '赵一鸣', dept: '信息技术部 · 开发工程师', avatar: '赵', bg: '#ec4899' },
]

const srvList = [
  { name: '智能问答服务', type: '推理服务', key: 'sk-qa-************a3f2', endpoint: 'https://api.domain.com/qa', status: '启用' },
  { name: '知识检索服务', type: '检索服务', key: 'sk-search-********b7e1', endpoint: 'https://api.domain.com/search', status: '启用' },
  { name: '数据统计分析', type: '分析服务', key: 'sk-analytics-****d4f0', endpoint: 'https://api.domain.com/analytics', status: '启用' },
  { name: '批量处理服务', type: '处理服务', key: 'sk-batch-********c9a2', endpoint: 'https://api.domain.com/batch', status: '已暂停' },
  { name: '实时监控服务', type: '监控服务', key: 'sk-monitor-****e5b7', endpoint: 'https://api.domain.com/monitor', status: '启用' },
]

export default function DomainManagement() {
  const [search, setSearch] = useState('')
  const [spaceFilter, setSpaceFilter] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [permOpen, setPermOpen] = useState(false)
  const [srvOpen, setSrvOpen] = useState(false)
  const [currentDomain, setCurrentDomain] = useState<any>(null)

  const columns = [
    { title: '领域服务名称', dataIndex: 'name', key: 'name', width: 140, render: (v: string) => <a className="yx-table-action">{v}</a> },
    { title: '所属空间', dataIndex: 'space', key: 'space', width: 140 },
    { title: '关联知识库', dataIndex: 'kbs', key: 'kbs', width: 220, render: (v: string[]) => (
      <Space size={4} wrap>{v.map((k) => <Tag key={k} style={{ fontSize: 11, background: '#f1f5f9', color: '#64748b', border: 'none' }}>{k}</Tag>)}</Space>
    )},
    { title: '权限设置', key: 'perm', width: 100, render: (_: any, r: any) => (
      <Button type="link" size="small" onClick={() => { setCurrentDomain(r); setPermOpen(true) }}><SettingOutlined /> 设置权限</Button>
    )},
    { title: '状态', dataIndex: 'status', key: 'status', width: 80, render: (v: string) => <Tag color={v === '启用' ? 'success' : v === '维护中' ? 'warning' : 'error'}>{v}</Tag> },
    { title: '操作', key: 'actions', width: 180, render: (_: any, r: any) => (
      <Space>
        <a className="yx-table-action" onClick={() => { setCurrentDomain(r); setSrvOpen(true) }}><KeyOutlined /> 服务配置</a>
        <a className="yx-table-action" onClick={() => { setCurrentDomain(r); setEditOpen(true) }}>编辑</a>
        <a className="yx-table-action" onClick={() => { message.success(`已删除 ${r.name}`) }}>删除</a>
      </Space>
    )},
  ]

  const filtered = mockDomains.filter((d) =>
    (!spaceFilter || d.space === spaceFilter) && d.name.includes(search)
  )

  const spaces = [...new Set(mockDomains.map((d) => d.space))]

  return (
    <div>
      <div className="yx-page-title">
        <h1>领域服务管理</h1>
        <p style={{ fontSize: 14, color: '#64748b', marginTop: 6 }}>管理各领域空间下的业务领域，每个领域必属于某个领域空间，并可关联一个或多个知识库</p>
      </div>

      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
        <Select placeholder="全部空间" allowClear value={spaceFilter || undefined} onChange={(v) => setSpaceFilter(v || '')} style={{ width: 180 }}
          options={spaces.map((s) => ({ value: s, label: s }))} />
        <span style={{ fontSize: 13, color: '#94a3b8' }}>共 {filtered.length} 个领域</span>
      </div>

      <Card className="yx-card">
        <div className="yx-toolbar">
          <Input prefix={<SearchOutlined />} placeholder="搜索领域服务名称..." value={search} onChange={(e) => setSearch(e.target.value)} style={{ width: 240 }} />
          <Button type="primary" icon={<PlusOutlined />} onClick={() => { setCurrentDomain(null); setCreateOpen(true) }}>新建领域服务</Button>
        </div>
        <Table columns={columns} dataSource={filtered} rowKey="name" pagination={{ total: 8, pageSize: 8 }} size="middle" />
      </Card>

      <Modal title={currentDomain ? '编辑领域' : '新建领域服务'} open={createOpen || editOpen} onCancel={() => { setCreateOpen(false); setEditOpen(false) }} onOk={() => { message.success(currentDomain ? '保存成功' : '创建成功'); setCreateOpen(false); setEditOpen(false) }} width={600}>
        <div className="yx-form-row"><label>领域名称 <span style={{ color: '#ef4444' }}>*</span></label><Input defaultValue={currentDomain?.name || ''} /></div>
        <div className="yx-form-row"><label>所属空间 <span style={{ color: '#ef4444' }}>*</span></label>
          <Select defaultValue={currentDomain?.space} style={{ width: '100%' }} options={spaces.map((s) => ({ value: s, label: s }))} />
        </div>
        <div className="yx-form-row">
          <label>关联知识库</label>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {allKbs.map((k) => <label key={k} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 10px', borderRadius: 6, border: '1px solid #eef2f6', fontSize: 13, color: '#475569', cursor: 'pointer' }}><input type="checkbox" defaultChecked={currentDomain?.kbs?.includes(k)} />{k}</label>)}
          </div>
          <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>选择该领域需要关联的知识库，可多选</div>
        </div>
      </Modal>

      <Modal title="领域权限设置" open={permOpen} onCancel={() => setPermOpen(false)} onOk={() => { message.success('权限保存成功'); setPermOpen(false) }} width={600}>
        <p style={{ fontSize: 14, color: '#475569', marginBottom: 16 }}>为领域 <strong style={{ color: '#0b2b5c' }}>{currentDomain?.name}</strong> 添加成员并设置权限</p>
        <Input prefix={<SearchOutlined />} placeholder="搜索用户或角色..." style={{ marginBottom: 12 }} />
        {mockUsers.map((u, i) => (
          <div key={u.name} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px', borderRadius: 8, border: '1px solid #eef2f6', marginBottom: 8 }}>
            <div style={{ width: 32, height: 32, borderRadius: 8, background: u.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 600, color: '#fff', flexShrink: 0 }}>{u.avatar}</div>
            <div style={{ flex: 1 }}><div style={{ fontSize: 14, fontWeight: 500 }}>{u.name}</div><div style={{ fontSize: 12, color: '#94a3b8' }}>{u.dept}</div></div>
            <Select defaultValue={i === 2 || i === 4 ? '管理' : '查看'} style={{ width: 100 }} options={[{ value: '查看', label: '查看' }, { value: '管理', label: '管理' }]} />
          </div>
        ))}
      </Modal>

      <Modal title="服务配置" open={srvOpen} onCancel={() => setSrvOpen(false)} onOk={() => { message.success('配置保存成功'); setSrvOpen(false) }} width={720}>
        <p style={{ fontSize: 14, color: '#475569', marginBottom: 16 }}>领域 <strong style={{ color: '#0b2b5c' }}>{currentDomain?.name}</strong> 的服务与 API Key 管理</p>
        <div style={{ textAlign: 'right', marginBottom: 12 }}>
          <Button type="primary" size="small" icon={<PlusOutlined />}>新建服务</Button>
        </div>
        <Table columns={[
          { title: '服务名称', dataIndex: 'name', key: 'name', width: 130 },
          { title: '服务类型', dataIndex: 'type', key: 'type', width: 90 },
          { title: 'API Key', dataIndex: 'key', key: 'key', width: 200, render: (v: string) => <code style={{ fontSize: 12, background: '#f1f5f9', padding: '2px 8px', borderRadius: 4 }}>{v}</code> },
          { title: '调用端点', dataIndex: 'endpoint', key: 'endpoint', width: 200 },
          { title: '状态', dataIndex: 'status', key: 'status', width: 80, render: (v: string) => <Tag color={v === '启用' ? 'success' : 'warning'}>{v}</Tag> },
          { title: '操作', key: 'actions', width: 80, render: () => <Space size={4}><a className="yx-table-action">编辑</a><a className="yx-table-action">删除</a></Space> },
        ]} dataSource={srvList} rowKey="name" pagination={false} size="small" />
      </Modal>
    </div>
  )
}
