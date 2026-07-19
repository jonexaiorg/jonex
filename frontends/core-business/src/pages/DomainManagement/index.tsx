import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { Input, Button, Table, Tag, Modal, Space, message, Result, Spin } from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  ReloadOutlined,
  GlobalOutlined,
  TeamOutlined,
  KeyOutlined,
  PlusCircleOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined,
  CheckOutlined,
  StopOutlined,
  CloseOutlined,
  UserAddOutlined,
} from '@ant-design/icons'
import { useSearchParams } from 'react-router-dom'
import { observer } from 'mobx-react-lite'
import { useStore } from '@/store'
import { SPACE_URL_PARAM } from '@jonex/shell-sdk'
import type { ColumnsType } from 'antd/es/table'
import {
  listServices, createService, updateService, deleteService,
  listServiceApiKeys, createServiceApiKey, deleteServiceApiKey,
  getServicePermissions, setServicePermissions,
} from '../../api/domainService'
import {
  SERVICE_STATUS_MAP,
  userToPermMember,
  type DomainServiceItem,
  type DomainServiceFormData,
  type KnowledgeBaseOption,
  type PermMember,
  type ServiceApiKeyItem,
} from '../../types/domainService'
import { listUsers, type PlatformUser } from '../../api/user'
import { getDomainKnowledgeList } from '../../api/domainKnowledge'
import type { DomainSpace } from '../../types/domainSpace'

