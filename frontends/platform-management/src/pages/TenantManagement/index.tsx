import React, { useState, useEffect, useCallback } from 'react'
import { Input, Button, Table, Tag, Modal, message, Spin, Result, Select } from 'antd'
import { useTranslation } from 'react-i18next'
import { SearchOutlined, PlusOutlined, EditOutlined } from '@ant-design/icons'
import {
  listTenants, createTenant, updateTenant, deleteTenant,
  type TenantItem, type TenantCreatePayload, type TenantUpdatePayload,
  getPlanTypeLabel, getStatusLabel,
} from '../../api/tenants'

export default function TenantManagement() {
  const { t } = useTranslation()
  const [tenants, setTenants] = useState<TenantItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<TenantItem | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState({ id: '', name: '', description: '', plan_type: 'free' })

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try { const r = await listTenants(); setTenants(r.items) }
    catch (e: unknown) { setError(e instanceof Error ? e.message : t('common.loadFailed')) }
    finally { setLoading(false) }
  }, [t])

  useEffect(() => { load() }, [load])

  const filtered = tenants.filter(t => !search || t.name.includes(search) || t.id.includes(search))

  const openCreate = () => { setEditing(null); setForm({ id: '', name: '', description: '', plan_type: 'free' }); setModalOpen(true) }
  const openEdit = (t: TenantItem) => { setEditing(t); setForm({ id: t.id, name: t.name, description: t.description || '', plan_type: t.plan_type }); setModalOpen(true) }

  const handleSave = async () => {
    if (!form.id && !editing) { message.warning(t('tenantManagement.codeRequired')); return }
    if (!form.name) { message.warning(t('tenantManagement.nameRequired')); return }
    setSubmitting(true)
    try {
      if (editing) {
        const payload: TenantUpdatePayload = { name: form.name, description: form.description, plan_type: form.plan_type }
        await updateTenant(editing.id, payload); message.success(t('common.updatedSuccess'))
      } else {
        const payload: TenantCreatePayload = { id: form.id, name: form.name, description: form.description, plan_type: form.plan_type }
        await createTenant(payload); message.success(t('common.createdSuccess'))
      }
      setModalOpen(false); await load()
    } catch (e: unknown) { message.error(e instanceof Error ? e.message : t('common.saveFailed')) }
    finally { setSubmitting(false) }
  }

  const columns = [
    { title: t('tenantManagement.tenantCode'), dataIndex: 'id', key: 'id', width: 180 },
    { title: t('tenantManagement.tenantName'), dataIndex: 'name', key: 'name', render: (v: string) => <a className="yx-table-action">{v}</a> },
    { title: t('tenantManagement.description'), dataIndex: 'description', key: 'description', ellipsis: true },
    { title: t('tenantManagement.planType', '版本'), dataIndex: 'plan_type', key: 'plan_type', width: 80, render: (v: string) => t(getPlanTypeLabel(v)) },
    { title: t('tenantManagement.status'), dataIndex: 'status', key: 'status', width: 80, render: (v: number) => { const s = getStatusLabel(v); return <Tag color={s.color}>{t(s.label)}</Tag> } },
    { title: t('common.actions', '操作'), key: 'actions', width: 100, render: (_: unknown, r: TenantItem) => <a className="yx-table-action" onClick={() => openEdit(r)}><EditOutlined /> {t('tenantManagement.edit')}</a> },
  ]

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', minHeight: 300, alignItems: 'center' }}><Spin size="large" /></div>
  if (error) return <Result status="error" title={t('common.loadFailed')} subTitle={error} extra={<Button type="primary" onClick={load}>{t('common.retry', '重试')}</Button>} />

  return (
    <div>
      <div className="yx-page-title"><h1>{t('tenantManagement.title')}</h1></div>
      <div className="yx-card">
        <div className="yx-toolbar">
          <Input prefix={<SearchOutlined />} placeholder={t('tenantManagement.searchPlaceholder', '搜索租户...')} style={{ width: 240 }} value={search} onChange={e => setSearch(e.target.value)} allowClear />
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>{t('tenantManagement.create')}</Button>
        </div>
        <Table columns={columns} dataSource={filtered} rowKey="id" pagination={{ total: filtered.length, pageSize: 10 }} size="middle" />
      </div>

      <Modal title={editing ? t('tenantManagement.edit') : t('tenantManagement.create')} open={modalOpen} onCancel={() => setModalOpen(false)} onOk={handleSave} okText={t('common.save')} cancelText={t('common.cancel')} confirmLoading={submitting} width={480}>
        {!editing && (
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>{t('tenantManagement.tenantCode')} <span style={{ color: '#dc2626' }}>*</span></label>
            <Input placeholder={t('tenantManagement.codeRequired')} value={form.id} onChange={e => setForm(f => ({ ...f, id: e.target.value }))} />
          </div>
        )}
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>{t('tenantManagement.tenantName')} <span style={{ color: '#dc2626' }}>*</span></label>
          <Input placeholder={t('tenantManagement.nameRequired')} value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
        </div>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>{t('tenantManagement.description')}</label>
          <Input placeholder={t('tenantManagement.description')} value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>{t('tenantManagement.planType', '版本')}</label>
          <Select value={form.plan_type} onChange={v => setForm(f => ({ ...f, plan_type: v }))} style={{ width: '100%' }} options={[
            { label: t('tenantManagement.free', '免费版'), value: 'free' }, { label: t('tenantManagement.pro', '专业版'), value: 'pro' }, { label: t('tenantManagement.enterprise', '企业版'), value: 'enterprise' },
          ]} />
        </div>
      </Modal>
    </div>
  )
}