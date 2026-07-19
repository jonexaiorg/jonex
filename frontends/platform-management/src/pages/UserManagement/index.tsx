import React, { useState, useEffect, useCallback } from 'react'
import { Input, Button, Table, Tag, Modal, Select, message, Spin, Result } from 'antd'
import { useTranslation } from 'react-i18next'
import { SearchOutlined, PlusOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import {
  listAllUsers, listUsers, createUser, updateUser, deleteUser,
  type UserItem, type UserCreatePayload, type UserUpdatePayload,
  getRoleLabel, getUserStatus,
} from '../../api/users'
import { listTenants, getTenantUserCounts, type TenantItem } from '../../api/tenants'
import './index.css'

export default function UserManagement() {
  const { t } = useTranslation()
  const [users, setUsers] = useState<UserItem[]>([])
  const [tenants, setTenants] = useState<(TenantItem & { userCount: number })[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('')
  const [activeTenant, setActiveTenant] = useState('all')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<UserItem | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [toggleTarget, setToggleTarget] = useState<UserItem | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<UserItem | null>(null)
  const [form, setForm] = useState({ username: '', password: '', display_name: '', email: '', role: 'user', tenant_id: '' })

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const [ur, tr, counts] = await Promise.all([listAllUsers(), listTenants(1, 100), getTenantUserCounts()])
      setUsers(ur.items)
      setTenants(tr.items.map(t => ({ ...t, userCount: counts[t.id] || 0 })))
    } catch (e: unknown) { setError(e instanceof Error ? e.message : t('common.loadFailed')) }
    finally { setLoading(false) }
  }, [t])

  useEffect(() => { load() }, [load])

  const filtered = users.filter(u => {
    if (activeTenant !== 'all' && u.tenant_id !== activeTenant) return false
    if (roleFilter && u.role !== roleFilter) return false
    if (search) {
      const q = search.toLowerCase()
      if (!u.username.includes(q) && !(u.display_name || '').includes(q) && !(u.email || '').includes(q)) return false
    }
    return true
  })

  const openCreate = () => {
    setEditing(null)
    setForm({ username: '', password: '', display_name: '', email: '', role: 'user', tenant_id: tenants[0]?.id || '' })
    setModalOpen(true)
  }

  const openEdit = (u: UserItem) => {
    setEditing(u)
    setForm({ username: u.username, password: '', display_name: u.display_name || '', email: u.email || '', role: u.role, tenant_id: u.tenant_id })
    setModalOpen(true)
  }

  const handleSave = async () => {
    if (!editing && !form.username) { message.warning(t('userManagement.nameRequired')); return }
    if (!editing && !form.password) { message.warning(t('userManagement.passwordRequired')); return }
    setSubmitting(true)
    try {
      if (editing) {
        const payload: UserUpdatePayload = { display_name: form.display_name, email: form.email, role: form.role }
        await updateUser(editing.id, payload); message.success(t('common.updatedSuccess'))
      } else {
        const payload: UserCreatePayload = { username: form.username, password: form.password, display_name: form.display_name, email: form.email, role: form.role }
        await createUser(payload); message.success(t('common.createdSuccess'))
      }
      setModalOpen(false); await load()
    } catch (e: unknown) { message.error(e instanceof Error ? e.message : t('common.saveFailed')) }
    finally { setSubmitting(false) }
  }

  const handleToggle = async () => {
    if (!toggleTarget) return
    const newStatus = toggleTarget.status === 1 ? 0 : 1
    try {
      await updateUser(toggleTarget.id, { status: newStatus })
      message.success(newStatus === 1 ? t('userManagement.enableSuccess') : t('userManagement.disableSuccess'))
      setToggleTarget(null); await load()
    } catch { message.error(t('common.operationFailed')) }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    try {
      await deleteUser(deleteTarget.id)
      message.success(t('common.deletedSuccess'))
      setDeleteTarget(null); await load()
    } catch { message.error(t('common.deleteFailed')) }
  }

  const columns = [
    { title: t('userManagement.username'), dataIndex: 'username', key: 'username', width: 120 },
    { title: t('userManagement.realName'), dataIndex: 'display_name', key: 'display_name', width: 100 },
    { title: t('userManagement.email'), dataIndex: 'email', key: 'email' },
    { title: t('userManagement.role'), dataIndex: 'role', key: 'role', width: 120, render: (v: string) => t(getRoleLabel(v)) },
    { title: t('userManagement.status'), dataIndex: 'status', key: 'status', width: 70, render: (v: number) => { const s = getUserStatus(v); return <Tag color={s.color}>{t(s.label)}</Tag> } },
    {
      title: t('userManagement.actions'), key: 'actions', width: 200,
      render: (_: unknown, r: UserItem) => (
        <span>
          <a className="yx-table-action" onClick={() => openEdit(r)}>{t('userManagement.edit')}</a>
          <a className="yx-table-action" style={{ marginLeft: 8 }} onClick={() => setToggleTarget(r)}>
            {r.status === 1 ? t('common.disable') : t('common.enable')}
          </a>
          <a className="yx-table-action" style={{ marginLeft: 8, color: '#dc2626' }} onClick={() => setDeleteTarget(r)}>{t('userManagement.delete')}</a>
        </span>
      ),
    },
  ]

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', minHeight: 300, alignItems: 'center' }}><Spin size="large" /></div>
  if (error) return <Result status="error" title={t('common.loadFailed')} subTitle={error} extra={<Button type="primary" onClick={load}>{t('common.retry', '重试')}</Button>} />

  return (
    <div>
      <div className="yx-page-title"><h1>{t('userManagement.title')}</h1></div>

      <div className="user-layout">
        { }
        <div className="tenant-panel">
          <div className="tenant-panel-header">{t('tenantManagement.title')}</div>
          <div className="tenant-list">
            <div className={`tenant-item${activeTenant === 'all' ? ' active' : ''}`} onClick={() => setActiveTenant('all')}>
              <span>{t('userManagement.allTenants', '全部租户')}</span>
              <span className="tenant-count">{users.length}</span>
            </div>
            {tenants.map(t => (
              <div key={t.id} className={`tenant-item${activeTenant === t.id ? ' active' : ''}`} onClick={() => setActiveTenant(t.id)}>
                <span>{t.name}</span>
                <span className="tenant-count">{t.userCount}</span>
              </div>
            ))}
          </div>
        </div>

        { }
        <div className="user-main">
          <div className="yx-card">
            <div className="yx-toolbar">
              <Input prefix={<SearchOutlined />} placeholder={t('userManagement.searchPlaceholder', '搜索用户...')} style={{ width: 200 }} value={search} onChange={e => setSearch(e.target.value)} allowClear />
              <Select placeholder={t('userManagement.allRoles', '全部角色')} style={{ width: 140 }} value={roleFilter || undefined} onChange={v => setRoleFilter(v || '')} allowClear
                options={[{ label: t(getRoleLabel('admin')), value: 'admin' }, { label: t(getRoleLabel('user')), value: 'user' }]} />
              <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>{t('userManagement.create')}</Button>
            </div>
            <Table columns={columns} dataSource={filtered} rowKey="id" pagination={{ total: filtered.length, pageSize: 10, showTotal: (n) => t('common.totalPage', { total: n }) }} size="middle" />
          </div>
        </div>
      </div>

      { }
      <Modal title={editing ? t('userManagement.edit') : t('userManagement.create')} open={modalOpen} onCancel={() => setModalOpen(false)} onOk={handleSave} okText={t('common.save')} cancelText={t('common.cancel')} confirmLoading={submitting} width={520}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 14 }}>
          <div>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: 13 }}>{t('userManagement.username')} <span style={{ color: '#dc2626' }}>*</span></label>
            <Input placeholder={t('userManagement.nameRequired')} value={form.username} disabled={!!editing} onChange={e => setForm(f => ({ ...f, username: e.target.value }))} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: 13 }}>{t('userManagement.realName')} <span style={{ color: '#dc2626' }}>*</span></label>
            <Input placeholder={t('userManagement.realName')} value={form.display_name} onChange={e => setForm(f => ({ ...f, display_name: e.target.value }))} />
          </div>
        </div>
        <div style={{ marginBottom: 14 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: 13 }}>{t('userManagement.email')} <span style={{ color: '#dc2626' }}>*</span></label>
          <Input placeholder={t('userManagement.emailRequired')} value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} />
        </div>
        <div style={{ marginBottom: 14 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: 13 }}>{t('userManagement.role')} <span style={{ color: '#dc2626' }}>*</span></label>
          <Select value={form.role} onChange={v => setForm(f => ({ ...f, role: v }))} style={{ width: '100%' }}
            options={[{ label: t(getRoleLabel('admin')), value: 'admin' }, { label: t(getRoleLabel('user')), value: 'user' }]} />
        </div>
        {!editing && <div style={{ marginTop: 14 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: 13 }}>{t('userManagement.passwordRequired')} <span style={{ color: '#dc2626' }}>*</span></label>
          <Input.Password placeholder={t('userManagement.passwordRequired')} value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} />
        </div>}
        {editing && <div style={{ marginTop: 14 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: 13 }}>{t('userManagement.resetPassword')}（{t('userManagement.leaveBlank', '留空不修改')}）</label>
          <Input.Password placeholder={t('userManagement.leaveBlank', '留空不修改密码')} value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} />
        </div>}
      </Modal>

      { }
      <Modal
        open={!!toggleTarget} onCancel={() => setToggleTarget(null)} onOk={handleToggle}
        okText={toggleTarget?.status === 1 ? t('userManagement.confirmDisable', '确认停用') : t('userManagement.confirmEnable', '确认启用')} cancelText={t('common.cancel')} width={380}
      >
        <div style={{ textAlign: 'center', padding: '8px 0' }}>
          <div style={{ fontSize: 40, marginBottom: 12, color: toggleTarget?.status === 1 ? '#f59e0b' : '#10b981' }}>
            <ExclamationCircleOutlined />
          </div>
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>{toggleTarget?.display_name || toggleTarget?.username}</div>
          <p style={{ color: '#64748b', margin: 0 }}>
            {toggleTarget?.status === 1 ? t('userManagement.disableConfirmMsg', '确认将该用户停用？停用后将无法登录平台。') : t('userManagement.enableConfirmMsg', '确认将该用户启用？启用后将恢复平台访问。')}
          </p>
        </div>
      </Modal>

      { }
      <Modal
        open={!!deleteTarget} onCancel={() => setDeleteTarget(null)} onOk={handleDelete}
        okText={t('rules.confirmDelete')} cancelText={t('common.cancel')} okButtonProps={{ danger: true }} width={380}
      >
        <div style={{ textAlign: 'center', padding: '8px 0' }}>
          <div style={{ fontSize: 40, marginBottom: 12, color: '#dc2626' }}><ExclamationCircleOutlined /></div>
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>{deleteTarget?.display_name || deleteTarget?.username}</div>
          <p style={{ color: '#64748b', margin: 0 }}>{t('userManagement.confirmDelete')}</p>
        </div>
      </Modal>
    </div>
  )
}