export default observer(function DomainManagement() {
  const { t } = useTranslation('business')
  const { global } = useStore()
  const [searchParams, setSearchParams] = useSearchParams()

  const [services, setServices] = useState<DomainServiceItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [submitting, setSubmitting] = useState(false)


  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<DomainServiceItem | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<DomainServiceItem | null>(null)


  const [formName, setFormName] = useState('')
  const [formSpaceId, setFormSpaceId] = useState('')
  const [formStatus, setFormStatus] = useState(true)
  const [formKbIds, setFormKbIds] = useState<string[]>([])


  const [permOpen, setPermOpen] = useState(false)
  const [permTarget, setPermTarget] = useState<DomainServiceItem | null>(null)
  const [permSearch, setPermSearch] = useState('')
  const [permMembers, setPermMembers] = useState<PermMember[]>([])
  const [permLoading, setPermLoading] = useState(false)
  const [permSaving, setPermSaving] = useState(false)


  const [userSelectOpen, setUserSelectOpen] = useState(false)
  const [userSearchText, setUserSearchText] = useState('')
  const [availableUsers, setAvailableUsers] = useState<PlatformUser[]>([])
  const [usersLoading, setUsersLoading] = useState(false)
  const userSelectRef = useRef<HTMLDivElement>(null)


  const [srvConfigOpen, setSrvConfigOpen] = useState(false)
  const [srvConfigTarget, setSrvConfigTarget] = useState<DomainServiceItem | null>(null)
  const [apiKeys, setApiKeys] = useState<ServiceApiKeyItem[]>([])
  const [apiKeysLoading, setApiKeysLoading] = useState(false)
  const [creatingKey, setCreatingKey] = useState(false)
  const [copiedKeyId, setCopiedKeyId] = useState<string | null>(null)

  const spaceMap = new Map(global.spaces.map((s) => [s.id, s.name]))

  const kbNameMap = new Map<string, string>()
  services.forEach((s) => {
    s.kb_ids?.forEach((kid, i) => {
      if (!kbNameMap.has(kid) && s.kb_names?.[i]) {
        kbNameMap.set(kid, s.kb_names[i])
      }
    })
  })


  const loadServices = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await listServices(global.currentSpaceId || undefined, 0, 100)
      setServices(result.items)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('domainService.loadFailed'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    global.loadSpaces()
  }, [])


  useEffect(() => {
    const urlSpaceId = searchParams.get(SPACE_URL_PARAM)
    if (urlSpaceId && global.spaces.some((s) => s.id === urlSpaceId)) {
      global.setCurrentSpaceId(urlSpaceId, { persist: true, broadcast: false })
    }
  }, [])


  useEffect(() => {
    if (global.spacesLoaded) {
      loadServices()
      const urlSpaceId = searchParams.get(SPACE_URL_PARAM)
      if (global.currentSpaceId && global.currentSpaceId !== urlSpaceId) {
        setSearchParams(
          (prev) => {
            const next = new URLSearchParams(prev)
            next.set(SPACE_URL_PARAM, global.currentSpaceId!)
            return next
          },
          { replace: true },
        )
      }
    }
  }, [global.currentSpaceId, global.spacesLoaded])


  useEffect(() => {
    if (!userSelectOpen) return
    const handler = (e: MouseEvent) => {
      if (userSelectRef.current && !userSelectRef.current.contains(e.target as Node)) {
        setUserSelectOpen(false)
        setUserSearchText('')
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [userSelectOpen])


  const filtered = services.filter((s) => {
    if (search && !s.name.includes(search) && !(s.description || '').includes(search)) return false
    return true
  })


  const openCreate = () => {
    setEditing(null)
    setFormName('')
    setFormSpaceId('')
    setFormStatus(true)
    setFormKbIds([])
    setFormOpen(true)
  }

  const openEdit = (item: DomainServiceItem) => {
    setEditing(item)
    setFormName(item.name)
    setFormSpaceId(item.space_id)
    setFormStatus(item.status === 'active')
    setFormKbIds(item.kb_ids || [])
    setFormOpen(true)
  }

  const handleSave = async () => {
    if (!formName.trim()) { message.warning(t('domainService.nameRequired')); return }
    if (!formSpaceId) { message.warning(t('domainService.spaceRequired')); return }
    setSubmitting(true)
    try {
      const data: DomainServiceFormData = {
        name: formName.trim(),
        space_id: formSpaceId,
        status: formStatus ? 'active' : 'inactive',
        kb_ids: formKbIds,
      }
      if (editing) {
        await updateService(editing.id, data)
        message.success(t('domainService.updateSuccess'))
      } else {
        await createService(data)
        message.success(t('domainService.createSuccess'))
      }
      setFormOpen(false)
      await loadServices()
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('common.saveFailed'))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    setSubmitting(true)
    try {
      await deleteService(deleteTarget.id)
      message.success(t('domainService.deleteSuccess'))
      setDeleteTarget(null)
      await loadServices()
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('common.deleteFailed'))
    } finally {
      setSubmitting(false)
    }
  }

  const toggleServiceStatus = async (item: DomainServiceItem) => {
    const newStatus = item.status === 'active' ? 'inactive' : 'active'
    try {
      await updateService(item.id, { status: newStatus })
      setServices((prev) =>
        prev.map((s) => (s.id === item.id ? { ...s, status: newStatus } : s)),
      )
      message.success(newStatus === 'active' ? t('status.enabled') : t('status.disabled'))
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('common.operationFailed'))
    }
  }


  const openPermModal = async (item: DomainServiceItem) => {
    setPermTarget(item)
    setPermSearch('')
    setPermOpen(true)
    setPermLoading(true)
    setUserSelectOpen(false)
    setUserSearchText('')
    try {
      const result = await getServicePermissions(item.id)
      const perms = result?.permissions ?? []
      if (Array.isArray(perms) && perms.length > 0) {

        let userMap: Map<string, PlatformUser> = new Map()
        try {
          const userResult = await listUsers(1, 100)
          for (const u of userResult.items) {
            userMap.set(String(u.id), u)
          }
        } catch {   }
        const members: PermMember[] = perms.map((p) => {
          const uid = String(p.user_id)
          const user = userMap.get(uid)
          return user
            ? userToPermMember(user, (p.role === 'manager' ? 'manager' : 'viewer'))
            : {
                id: uid,
                name: t('domainService.unknownUser', { id: uid.slice(0, 8) }),
                department: '',
                avatar: uid.charAt(0).toUpperCase(),
                avatarColor: '#94a3b8',
                role: (p.role === 'manager' ? 'manager' : 'viewer') as 'viewer' | 'manager',
              }
        })
        setPermMembers(members)
      } else {
        setPermMembers([])
      }
    } catch {
      setPermMembers([])
    } finally {
      setPermLoading(false)
    }
  }

  const handlePermSave = async () => {
    if (!permTarget) return
    setPermSaving(true)
    try {
      const permissions = permMembers.map((m) => ({
        user_id: m.id,
        role: m.role,
      }))
      await setServicePermissions(permTarget.id, permissions)
      message.success(t('permission.saveSuccess'))
      setPermOpen(false)
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('common.saveFailed'))
    } finally {
      setPermSaving(false)
    }
  }

  const loadAvailableUsers = useCallback(async () => {
    setUsersLoading(true)
    try {
      const result = await listUsers(1, 100)
      setAvailableUsers(result.items)
    } catch {
      setAvailableUsers([])
    } finally {
      setUsersLoading(false)
    }
  }, [])

  const addPermMember = (user: PlatformUser) => {
    setPermMembers((prev) => {
      if (prev.some((m) => m.id === String(user.id))) return prev
      return [...prev, userToPermMember(user, 'viewer')]
    })
  }

  const removePermMember = (userId: string) => {
    setPermMembers((prev) => prev.filter((m) => m.id !== userId))
  }

  const filteredPermMembers = permMembers.filter((m) => {
    if (!permSearch) return true
    return m.name.includes(permSearch) || m.department.includes(permSearch)
  })


  const addedUserIds = new Set(permMembers.map((m) => m.id))
  const filteredAvailableUsers = availableUsers.filter((u) => {
    if (!userSearchText) return !addedUserIds.has(String(u.id))
    const q = userSearchText.toLowerCase()
    return (
      !addedUserIds.has(String(u.id)) &&
      ((u.display_name || '').toLowerCase().includes(q) ||
        u.username.toLowerCase().includes(q) ||
        (u.email || '').toLowerCase().includes(q))
    )
  })


  const openSrvConfig = async (item: DomainServiceItem) => {
    setSrvConfigTarget(item)
    setCopiedKeyId(null)
    setSrvConfigOpen(true)
    setApiKeysLoading(true)
    try {
      const result = await listServiceApiKeys(item.id)
      setApiKeys(result.items || [])
    } catch {
      setApiKeys([])
    } finally {
      setApiKeysLoading(false)
    }
  }

  const handleCopyKey = async (keyId: string, key: string) => {
    try {
      await navigator.clipboard.writeText(key)
      setCopiedKeyId(keyId)
      setTimeout(() => setCopiedKeyId(null), 2000)
    } catch {
      const ta = document.createElement('textarea')
      ta.value = key
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      setCopiedKeyId(keyId)
      setTimeout(() => setCopiedKeyId(null), 2000)
    }
  }

  const handleCreateKey = async () => {
    if (!srvConfigTarget) return
    setCreatingKey(true)
    try {
      const newKey = await createServiceApiKey(srvConfigTarget.id, { expires_in_days: 365 })
      setApiKeys((prev) => [newKey, ...prev])
      message.success(t('domainService.apiKeyCreated'))
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('common.createFailed'))
    } finally {
      setCreatingKey(false)
    }
  }

  const handleDeleteKey = async (keyId: string) => {
    if (!srvConfigTarget) return
    Modal.confirm({
      title: t('domainService.deleteApiKeyTitle'),
      content: t('domainService.deleteApiKeyConfirm'),
      okText: t('domainService.confirmDelete'),
      okType: 'danger',
      cancelText: t('domainService.cancel'),
      onOk: async () => {
        await deleteServiceApiKey(srvConfigTarget.id, keyId)
        setApiKeys((prev) => prev.filter((k) => k.id !== keyId))
        message.success(t('domainService.apiKeyDeleted'))
      },
    })
  }

  const formatDate = (dateStr: string | null): string => {
    if (!dateStr) return '—'
    try {
      return new Date(dateStr).toISOString().slice(0, 10)
    } catch {
      return dateStr
    }
  }


  const [availableKbs, setAvailableKbs] = useState<KnowledgeBaseOption[]>([])

  useEffect(() => {

    getDomainKnowledgeList({ page: 1, pageSize: 100 })
      .then((result) => {
        if (result.list && result.list.length > 0) {
          setAvailableKbs(result.list.map((kb) => ({ id: kb.id, name: kb.name })))
        }
      })
      .catch(() => {   })
  }, [])
  const toggleKb = (kbId: string) => {
    setFormKbIds((prev) =>
      prev.includes(kbId) ? prev.filter((id) => id !== kbId) : [...prev, kbId],
    )
  }


  const columns: ColumnsType<DomainServiceItem> = [
    {
      title: t('domainService.serviceName'),
      dataIndex: 'name',
      key: 'name',
      width: 140,
      render: (v: string) => (
        <span
          className="yx-domain-name"
          onClick={() => { }}
        >
          {v}
        </span>
      ),
    },
    {
      title: t('domainService.space'),
      dataIndex: 'space_id',
      key: 'space',
      width: 140,
      render: (id: string) => spaceMap.get(id) || id,
    },
    {
      title: t('domainService.relatedKnowledgeBases'),
      key: 'kbs',
      width: 240,
      render: (_: unknown, r: DomainServiceItem) => (
        <div className="yx-kb-tags">
          {r.kb_ids && r.kb_ids.length > 0
            ? r.kb_ids.map((kbId) => (
                <span key={kbId} className="yx-kb-tag">
                  {kbNameMap.get(kbId) || kbId}
                </span>
              ))
            : <span className="yx-kb-tag">—</span>}
        </div>
      ),
    },












    {
      title: t('domainService.status'),
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (v: string, r: DomainServiceItem) => {
        const cfg = SERVICE_STATUS_MAP[v]
        if (!cfg) return <Tag>{v}</Tag>
        return (
          <Tag
            color={v === 'active' ? 'success' : v === 'testing' ? 'warning' : 'error'}
            style={{ cursor: 'pointer' }}
            onClick={() => toggleServiceStatus(r)}
          >
            {t(cfg.label)}
          </Tag>
        )
      },
    },
    {
      title: t('domainService.actions'),
      key: 'actions',
      width: 240,
      render: (_: unknown, r: DomainServiceItem) => {
        const isActive = r.status === 'active'
        return (
          <Space>
            <a
              className="yx-table-action"
              onClick={() => toggleServiceStatus(r)}
            >
              {t(isActive ? 'domainService.deactivate' : 'domainService.activate')}
            </a>
            { }
            {

}
            <a className="yx-table-action" onClick={() => openEdit(r)}>
              {t('domainService.edit')}
            </a>
            <a
              className="yx-table-action"
              style={{ color: '#dc2626' }}
              onClick={() => setDeleteTarget(r)}
            >
              {t('domainService.delete')}
            </a>
          </Space>
        )
      },
    },
  ]


  if (loading && services.length === 0) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (error) {
    return (
      <Result
        status="error"
        title={t('domainService.loadFailed')}
        subTitle={error}
        extra={
          <Button type="primary" icon={<ReloadOutlined />} onClick={() => loadServices()}>
            {t('domainService.retry')}
          </Button>
        }
      />
    )
  }

  const spaceOptions = global.spaces.filter((s: DomainSpace) => s.status === 'active')

  return (
    <div className="yx-domain-management-page">
      { }
      <div className="yx-page-header">
        <h1 className="yx-page-title">{t('domainService.title')}</h1>
        <p className="yx-page-desc">
          {t('domainService.pageDescription')}
        </p>
      </div>

      { }
      <div className="yx-filter-row">
        <label>
          <GlobalOutlined style={{ color: '#3b82f6' }} /> {t('domainService.space')}:
        </label>
        <select
          className="yx-filter-select"
          disabled
          value={global.currentSpaceId || ''}
        >
          <option value="">{t('domainService.allSpaces')}</option>
          {spaceOptions.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
        <span className="yx-filter-count">{t('domainService.domainCount', { count: filtered.length })}</span>
      </div>

      { }
      <div className="yx-card">
        <div className="yx-toolbar">
          <div className="yx-search-box">
            <SearchOutlined style={{ color: '#94a3b8', fontSize: 14 }} />
            <input
              type="text"
              placeholder={t('domainService.searchPlaceholder')}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            {t('domainService.create')}
          </Button>
        </div>

        <Table<DomainServiceItem>
          columns={columns}
          dataSource={filtered}
          rowKey="id"
          pagination={{
            total: filtered.length,
            pageSize: 10,
            showTotal: (total, range) => t('domainService.totalRange', { total, start: range[0], end: range[1] }),
          }}
          size="middle"
          locale={{ emptyText: t('domainService.empty') }}
        />
      </div>

      { }
      <Modal
        wrapClassName="yx-domain-space-modal"
        title={
          <span>
            {editing ? (
              <EditOutlined style={{ color: '#3b82f6', marginRight: 8 }} />
            ) : (
              <PlusCircleOutlined style={{ color: '#3b82f6', marginRight: 8 }} />
            )}
            {t(editing ? 'domainService.edit' : 'domainService.create')}
          </span>
        }
        open={formOpen}
        onCancel={() => setFormOpen(false)}
        onOk={handleSave}
        confirmLoading={submitting}
        okText={t(editing ? 'domainService.save' : 'domainService.createAction')}
        cancelText={t('domainService.cancel')}
        width={600}
        destroyOnHidden
      >
        <div className="yx-form-row">
          <label>
            {t('domainService.name')} <span style={{ color: '#ef4444' }}>*</span>
          </label>
          <input
            type="text"
            className="yx-form-input"
            placeholder={t('domainService.namePlaceholder')}
            value={formName}
            onChange={(e) => setFormName(e.target.value)}
          />
        </div>
        <div className="yx-form-row">
          <label>
            {t('domainService.space')} <span style={{ color: '#ef4444' }}>*</span>
          </label>
          <select
            className="yx-form-select"
            value={formSpaceId}
            onChange={(e) => setFormSpaceId(e.target.value)}
          >
            <option value="">{t('domainService.selectSpace')}</option>
            {spaceOptions.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
        <div className="yx-form-row">
          <label>{t('domainService.relatedKnowledgeBases')}</label>
          <div className="yx-kb-check-list">
            {availableKbs.map((kb) => (
              <label key={kb.id} className="yx-kb-check-item">
                <input
                  type="checkbox"
                  checked={formKbIds.includes(kb.id)}
                  onChange={() => toggleKb(kb.id)}
                />
                {kb.name}
              </label>
            ))}
          </div>
          <div className="yx-form-hint">
            {t('domainService.relatedKnowledgeBasesHint')}
          </div>
        </div>
        <div className="yx-form-row">
          <label>{t('domainService.status')}</label>
          <div className="yx-switch-wrap">
            <label className="yx-switch-label">
              <input
                type="checkbox"
                checked={formStatus}
                onChange={(e) => setFormStatus(e.target.checked)}
              />
              <span className="yx-switch-slider" />
            </label>
            <span className="yx-switch-text">{t(formStatus ? 'domainService.enabled' : 'domainService.disabled')}</span>
          </div>
        </div>
      </Modal>

      { }
      <Modal
        wrapClassName="yx-domain-space-modal"
        title={
          <span>
            <StopOutlined style={{ color: '#ef4444', marginRight: 8 }} />
            {t('domainService.confirmDelete')}
          </span>
        }
        open={!!deleteTarget}
        onCancel={() => setDeleteTarget(null)}
        footer={
          <div style={{ display: 'flex', justifyContent: 'center', gap: 12 }}>
            <Button onClick={() => setDeleteTarget(null)}>{t('domainService.cancel')}</Button>
            <Button
              danger
              type="primary"
              loading={submitting}
              onClick={handleDelete}
            >
              {t('domainService.confirmDelete')}
            </Button>
          </div>
        }
        width={420}
      >
        <div style={{ textAlign: 'center', padding: '12px 0' }}>
          <DeleteOutlined style={{ fontSize: 48, color: '#ef4444', marginBottom: 16, display: 'block' }} />
          <p style={{ fontSize: 16, color: '#1e293b', fontWeight: 500 }}>
            {t('domainService.deleteConfirm', { name: deleteTarget?.name ?? '' })}
          </p>
          <p style={{ fontSize: 13, color: '#94a3b8', marginTop: 8 }}>
            {t('domainService.deleteWarning')}
          </p>
        </div>
      </Modal>

      { }
      <Modal
        wrapClassName="yx-domain-space-modal"
        title={
          <span>
            <TeamOutlined style={{ color: '#3b82f6', marginRight: 8 }} />
            {t('domainService.permissionTitle')}
          </span>
        }
        open={permOpen}
        onCancel={() => { setPermOpen(false); setUserSelectOpen(false) }}
        onOk={handlePermSave}
        confirmLoading={permSaving}
        okText={t('domainService.savePermission')}
        cancelText={t('domainService.cancel')}
        width={600}
      >
        <p style={{ fontSize: 14, color: '#475569', marginBottom: 12 }}>
          {t('domainService.permissionDescription', { name: permTarget?.name ?? '' })}
        </p>

        { }
        <div ref={userSelectRef} style={{ position: 'relative', marginBottom: 12 }}>
          <Button
            icon={<UserAddOutlined />}
            onClick={() => {
              const willOpen = !userSelectOpen
              setUserSelectOpen(willOpen)
              setUserSearchText('')
              if (willOpen && availableUsers.length === 0) loadAvailableUsers()
            }}
            style={{ marginBottom: userSelectOpen ? 8 : 0 }}
          >
            {t('domainService.addMember')}
          </Button>
          {userSelectOpen && (
            <div
              style={{
                position: 'absolute', top: 38, left: 0, zIndex: 10,
                width: 320, background: '#fff', borderRadius: 8,
                boxShadow: '0 4px 20px rgba(0,0,0,.12)', border: '1px solid #e2e8f0',
                overflow: 'hidden',
              }}
            >
              <div style={{ padding: '8px 12px', borderBottom: '1px solid #e2e8f0' }}>
                <Input
                  size="small"
                  placeholder={t('domainService.searchUsers')}
                  prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
                  value={userSearchText}
                  onChange={(e) => setUserSearchText(e.target.value)}
                  allowClear
                />
              </div>
              <div style={{ maxHeight: 220, overflowY: 'auto' }}>
                {usersLoading ? (
                  <div style={{ textAlign: 'center', padding: 20 }}><Spin size="small" /></div>
                ) : filteredAvailableUsers.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: 20, color: '#94a3b8', fontSize: 13 }}>
                    {t(userSearchText ? 'domainService.noMatchingUsers' : 'domainService.noAvailableUsers')}
                  </div>
                ) : (
                  filteredAvailableUsers.slice(0, 30).map((user) => (
                    <div
                      key={user.id}
                      className="yx-perm-user-row"
                      style={{ cursor: 'pointer', padding: '8px 12px' }}
                      onClick={() => { addPermMember(user); setUserSearchText('') }}
                    >
                      <div
                        className="yx-perm-avatar"
                        style={{ background: userToPermMember(user).avatarColor }}
                      >
                        {userToPermMember(user).avatar}
                      </div>
                      <div className="yx-perm-user-info" style={{ flex: 1 }}>
                        <div className="yx-perm-user-name">
                          {user.display_name || user.username}
                        </div>
                        <div className="yx-perm-user-dept">
                          {user.email || user.role || ''}
                        </div>
                      </div>
                      <span style={{ fontSize: 20, color: '#3b82f6', lineHeight: 1 }}>+</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        { }
        <div className="yx-search-box" style={{ width: '100%', marginBottom: 12 }}>
          <SearchOutlined style={{ color: '#94a3b8', fontSize: 14 }} />
          <input
            type="text"
            placeholder={t('domainService.searchAddedMembers')}
            value={permSearch}
            onChange={(e) => setPermSearch(e.target.value)}
            style={{ width: '100%' }}
          />
        </div>

        { }
        <div style={{ maxHeight: 280, overflowY: 'auto' }}>
          {permLoading ? (
            <div style={{ textAlign: 'center', padding: 24 }}><Spin /></div>
          ) : filteredPermMembers.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 24, color: '#94a3b8', fontSize: 13 }}>
              {t(permSearch ? 'domainService.noMatchingMembers' : 'domainService.noPermissionMembers')}
            </div>
          ) : (
            filteredPermMembers.map((member) => (
              <div key={member.id} className="yx-perm-user-row">
                <div className="yx-perm-avatar" style={{ background: member.avatarColor }}>
                  {member.avatar}
                </div>
                <div className="yx-perm-user-info" style={{ flex: 1 }}>
                  <div className="yx-perm-user-name">{member.name}</div>
                  <div className="yx-perm-user-dept">{member.department || `ID: ${member.id.slice(0, 8)}`}</div>
                </div>
                <div className="yx-perm-radio">
                  <label
                    className={`yx-perm-radio-label${member.role === 'viewer' ? ' is-checked' : ''}`}
                  >
                    <input
                      type="radio"
                      name={`perm-${member.id}`}
                      value="viewer"
                      checked={member.role === 'viewer'}
                      onChange={() => {
                        setPermMembers((prev) =>
                          prev.map((m) => (m.id === member.id ? { ...m, role: 'viewer' as const } : m)),
                        )
                      }}
                    />
                    {t('domainService.viewer')}
                  </label>
                  <label
                    className={`yx-perm-radio-label${member.role === 'manager' ? ' is-checked' : ''}`}
                  >
                    <input
                      type="radio"
                      name={`perm-${member.id}`}
                      value="manager"
                      checked={member.role === 'manager'}
                      onChange={() => {
                        setPermMembers((prev) =>
                          prev.map((m) => (m.id === member.id ? { ...m, role: 'manager' as const } : m)),
                        )
                      }}
                    />
                    {t('domainService.manager')}
                  </label>
                </div>
                <button
                  type="button"
                  className="yx-perm-remove-btn"
                  onClick={() => removePermMember(member.id)}
                  title={t('domainService.removeMember')}
                  style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: '#94a3b8', fontSize: 16, padding: '0 0 0 8px',
                    lineHeight: 1,
                  }}
                >
                  <CloseOutlined />
                </button>
              </div>
            ))
          )}
        </div>
      </Modal>

      { }
      <Modal
        wrapClassName="yx-domain-space-modal"
        title={
          <span>
            <KeyOutlined style={{ color: '#f97316', marginRight: 8 }} />
            {t('domainService.serviceConfig')}
          </span>
        }
        open={srvConfigOpen}
        onCancel={() => setSrvConfigOpen(false)}
        footer={
          <Button onClick={() => setSrvConfigOpen(false)}>{t('domainService.close')}</Button>
        }
        width={760}
      >
        <p style={{ fontSize: 14, color: '#475569', marginBottom: 16 }}>
          {t('domainService.apiKeyDescription', { name: srvConfigTarget?.name ?? '' })}
        </p>
        <div style={{ textAlign: 'right', marginBottom: 12 }}>
          <Button
            type="primary"
            size="small"
            icon={<PlusOutlined />}
            loading={creatingKey}
            onClick={handleCreateKey}
          >
            {t('domainService.addApiKey')}
          </Button>
        </div>
        {apiKeysLoading ? (
          <div style={{ textAlign: 'center', padding: 24 }}><Spin /></div>
        ) : (
          <table className="yx-srv-table">
            <thead>
              <tr>
                <th style={{ minWidth: 240 }}>API Key</th>
                <th>{t('domainService.expiresAt')}</th>
                <th>{t('domainService.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {apiKeys.length === 0 ? (
                <tr>
                  <td colSpan={3} style={{ textAlign: 'center', color: '#94a3b8', padding: 24 }}>
                    {t('domainService.emptyApiKeys')}
                  </td>
                </tr>
              ) : (
                apiKeys.map((key) => (
                  <tr key={key.id}>
                    <td>
                      <span className="yx-key-text">
                        {key.key_encrypted || '—'}
                      </span>
                      {key.key_encrypted && (
                        <button
                          className={`yx-copy-btn${copiedKeyId === key.id ? ' copied' : ''}`}
                          title={t(copiedKeyId === key.id ? 'domainService.copied' : 'domainService.copyApiKey')}
                          onClick={() => handleCopyKey(key.id, key.key_encrypted)}
                        >
                          {copiedKeyId === key.id ? <CheckOutlined /> : <CopyOutlined />}
                        </button>
                      )}
                    </td>
                    <td>{formatDate(key.expires_at)}</td>
                    <td>
                      <div className="yx-srv-actions">
                        <button
                          className="danger"
                          onClick={() => handleDeleteKey(key.id)}
                        >
                          <DeleteOutlined /> {t('domainService.delete')}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </Modal>
    </div>
  )
})
