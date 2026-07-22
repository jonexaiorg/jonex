import React, { useState, useMemo } from 'react'
import { Card, Table, Tag, Button, Input, Select, Modal, message } from 'antd'
import { PlusOutlined, EditOutlined, SearchOutlined } from '@ant-design/icons'
import { colors, radius } from '@jonex/platform-theme/tokens'
import type { Skill } from '../../types/catalog'

const initialSkills: Skill[] = []

const STATUS_MAP: Record<string, { label: string; cls: string }> = {
  enabled: { label: '启用', cls: 'active' },
  disabled: { label: '禁用', cls: 'inactive' },
  draft: { label: '草稿', cls: 'pending' },
}

export default function Skills() {
  const [skills, setSkills] = useState<Skill[]>(initialSkills)
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingSkill, setEditingSkill] = useState<Skill | null>(null)
  const [form, setForm] = useState({ name: '', category: '', description: '' })

  const categories = useMemo(() => [...new Set(skills.map((s) => s.category))], [skills])

  const filtered = useMemo(() => {
    return skills.filter((s) => {
      if (search && !s.name.includes(search) && !s.description.includes(search)) return false
      if (categoryFilter && s.category !== categoryFilter) return false
      return true
    })
  }, [skills, search, categoryFilter])

  const openCreate = () => {
    setEditingSkill(null)
    setForm({ name: '', category: '', description: '' })
    setModalOpen(true)
  }

  const openEdit = (skill: Skill) => {
    setEditingSkill(skill)
    setForm({ name: skill.name, category: skill.category, description: skill.description })
    setModalOpen(true)
  }

  const handleSave = () => {
    if (!form.name || !form.category) {
      message.warning('请填写名称和分类')
      return
    }
    if (editingSkill) {
      setSkills((prev) =>
        prev.map((s) => (s.id === editingSkill.id ? { ...s, ...form } : s)),
      )
      message.success('技能已更新')
    } else {
      const newSkill: Skill = {
        ...form,
        id: `sk-${Date.now()}`,
        status: 'draft',
        version: 'v0.1.0',
        updatedAt: new Date().toISOString().slice(0, 10),
      }
      setSkills((prev) => [...prev, newSkill])
      message.success('技能已创建')
    }
    setModalOpen(false)
  }

  const toggleStatus = (skill: Skill) => {
    const newStatus = skill.status === 'enabled' ? 'disabled' : 'enabled'
    setSkills((prev) => prev.map((s) => (s.id === skill.id ? { ...s, status: newStatus } : s)))
    message.success(newStatus === 'enabled' ? '技能已启用' : '技能已禁用')
  }

  const columns = [
    { title: '技能名称', dataIndex: 'name', key: 'name', width: 160 },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: (v: string) => <Tag>{v}</Tag>,
    },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (v: string) => <span className={`yx-status-badge ${STATUS_MAP[v]?.cls || v}`}>{STATUS_MAP[v]?.label || v}</span>,
    },
    { title: '版本', dataIndex: 'version', key: 'version', width: 90 },
    { title: '更新时间', dataIndex: 'updatedAt', key: 'updatedAt', width: 120 },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_: unknown, record: Skill) => (
        <div className="yx-table-action">
          <Button size="small" type="link" icon={<EditOutlined />} onClick={() => openEdit(record)}>
            编辑
          </Button>
          <Button
            size="small"
            type="link"
            onClick={() => toggleStatus(record)}
          >
            {record.status === 'enabled' ? '禁用' : '启用'}
          </Button>
        </div>
      ),
    },
  ]

  return (
    <div>
      <div className="yx-page-title">
        <h1 style={{ fontSize: 24, fontWeight: 700, color: colors.brandDark, marginBottom: 4 }}>技能管理</h1>
        <p style={{ color: colors.textMuted, margin: '4px 0 0', fontSize: 14 }}>管理平台的AI技能能力</p>
      </div>

      <div className="yx-toolbar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 12 }}>
          <Input
            className="yx-search-box"
            placeholder="搜索技能名称或描述"
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            allowClear
            style={{ width: 260 }}
          />
          <Select
            placeholder="按分类筛选"
            value={categoryFilter || undefined}
            onChange={(v) => setCategoryFilter(v || '')}
            allowClear
            style={{ width: 160 }}
            options={categories.map((c) => ({ label: c, value: c }))}
          />
        </div>
        <Button className="yx-btn yx-btn-primary" type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          新建技能
        </Button>
      </div>

      <Card style={{ borderRadius: radius.card }}>
        <Table
          dataSource={filtered}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title={editingSkill ? '编辑技能' : '新建技能'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleSave}
        okText="保存"
        cancelText="取消"
      >
        <div className="yx-form-row" style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>名称</label>
          <Input
            placeholder="请输入技能名称"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          />
        </div>
        <div className="yx-form-row" style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>分类</label>
          <Input
            placeholder="请输入分类名称"
            value={form.category}
            onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
          />
        </div>
        <div className="yx-form-row">
          <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>描述</label>
          <Input.TextArea
            placeholder="请输入技能描述"
            rows={3}
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
          />
        </div>
      </Modal>
    </div>
  )
}
