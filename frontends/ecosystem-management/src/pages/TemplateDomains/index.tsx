import React, { useState, useMemo } from 'react'
import { Card, Tag, Button, Input, Select, Modal, message } from 'antd'
import { PlusOutlined, EditOutlined, CopyOutlined, CloudUploadOutlined, SearchOutlined } from '@ant-design/icons'
import { colors, radius } from '@jonex/platform-theme/tokens'
import type { TemplateDomain } from '../../types/catalog'

const initialDomains: TemplateDomain[] = []

const STATUS_MAP: Record<string, { label: string; cls: string }> = {
  published: { label: '已发布', cls: 'active' },
  draft: { label: '草稿', cls: 'pending' },
}

export default function TemplateDomains() {
  const [domains, setDomains] = useState<TemplateDomain[]>(initialDomains)
  const [search, setSearch] = useState('')
  const [industryFilter, setIndustryFilter] = useState<string>('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingDomain, setEditingDomain] = useState<TemplateDomain | null>(null)
  const [form, setForm] = useState({ name: '', industry: '', description: '' })

  const industries = useMemo(() => [...new Set(domains.map((d) => d.industry))], [domains])

  const filtered = useMemo(() => {
    return domains.filter((d) => {
      if (search && !d.name.includes(search) && !d.description.includes(search)) return false
      if (industryFilter && d.industry !== industryFilter) return false
      return true
    })
  }, [domains, search, industryFilter])

  const openCreate = () => {
    setEditingDomain(null)
    setForm({ name: '', industry: '', description: '' })
    setModalOpen(true)
  }

  const openEdit = (domain: TemplateDomain) => {
    setEditingDomain(domain)
    setForm({ name: domain.name, industry: domain.industry, description: domain.description })
    setModalOpen(true)
  }

  const handleSave = () => {
    if (!form.name || !form.industry) {
      message.warning('请填写名称和行业')
      return
    }
    if (editingDomain) {
      setDomains((prev) =>
        prev.map((d) => (d.id === editingDomain.id ? { ...d, ...form } : d)),
      )
      message.success('领域模板已更新')
    } else {
      const newDomain: TemplateDomain = {
        ...form,
        id: `td-${Date.now()}`,
        usageCount: 0,
        status: 'draft',
        updatedAt: new Date().toISOString().slice(0, 10),
      }
      setDomains((prev) => [...prev, newDomain])
      message.success('领域模板已创建')
    }
    setModalOpen(false)
  }

  const handleCopy = (domain: TemplateDomain) => {
    const newDomain: TemplateDomain = {
      ...domain,
      id: `td-${Date.now()}`,
      name: `${domain.name} (副本)`,
      usageCount: 0,
      status: 'draft',
      updatedAt: new Date().toISOString().slice(0, 10),
    }
    setDomains((prev) => [...prev, newDomain])
    message.success('模板已复制')
  }

  const handlePublish = (domain: TemplateDomain) => {
    setDomains((prev) =>
      prev.map((d) => (d.id === domain.id ? { ...d, status: 'published' as const } : d)),
    )
    message.success('模板已发布')
  }

  return (
    <div>
      <div className="yx-page-title">
        <h1 style={{ fontSize: 24, fontWeight: 700, color: colors.brandDark, marginBottom: 4 }}>模板领域</h1>
        <p style={{ color: colors.textMuted, margin: '4px 0 0', fontSize: 14 }}>管理各行业领域的知识模板</p>
      </div>

      <div className="yx-toolbar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 12 }}>
          <Input
            className="yx-search-box"
            placeholder="搜索模板名称或描述"
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            allowClear
            style={{ width: 260 }}
          />
          <Select
            placeholder="按行业筛选"
            value={industryFilter || undefined}
            onChange={(v) => setIndustryFilter(v || '')}
            allowClear
            style={{ width: 160 }}
            options={industries.map((i) => ({ label: i, value: i }))}
          />
        </div>
        <Button className="yx-btn yx-btn-primary" type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          新建模板
        </Button>
      </div>

      {filtered.length === 0 ? (
        <div className="yx-empty-state" style={{ textAlign: 'center', padding: 60, color: colors.textMuted }}>
          暂无匹配的领域模板
        </div>
      ) : (
        <div className="yx-config-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 20 }}>
          {filtered.map((domain) => (
            <Card
              key={domain.id}
              className="yx-config-card"
              hoverable
              style={{ borderRadius: radius.card }}
              styles={{ body: { padding: 24 } }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600, color: colors.brandDark }}>{domain.name}</h3>
                <span className={`yx-status-badge ${STATUS_MAP[domain.status]?.cls || domain.status}`}>
                  {STATUS_MAP[domain.status]?.label || domain.status}
                </span>
              </div>
              <Tag style={{ marginBottom: 8 }}>{domain.industry}</Tag>
              <p style={{ fontSize: 13, color: colors.textSecondary, marginBottom: 12, lineHeight: 1.5 }}>{domain.description}</p>
              <div style={{ fontSize: 12, color: colors.textMuted, marginBottom: 12 }}>
                使用量: {domain.usageCount.toLocaleString()} 次 · 更新: {domain.updatedAt}
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(domain)}>编辑</Button>
                <Button size="small" icon={<CopyOutlined />} onClick={() => handleCopy(domain)}>复制</Button>
                {domain.status === 'draft' && (
                  <Button size="small" type="primary" icon={<CloudUploadOutlined />} onClick={() => handlePublish(domain)}>发布</Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal
        title={editingDomain ? '编辑领域模板' : '新建领域模板'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleSave}
        okText="保存"
        cancelText="取消"
      >
        <div className="yx-form-row" style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>名称</label>
          <Input
            placeholder="请输入模板名称"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          />
        </div>
        <div className="yx-form-row" style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>行业</label>
          <Input
            placeholder="请输入行业名称"
            value={form.industry}
            onChange={(e) => setForm((f) => ({ ...f, industry: e.target.value }))}
          />
        </div>
        <div className="yx-form-row">
          <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>描述</label>
          <Input.TextArea
            placeholder="请输入模板描述"
            rows={3}
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
          />
        </div>
      </Modal>
    </div>
  )
}
