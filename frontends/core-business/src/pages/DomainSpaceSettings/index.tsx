import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams, useNavigate } from 'react-router-dom'
import { observer } from 'mobx-react-lite'
import { Input, Button, Spin, Result, message, Modal } from 'antd'
import {
  SaveOutlined,
  TeamOutlined,
  UserAddOutlined,
  SearchOutlined,
  WarningOutlined,
  DeleteOutlined,
  CloseOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'
import { emitSpacesInvalidated, emitSpaceChanged } from '@jonex/shell-sdk'
import {
  getSpace,
  updateSpace,
  deleteSpace,
  getSpacePermissions,
  updateSpacePermissions,
} from '../../api/domainSpace'
import type { DomainSpace } from '../../types/domainSpace'
import { userToPermMember, type PermMember } from '../../types/domainService'
import { listUsers, type PlatformUser } from '../../api/user'
import { useStore } from '../../store'

export default observer(function DomainSpaceSettings() {
  const { t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { global } = useStore()

  const [space, setSpace] = useState<DomainSpace | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)


  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [savingInfo, setSavingInfo] = useState(false)


  const [permMembers, setPermMembers] = useState<PermMember[]>([])
  const [permLoading, setPermLoading] = useState(false)
  const [permSaving, setPermSaving] = useState(false)
  const [permSearch, setPermSearch] = useState('')


  const [userSelectOpen, setUserSelectOpen] = useState(false)
  const [userSearchText, setUserSearchText] = useState('')
  const [availableUsers, setAvailableUsers] = useState<PlatformUser[]>([])
  const [usersLoading, setUsersLoading] = useState(false)
  const userSelectRef = useRef<HTMLDivElement>(null)


  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deleting, setDeleting] = useState(false)


  const loadSpace = useCallback(async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const data = await getSpace(id)
      setSpace(data)
      setName(data.name)
      setDescription(data.description || '')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('common.loadFailed'))
    } finally {
      setLoading(false)
    }
  }, [id])


  const loadPermissions = useCallback(async () => {
    if (!id) return
    setPermLoading(true)
    try {
      const perms = await getSpacePermissions(id)
      if (perms.length > 0) {
        const userMap = new Map<string, PlatformUser>()
        try {
          const userResult = await listUsers(1, 100)
          for (const u of userResult.items) userMap.set(String(u.id), u)
        } catch {   }
        setPermMembers(
          perms.map((p) => {
            const uid = String(p.user_id)
            const user = userMap.get(uid)
            const role = (p.role === 'manager' ? 'manager' : 'viewer') as 'viewer' | 'manager'
            return user
              ? userToPermMember(user, role)
              : {
                  id: uid,
                  name: `用户 ${uid.slice(0, 8)}`,
                  department: '',
                  avatar: uid.charAt(0).toUpperCase(),
                  avatarColor: '#94a3b8',
                  role,
                }
          }),
        )
      } else {
        setPermMembers([])
      }
    } catch {
      setPermMembers([])
    } finally {
      setPermLoading(false)
    }
  }, [id])

  useEffect(() => {
    loadSpace()
    loadPermissions()
  }, [loadSpace, loadPermissions])


  useEffect(() => {
    if (global.currentSpaceId && id && global.currentSpaceId !== id) {
      navigate(`/domain-space/${global.currentSpaceId}/settings`, { replace: true })
    }
  }, [global.currentSpaceId, id, navigate])


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


  const handleSaveInfo = async () => {
    if (!id) return
    if (!name.trim()) { message.warning(t('domainSpace.nameRequired')); return }
    setSavingInfo(true)
    try {
      await updateSpace(id, { name: name.trim(), description })
      message.success(t('domainSpace.basicInfoSaved'))
      await global.refreshSpaces()
      emitSpacesInvalidated()
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('common.saveFailed'))
    } finally {
      setSavingInfo(false)
    }
  }


  const addPermMember = (user: PlatformUser) => {
    setPermMembers((prev) => {
      if (prev.some((m) => m.id === String(user.id))) return prev
      return [...prev, userToPermMember(user, 'viewer')]
    })
  }

  const removePermMember = (userId: string) => {
    setPermMembers((prev) => prev.filter((m) => m.id !== userId))
  }

  const setMemberRole = (userId: string, role: 'viewer' | 'manager') => {
    setPermMembers((prev) => prev.map((m) => (m.id === userId ? { ...m, role } : m)))
  }

  const handleSavePermissions = async () => {
    if (!id) return
    setPermSaving(true)
    try {
      await updateSpacePermissions(
        id,
        permMembers.map((m) => ({ user_id: m.id, role: m.role })),
      )
      message.success(t('permission.saveSuccess'))
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('permission.saveFailed'))
    } finally {
      setPermSaving(false)
    }
  }

  const addedUserIds = new Set(permMembers.map((m) => m.id))
  const filteredAvailableUsers = availableUsers.filter((u) => {
    if (addedUserIds.has(String(u.id))) return false
    if (!userSearchText) return true
    const q = userSearchText.toLowerCase()
    return (
      (u.display_name || '').toLowerCase().includes(q) ||
      u.username.toLowerCase().includes(q) ||
      (u.email || '').toLowerCase().includes(q)
    )
  })
  const filteredPermMembers = permMembers.filter((m) => {
    if (!permSearch) return true
    return m.name.includes(permSearch) || m.department.includes(permSearch)
  })


  const handleDelete = async () => {
    if (!id) return
    setDeleting(true)
    try {
      const wasCurrent = global.currentSpaceId === id
      await deleteSpace(id)
      message.success(t('domainSpace.deleteSuccess'))
      setDeleteOpen(false)
      await global.refreshSpaces()
      if (wasCurrent) emitSpaceChanged(global.currentSpaceId)
      emitSpacesInvalidated()
      navigate('/domain-space')
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('common.deleteFailed'))
    } finally {
      setDeleting(false)
    }
  }

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}><Spin size="large" /></div>
  }
  if (error || !space) {
    return (
      <Result
        status="error"
        title={t('common.loadFailed')}
        subTitle={error || '未找到该领域空间'}
        extra={<Button type="primary" onClick={() => navigate('/domain-space')}>{t('domainKnowledge.list')}</Button>}
      />
    )
  }

  return (
    <div className="yx-domain-space-page">
      { }
      <div className="yx-page-header">
        <h1 className="yx-page-title" style={{ margin: 0 }}>{t('domainSpace.settings')} · {space.name}</h1>
      </div>

      { }
      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 17, fontWeight: 600, color: '#0b2b5c', marginBottom: 16, paddingBottom: 12, borderBottom: '1px solid #eef2f6', display: 'flex', alignItems: 'center', gap: 8 }}>
          <InfoCircleOutlined style={{ color: '#3b82f6' }} /> {t('domainSpace.basicInfo')}
        </h2>
        <div className="yx-card" style={{ padding: '24px 28px' }}>
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, color: '#64748b', marginBottom: 6 }}>空间名称</div>
            <Input value={name} onChange={(e) => setName(e.target.value)} maxLength={128} placeholder="领域空间名称" />
          </div>
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, color: '#64748b', marginBottom: 6 }}>空间描述</div>
            <Input.TextArea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} placeholder="简要描述该空间的用途和范围" />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, paddingTop: 8 }}>
            <Button type="primary" icon={<SaveOutlined />} loading={savingInfo} onClick={handleSaveInfo}>
              {t('common.save')}
            </Button>
          </div>
        </div>
      </section>

      { }
      <section style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 17, fontWeight: 600, color: '#0b2b5c', marginBottom: 16, paddingBottom: 12, borderBottom: '1px solid #eef2f6', display: 'flex', alignItems: 'center', gap: 8 }}>
          <TeamOutlined style={{ color: '#3b82f6' }} /> {t('domainSpace.permission')}
        </h2>
        <div className="yx-card" style={{ padding: '24px 28px' }}>
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
            >
              {t('domainKnowledge.addMember')}
            </Button>
            {userSelectOpen && (
              <div style={{ position: 'absolute', top: 40, left: 0, zIndex: 10, width: 320, background: '#fff', borderRadius: 8, boxShadow: '0 4px 20px rgba(0,0,0,.12)', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
                <div style={{ padding: '8px 12px', borderBottom: '1px solid #e2e8f0' }}>
                  <Input size="small" placeholder={t('domainKnowledge.selectMember')} prefix={<SearchOutlined style={{ color: '#94a3b8' }} />} value={userSearchText} onChange={(e) => setUserSearchText(e.target.value)} allowClear />
                </div>
                <div style={{ maxHeight: 220, overflowY: 'auto' }}>
                  {usersLoading ? (
                    <div style={{ textAlign: 'center', padding: 20 }}><Spin size="small" /></div>
                  ) : filteredAvailableUsers.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: 20, color: '#94a3b8', fontSize: 13 }}>
                      {userSearchText ? t('domainKnowledge.selectMember') : t('domainKnowledge.addMemberSoon')}
                    </div>
                  ) : (
                    filteredAvailableUsers.slice(0, 30).map((user) => (
                      <div key={user.id} className="yx-perm-user-row" style={{ cursor: 'pointer', padding: '8px 12px' }} onClick={() => { addPermMember(user); setUserSearchText('') }}>
                        <div className="yx-perm-avatar" style={{ background: userToPermMember(user).avatarColor }}>
                          {userToPermMember(user).avatar}
                        </div>
                        <div className="yx-perm-user-info" style={{ flex: 1 }}>
                          <div className="yx-perm-user-name">{user.display_name || user.username}</div>
                          <div className="yx-perm-user-dept">{user.email || user.role || ''}</div>
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
            <input type="text" placeholder={t('domainKnowledge.selectMember')} value={permSearch} onChange={(e) => setPermSearch(e.target.value)} style={{ width: '100%' }} />
          </div>

          { }
          <div style={{ maxHeight: 320, overflowY: 'auto', marginBottom: 16 }}>
            {permLoading ? (
              <div style={{ textAlign: 'center', padding: 24 }}><Spin /></div>
            ) : filteredPermMembers.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 24, color: '#94a3b8', fontSize: 13 }}>
                {permSearch ? t('domainKnowledge.selectMember') : t('domainKnowledge.addMemberSoon')}
              </div>
            ) : (
              filteredPermMembers.map((member) => (
                <div key={member.id} className="yx-perm-user-row">
                  <div className="yx-perm-avatar" style={{ background: member.avatarColor }}>{member.avatar}</div>
                  <div className="yx-perm-user-info" style={{ flex: 1 }}>
                    <div className="yx-perm-user-name">{member.name}</div>
                    <div className="yx-perm-user-dept">{member.department || `ID: ${member.id.slice(0, 8)}`}</div>
                  </div>
                  <div className="yx-perm-radio">
                    <label className={`yx-perm-radio-label${member.role === 'viewer' ? ' is-checked' : ''}`}>
                      <input type="radio" name={`perm-${member.id}`} value="viewer" checked={member.role === 'viewer'} onChange={() => setMemberRole(member.id, 'viewer')} />
                      {t('domainKnowledge.roleView')}
                    </label>
                    <label className={`yx-perm-radio-label${member.role === 'manager' ? ' is-checked' : ''}`}>
                      <input type="radio" name={`perm-${member.id}`} value="manager" checked={member.role === 'manager'} onChange={() => setMemberRole(member.id, 'manager')} />
                      {t('domainKnowledge.roleManage')}
                    </label>
                  </div>
                  <button type="button" className="yx-perm-remove-btn" onClick={() => removePermMember(member.id)} title={t('domainKnowledge.selectMember')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: 16, padding: '0 0 0 8px', lineHeight: 1 }}>
                    <CloseOutlined />
                  </button>
                </div>
              ))
            )}
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button type="primary" icon={<SaveOutlined />} loading={permSaving} onClick={handleSavePermissions}>
              {t('domainKnowledge.savePermission')}
            </Button>
          </div>
        </div>
      </section>

      { }
      <section>
        <div style={{ border: '1px solid #fecaca', borderRadius: 14, overflow: 'hidden' }}>
          <div style={{ background: '#fef2f2', padding: '16px 24px', display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600, color: '#dc2626', fontSize: 15 }}>
            <WarningOutlined /> {t('domainSpace.delete')}
          </div>
          <div style={{ background: '#fff', padding: 24, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <p style={{ fontSize: 14, color: '#1e293b', fontWeight: 500, marginBottom: 4 }}>{t('domainSpace.delete')}</p>
              <p style={{ fontSize: 13, color: '#64748b' }}>删除后该空间下的所有领域和知识库将被移除，此操作不可撤销。</p>
            </div>
            <Button danger type="primary" icon={<DeleteOutlined />} onClick={() => setDeleteOpen(true)}>
              {t('domainSpace.delete')}
            </Button>
          </div>
        </div>
      </section>

      { }
      <Modal
        wrapClassName="yx-domain-space-modal"
        title={<span><WarningOutlined style={{ color: '#ef4444', marginRight: 8 }} />{t('validation.confirmDelete')}</span>}
        open={deleteOpen}
        onCancel={() => setDeleteOpen(false)}
        footer={
          <div style={{ display: 'flex', justifyContent: 'center', gap: 12 }}>
            <Button onClick={() => setDeleteOpen(false)}>{t('dataSource.cancel')}</Button>
            <Button danger type="primary" loading={deleting} onClick={handleDelete}>{t('validation.confirmDelete')}</Button>
          </div>
        }
        width={420}
      >
        <div style={{ textAlign: 'center', padding: '12px 0' }}>
          <DeleteOutlined style={{ fontSize: 48, color: '#ef4444', marginBottom: 16, display: 'block' }} />
          <p style={{ fontSize: 16, color: '#1e293b', fontWeight: 500 }}>
            确定要删除领域空间 "<strong>{space.name}</strong>" 吗？
          </p>
          <p style={{ fontSize: 13, color: '#94a3b8', marginTop: 8 }}>
            删除后该空间下的所有领域和知识库将被移除，此操作不可撤销。
          </p>
        </div>
      </Modal>
    </div>
  )
})
