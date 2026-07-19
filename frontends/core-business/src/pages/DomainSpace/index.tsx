import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { Input, Button, Table, Tag, Modal, Space, message, Result, Spin } from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  ReloadOutlined,
  TeamOutlined,
  WarningOutlined,
  DeleteOutlined,
  CloseOutlined,
  UserAddOutlined,
} from '@ant-design/icons'
import { emitSpacesInvalidated, emitSpaceChanged } from '@jonex/shell-sdk'
import {
  listSpaces, updateSpace, deleteSpace,
  getSpacePermissions, updateSpacePermissions,
} from '../../api/domainSpace'
import { SPACE_STATUS_MAP, type DomainSpace } from '../../types/domainSpace'
import { userToPermMember, type PermMember } from '../../types/domainService'
import { listUsers, type PlatformUser } from '../../api/user'
import { useStore } from '../../store'
import SpaceFormModal from '../../features/SpaceForm/SpaceFormModal'

export default function DomainSpace() {
  const { t } = useTranslation()
  const { global } = useStore()
  const navigate = useNavigate()
  const [spaces, setSpaces] = useState<DomainSpace[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [submitting, setSubmitting] = useState(false)


  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<DomainSpace | null>(null)
  const [deleting, setDeleting] = useState<DomainSpace | null>(null)


  const [permOpen, setPermOpen] = useState(false)
  const [permSpace, setPermSpace] = useState<DomainSpace | null>(null)
  const [permMembers, setPermMembers] = useState<PermMember[]>([])
  const [permSearch, setPermSearch] = useState('')
  const [permLoading, setPermLoading] = useState(false)


  const [userSelectOpen, setUserSelectOpen] = useState(false)
  const [userSearchText, setUserSearchText] = useState('')
  const [availableUsers, setAvailableUsers] = useState<PlatformUser[]>([])
  const [usersLoading, setUsersLoading] = useState(false)
  const userSelectRef = useRef<HTMLDivElement>(null)

  const loadSpaces = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await listSpaces(0, 100)
      setSpaces(result.items)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadSpaces() }, [loadSpaces])


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

  const filtered = spaces.filter((s) => {
    if (!search) return true
    return s.name.includes(search) || (s.description || '').includes(search)
  })



  const openCreate = () => {
    navigate('/domain-space/new')
  }

  const openEdit = (space: DomainSpace) => {
    setEditing(space)
    setFormOpen(true)
  }


  const handleSaved = async () => {
    setFormOpen(false)
    setEditing(null)
    await loadSpaces()
    await global.refreshSpaces()
    emitSpacesInvalidated()
  }

  const handleDelete = async () => {
    if (!deleting) return
    setSubmitting(true)
    try {
      const wasCurrent = global.currentSpaceId === deleting.id
      await deleteSpace(deleting.id)
      message.success(t('domainSpace.deleteSuccess'))
      setDeleting(null)
      await loadSpaces()

      await global.refreshSpaces()
      if (wasCurrent) {

        emitSpaceChanged(global.currentSpaceId)
      }
      emitSpacesInvalidated()
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('common.deleteFailed'))
    } finally {
      setSubmitting(false)
    }
  }


  const toggleStatus = async (space: DomainSpace) => {
    let newStatus: DomainSpace['status']
    if (space.status === 'active') {
      newStatus = 'disabled'
    } else {
      newStatus = 'active'
    }
    try {
      await updateSpace(space.id, { status: newStatus })
      setSpaces((prev) => prev.map((s) => s.id === space.id ? { ...s, status: newStatus } : s))
      const cfg = SPACE_STATUS_MAP[newStatus]
      message.success(t('domainSpace.switchedTo', { status: t(cfg.tKey) }))
      await global.refreshSpaces()
      emitSpacesInvalidated()
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('common.operationFailed'))
    }
  }


  const openPermModal = async (space: DomainSpace) => {
    setPermSpace(space)
    setPermSearch('')
    setPermOpen(true)
    setPermLoading(true)
    setUserSelectOpen(false)
    setUserSearchText('')
    try {
      const perms = await getSpacePermissions(space.id)
      if (perms.length > 0) {

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
                name: `用户 ${uid.slice(0, 8)}`,
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
      message.error(t('domainSpace.permissionLoadFailed'))
      setPermMembers([])
    } finally {
      setPermLoading(false)
    }
  }

  const handlePermSave = async () => {
    if (!permSpace) return
    setSubmitting(true)
    try {
      await updateSpacePermissions(
        permSpace.id,
        permMembers.map((m) => ({ user_id: m.id, role: m.role })),
      )
      message.success(t('permission.saveSuccess'))
      setPermOpen(false)
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('domainSpace.permissionSaveFailed'))
    } finally {
      setSubmitting(false)
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

  const columns = [
    { title: '空间名称', dataIndex: 'name', key: 'name', width: 160,
      render: (v: string) => <span style={{ color: '#3b82f6', cursor: 'pointer' }}>{v}</span>,
    },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true,
      render: (v: string | null) => v || '—',
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 150,
      render: (v: string | null) => v?.slice(0, 16) || '—',
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 90,
      render: (v: string, r: DomainSpace) => {
        const cfg = SPACE_STATUS_MAP[v] || { tKey: v, color: 'default' }
        return <Tag color={cfg.color} style={{ cursor: 'pointer' }} onClick={() => toggleStatus(r)}>{t(cfg.tKey)}</Tag>
      },
    },

    {
      title: '权限设置', key: 'permission', width: 110,
      render: (_: unknown, r: DomainSpace) => (
        <span className="yx-perm-badge" onClick={() => openPermModal(r)}>
          <TeamOutlined style={{ fontSize: 11, marginRight: 4 }} />
          设置权限
        </span>
      ),
    },
    {
      title: '操作', key: 'actions', width: 120,
      render: (_: unknown, r: DomainSpace) => (
        <Space>
          <a className="yx-table-action" onClick={() => openEdit(r)}>编辑</a>
          <a className="yx-table-action" style={{ color: '#dc2626' }} onClick={() => setDeleting(r)}>删除</a>
        </Space>
      ),
    },
  ]


  if (loading && spaces.length === 0) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}><Spin size="large" /></div>
  }

  if (error) {
    return <Result status="error" title="加载失败" subTitle={error} extra={<Button type="primary" icon={<ReloadOutlined />} onClick={loadSpaces}>重试</Button>} />
  }

  return (
    <div className="yx-domain-space-page">
      { }
      <div className="yx-page-header">
        <h1 className="yx-page-title">领域空间管理</h1>
      </div>

      { }
      <div className="yx-toolbar">
        <div className="yx-search-box">
          <SearchOutlined style={{ color: '#94a3b8', fontSize: 14 }} />
          <input
            type="text"
            placeholder="搜索空间名称..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新建领域空间</Button>
      </div>

      { }
      <div className="yx-card">
        <Table
          columns={columns}
          dataSource={filtered}
          rowKey="id"
          pagination={{
            total: filtered.length,
            pageSize: 10,
            showTotal: (t, range) => `共 ${t} 条，${range[0]}-${range[1]}`,
          }}
          size="middle"
          locale={{ emptyText: '暂无领域空间，点击上方按钮新建' }}
        />
      </div>

      { }
      <SpaceFormModal
        open={formOpen}
        editing={editing}
        onClose={() => { setFormOpen(false); setEditing(null) }}
        onSaved={handleSaved}
      />

      { }
      <Modal
        wrapClassName="yx-domain-space-modal"
        title={
          <span>
            <WarningOutlined style={{ color: '#ef4444', marginRight: 8 }} />
            确认删除
          </span>
        }
        open={!!deleting}
        onCancel={() => setDeleting(null)}
        footer={
          <div style={{ display: 'flex', justifyContent: 'center', gap: 12 }}>
            <Button onClick={() => setDeleting(null)}>取消</Button>
            <Button
              danger
              type="primary"
              loading={submitting}
              onClick={handleDelete}
            >
              确认删除
            </Button>
          </div>
        }
        width={420}
      >
        <div style={{ textAlign: 'center', padding: '12px 0' }}>
          <DeleteOutlined style={{ fontSize: 48, color: '#ef4444', marginBottom: 16, display: 'block' }} />
          <p style={{ fontSize: 16, color: '#1e293b', fontWeight: 500 }}>
            确定要删除领域空间 "<strong>{deleting?.name}</strong>" 吗？
          </p>
          <p style={{ fontSize: 13, color: '#94a3b8', marginTop: 8 }}>
            删除后该空间下的所有领域和知识库将被移除，此操作不可撤销。
          </p>
        </div>
      </Modal>

      { }
      <Modal
        wrapClassName="yx-domain-space-modal"
        title={
          <span>
            <TeamOutlined style={{ color: '#3b82f6', marginRight: 8 }} />
            空间权限设置
          </span>
        }
        open={permOpen}
        onCancel={() => { setPermOpen(false); setUserSelectOpen(false) }}
        onOk={handlePermSave}
        confirmLoading={submitting}
        okText="保存权限"
        cancelText="取消"
        width={600}
      >
        <p style={{ fontSize: 14, color: '#475569', marginBottom: 12 }}>
          为 <strong style={{ color: '#0b2b5c' }}>{permSpace?.name}</strong> 设置成员权限
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
            添加成员
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
                  placeholder="搜索用户名或邮箱..."
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
                    {userSearchText ? '未找到匹配用户' : '暂无可添加的用户'}
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
            placeholder="搜索已添加的成员..."
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
              {permSearch ? '未找到匹配的成员' : '暂无权限成员，请通过上方按钮添加'}
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
                    查看
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
                    管理
                  </label>
                </div>
                <button
                  type="button"
                  className="yx-perm-remove-btn"
                  onClick={() => removePermMember(member.id)}
                  title="移除成员"
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
    </div>
  )
}