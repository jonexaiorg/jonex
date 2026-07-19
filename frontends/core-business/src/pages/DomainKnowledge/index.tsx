import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { Input, Select, Button, Modal, message, Empty, Spin } from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  GlobalOutlined,
  SettingOutlined,
  CloseOutlined,
  EditOutlined,
  DeleteOutlined,
  EllipsisOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  DatabaseOutlined,
  LineChartOutlined,
} from '@ant-design/icons'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { observer } from 'mobx-react-lite'
import { useStore } from '@/store'
import { SPACE_URL_PARAM } from '@jonex/shell-sdk'
import type {
  DomainKnowledgeItem,
  DomainKnowledgePermissionMember,
} from '@/types/domainKnowledge'
import {
  getDomainKnowledgeList,
  getDomainKnowledgePermissions,
  saveDomainKnowledgePermissions,
  createKnowledgeInfo,
  updateKnowledgeInfo,
  deleteKnowledgeInfo,
} from '@/api/domainKnowledge'
import { listAccessMethods } from '@/api/dataSource'

const PAGE_SIZE = 6

export default observer(function DomainKnowledge() {
  const { t } = useTranslation()
  const { global } = useStore()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()


  const [keywordInput, setKeywordInput] = useState('')
  const [keyword, setKeyword] = useState('')


  const [sourceTypeNames, setSourceTypeNames] = useState<Record<string, string>>({})

  const fetchSourceTypeNames = useCallback(async () => {
    try {
      const methods = await listAccessMethods()
      const map: Record<string, string> = {}
      methods.forEach((m) => { map[m.accessType] = m.name })
      setSourceTypeNames(map)
    } catch {   }
  }, [])


  const [list, setList] = useState<DomainKnowledgeItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)


  const [openMenuKbId, setOpenMenuKbId] = useState<string | null>(null)
  const cardMoreRefs = useRef<Map<string, HTMLDivElement | null>>(new Map())


  const [permOpen, setPermOpen] = useState(false)
  const [permLoading, setPermLoading] = useState(false)
  const [permSaving, setPermSaving] = useState(false)
  const [currentKb, setCurrentKb] = useState<DomainKnowledgeItem | null>(null)
  const [permissionMembers, setPermissionMembers] = useState<DomainKnowledgePermissionMember[]>([])
  const [permissionKeyword, setPermissionKeyword] = useState('')


  const [createOpen, setCreateOpen] = useState(false)
  const [createName, setCreateName] = useState('')
  const [createSpaceId, setCreateSpaceId] = useState('')
  const [createDesc, setCreateDesc] = useState('')
  const [createSubmitting, setCreateSubmitting] = useState(false)


  const [editingKb, setEditingKb] = useState<DomainKnowledgeItem | null>(null)
  const [deletingKb, setDeletingKb] = useState<DomainKnowledgeItem | null>(null)
  const [deleteSubmitting, setDeleteSubmitting] = useState(false)

  const debounceRef = useRef<ReturnType<typeof setTimeout>>()



  useEffect(() => {
    const urlSpaceId = searchParams.get(SPACE_URL_PARAM)
    if (urlSpaceId && global.spaces.some((s) => s.id === urlSpaceId)) {
      global.setCurrentSpaceId(urlSpaceId, { persist: true, broadcast: false })
    }
  }, [])


  useEffect(() => {
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
  }, [global.currentSpaceId])


  const fetchList = useCallback(
    async (p: number, kw: string) => {
      setLoading(true)
      try {
        const result = await getDomainKnowledgeList({
          page: p,
          pageSize: PAGE_SIZE,
          keyword: kw || undefined,
          spaceId: global.currentSpaceId || undefined,
        })
        setList(result.list)
        setTotal(result.pagination.total)
      } catch (err: any) {
        message.error(err?.message || t('domainKnowledge.loadFailed'))
      } finally {
        setLoading(false)
      }
    },
    [global.currentSpaceId],
  )


  useEffect(() => {
    global.loadSpaces()
    fetchSourceTypeNames()
  }, [])

  useEffect(() => {
    if (global.spacesLoaded) {
      fetchList(1, keyword)
    }
  }, [global.spacesLoaded, global.currentSpaceId])


  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setKeyword(keywordInput)
    }, 300)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [keywordInput])


  useEffect(() => {
    if (global.spacesLoaded) {
      fetchList(1, keyword)
    }
  }, [keyword])


  useEffect(() => {
    if (page !== 1 && global.spacesLoaded) {
      fetchList(page, keyword)
    }
  }, [page])


  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (!openMenuKbId) return
      const target = e.target as HTMLElement

      let insideOpen = false
      cardMoreRefs.current.forEach((el, id) => {
        if (el && el.contains(target)) {
          insideOpen = true
        }
      })
      if (!insideOpen) {
        setOpenMenuKbId(null)
      }
    }
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [openMenuKbId])


  const toggleCardMenu = (e: React.MouseEvent, kbId: string) => {
    e.stopPropagation()
    setOpenMenuKbId((prev) => (prev === kbId ? null : kbId))
  }


  const handleCreate = async () => {
    if (!createName.trim()) { message.warning(t('domainKnowledge.nameRequired')); return }
    if (!createSpaceId) { message.warning(t('domainKnowledge.spaceRequired')); return }
    setCreateSubmitting(true)
    try {
      const data = {
        name: createName.trim(),
        space_id: createSpaceId,
        description: createDesc || undefined,
      }
      if (editingKb) {
        await updateKnowledgeInfo(editingKb.id, data)
        message.success(t('domainKnowledge.updateSuccess'))
      } else {
        await createKnowledgeInfo(data)
        message.success(t('domainKnowledge.createSuccess'))
      }
      setCreateOpen(false)
      setEditingKb(null)
      setCreateName('')
      setCreateSpaceId('')
      setCreateDesc('')
      fetchList(1, keyword)
    } catch (err: any) {
      message.error(err?.message || (editingKb ? t('domainKnowledge.updateFailed') : t('domainKnowledge.createFailed')))
    } finally {
      setCreateSubmitting(false)
    }
  }

  const openCreateModal = () => {
    setEditingKb(null)
    setCreateName('')
    setCreateSpaceId(global.currentSpaceId || '')
    setCreateDesc('')
    setCreateOpen(true)
  }

  const openEditModal = (kb: DomainKnowledgeItem) => {
    setEditingKb(kb)
    setCreateName(kb.name)
    setCreateSpaceId(kb.spaceId)
    setCreateDesc(kb.description || '')
    setCreateOpen(true)
  }

  const handleDelete = async () => {
    if (!deletingKb) return
    setDeleteSubmitting(true)
    try {
      await deleteKnowledgeInfo(deletingKb.id)
      message.success(t('domainKnowledge.deleteSuccess'))
      setDeletingKb(null)
      fetchList(1, keyword)
    } catch (err: any) {
      message.error(err?.message || t('domainKnowledge.deleteFailed'))
    } finally {
      setDeleteSubmitting(false)
    }
  }


  const openPermModal = async (kb: DomainKnowledgeItem) => {
    setCurrentKb(kb)
    setPermissionKeyword('')
    setPermOpen(true)
    setPermLoading(true)
    try {
      const data = await getDomainKnowledgePermissions(kb.id)
      setPermissionMembers(data.members)
    } catch {
      message.error(t('domainKnowledge.permissionLoadFailed'))
    } finally {
      setPermLoading(false)
    }
  }

  const debouncedPermSearch = useCallback(
    (kw: string) => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
      debounceRef.current = setTimeout(async () => {
        if (!currentKb) return
        setPermLoading(true)
        try {
          const data = await getDomainKnowledgePermissions(currentKb.id, kw || undefined)
          setPermissionMembers(data.members)
        } catch {

        } finally {
          setPermLoading(false)
        }
      }, 300)
    },
    [currentKb],
  )

  const handlePermKeywordChange = (val: string) => {
    setPermissionKeyword(val)
    debouncedPermSearch(val)
  }

  const handlePermRoleChange = (userId: string, role: 'view' | 'manage') => {
    setPermissionMembers((prev) =>
      prev.map((m) => (m.userId === userId ? { ...m, role } : m)),
    )
  }

  const handleSavePermissions = async () => {
    if (!currentKb) return
    setPermSaving(true)
    try {
      await saveDomainKnowledgePermissions(currentKb.id, {
        members: permissionMembers.map((m) => ({
          userId: m.userId,
          role: m.role,
        })),
      })
      message.success(t('domainKnowledge.permissionSaveSuccess'))
      setPermOpen(false)
    } catch (err: any) {
      message.error(err?.message || t('domainKnowledge.permissionSaveFailed'))
    } finally {
      setPermSaving(false)
    }
  }


  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  const pageNumbers = (): number[] => {
    const pages: number[] = []
    for (let i = 1; i <= totalPages; i++) pages.push(i)
    return pages
  }


  const displayList = list.map((item) => ({
    ...item,
    spaceName: global.currentSpace?.name || item.spaceName || '',
  }))


  const getSourceTypeDisplay = (type: string): string => {
    return sourceTypeNames[type] || type
  }


  return (
    <div>
      { }
      <div className="yx-page-title">
        <h1>{t('domainKnowledge.title')}</h1>
        <p className="yx-page-subtitle">
          {t('domainKnowledge.title')}
        </p>
      </div>

      { }
      <div className="yx-filter-row">
        <label>
          <GlobalOutlined style={{ color: '#3b82f6' }} /> {t('domainSpace.settings')}：
        </label>
        <span style={{ fontWeight: 500, color: '#0b2b5c' }}>
          {global.currentSpace?.name || t('domainKnowledge.noSpace')}
        </span>
        <span className="yx-filter-count">
          {t('common.totalPage', { total: total })}
        </span>
      </div>

      { }
      <div className="yx-page-card">
        <div className="yx-toolbar">
          <div className="yx-search-box">
            <SearchOutlined style={{ color: '#94a3b8', fontSize: 14 }} />
            <input
              type="text"
              placeholder={t('domainKnowledge.name')}
              value={keywordInput}
              onChange={(e) => {
                setKeywordInput(e.target.value)
                setPage(1)
              }}
            />
          </div>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
            {t('domainKnowledge.create')}
          </Button>
        </div>

        { }
        {loading && list.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '80px 0' }}>
            <Spin size="large" />
          </div>
        ) : list.length === 0 ? (

          <div style={{ textAlign: 'center', padding: '80px 0' }}>
            <Empty description={t('domainKnowledge.title')}>
              <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
                {t('domainKnowledge.create')}
              </Button>
            </Empty>
          </div>
        ) : (

          <div className="kb-card-grid">
            {displayList.map((item) => (
              <div className="kb-card" key={item.id}>
                { }
                <div className="kb-card-top">
                  <div className="kb-card-icon">
                    <DatabaseOutlined />
                  </div>
                  <div className="kb-card-info">
                    <div
                      className="kb-card-name"
                      onClick={() => navigate(`/domain-knowledge/${item.id}`)}
                    >
                      {item.name}
                    </div>
                    <div className="kb-card-meta">
                      <span>
                        <FileTextOutlined /> {(item.documentCount ?? 0).toLocaleString()} {t('domainKnowledge.list')}
                      </span>
                      <span>
                        <ClockCircleOutlined /> {item.updatedAt || '—'}
                      </span>
                    </div>
                  </div>
                  { }
                  <div
                    className="card-more"
                    ref={(el) => { cardMoreRefs.current.set(item.id, el) }}
                  >
                    <button
                      className="card-more-btn"
                      onClick={(e) => toggleCardMenu(e, item.id)}
                    >
                      <EllipsisOutlined />
                    </button>
                    <div
                      className={`card-dropdown${openMenuKbId === item.id ? ' open' : ''}`}
                      style={{ display: openMenuKbId === item.id ? 'block' : 'none' }}
                    >
                      <a
                        className="card-dropdown-item"
                        onClick={(e) => {
                          e.stopPropagation()
                          setOpenMenuKbId(null)
                          navigate(`/domain-knowledge/${item.id}`)
                        }}
                      >
                        <SettingOutlined /> {t('domainKnowledge.settings')}
                      </a>
                      <a
                        className="card-dropdown-item"
                        onClick={(e) => {
                          e.stopPropagation()
                          setOpenMenuKbId(null)
                          navigate(`/domain-knowledge/${item.id}/tracking`)
                        }}
                      >
                        <LineChartOutlined /> {t('knowledgeTracking.title')}
                      </a>
                      <a
                        className="card-dropdown-item"
                        onClick={(e) => {
                          e.stopPropagation()
                          setOpenMenuKbId(null)
                          openEditModal(item)
                        }}
                      >
                        <EditOutlined /> {t('domainKnowledge.edit')}
                      </a>
                      <a
                        className="card-dropdown-item danger"
                        onClick={(e) => {
                          e.stopPropagation()
                          setOpenMenuKbId(null)
                          setDeletingKb(item)
                        }}
                      >
                        <DeleteOutlined /> {t('domainKnowledge.delete')}
                      </a>
                    </div>
                  </div>
                </div>

                { }
                <div className="kb-card-body">
                  <div className="kb-card-desc">
                    {item.description || t('common.noDescription')}
                  </div>
                </div>

                { }
                <div className="kb-card-tags">
                  <div className="source-tags">
                    {(item.dataSourceTypes && item.dataSourceTypes.length > 0
                      ? item.dataSourceTypes
                      : ['file']
                    ).map((type) => (
                      <span key={type} className="source-tag">
                        {getSourceTypeDisplay(type)}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        { }
        {list.length > 0 && (
          <div className="yx-pagination">
            <span
              className={`yx-page-btn${page <= 1 ? ' disabled' : ''}`}
              onClick={() => page > 1 && setPage((p) => p - 1)}
            >
              &lt;
            </span>
            {pageNumbers().map((n) => (
              <span
                key={n}
                className={`yx-page-btn${n === page ? ' active' : ''}`}
                onClick={() => setPage(n)}
              >
                {n}
              </span>
            ))}
            <span
              className={`yx-page-btn${page >= totalPages ? ' disabled' : ''}`}
              onClick={() => page < totalPages && setPage((p) => p + 1)}
            >
              &gt;
            </span>
            <span className="yx-page-info">
              {t('common.totalPage', { total, page, totalPages })}
            </span>
          </div>
        )}
      </div>

      { }
      <Modal
        open={permOpen}
        onCancel={() => setPermOpen(false)}
        footer={null}
        width={600}
        closable={false}
        styles={{ body: { padding: 0 } }}
      >
        <div className="yx-modal-header">
          <h2>
            <SettingOutlined style={{ color: '#3b82f6' }} /> {t('domainKnowledge.scopePermission')}
          </h2>
          <button className="yx-modal-close-btn" onClick={() => setPermOpen(false)}>
            <CloseOutlined />
          </button>
        </div>
        <div style={{ padding: '20px 24px' }}>
          <p style={{ fontSize: 14, color: '#475569', marginBottom: 16 }}>
            {t('domainKnowledge.scopePermission')}{' '}
            <strong style={{ color: '#0b2b5c' }}>{currentKb?.name}</strong>{' '}
            {t('domainKnowledge.scopeMembers')}
          </p>
          <div className="yx-search-box yx-perm-search">
            <SearchOutlined style={{ color: '#94a3b8', fontSize: 14 }} />
            <input
              type="text"
              placeholder={t('domainKnowledge.selectMember')}
              value={permissionKeyword}
              onChange={(e) => handlePermKeywordChange(e.target.value)}
            />
          </div>
          {permLoading ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>
              {t('dataSource.loading')}
            </div>
          ) : (
            permissionMembers.map((u, i) => {
              const checked = u.role
              return (
                <div className="yx-perm-user-row" key={u.userId}>
                  <div
                    className="yx-perm-avatar"
                    style={{ background: u.avatarColor }}
                  >
                    {u.avatarText}
                  </div>
                  <div className="yx-perm-user-info">
                    <div className="yx-perm-user-name">{u.name}</div>
                    <div className="yx-perm-user-dept">{u.dept}</div>
                  </div>
                  <div className="yx-perm-radio">
                    {(['view', 'manage'] as const).map((role) => {
                      const isActive = checked === role
                      const label = role === 'view' ? t('domainKnowledge.roleView') : t('domainKnowledge.roleManage')
                      return (
                        <label
                          key={role}
                          className={isActive ? 'is-checked' : ''}
                        >
                          <input
                            type="radio"
                            name={`perm-${i}`}
                            checked={isActive}
                            onChange={() => handlePermRoleChange(u.userId, role)}
                          />
                          {label}
                        </label>
                      )
                    })}
                  </div>
                </div>
              )
            })
          )}
        </div>
        <div className="yx-modal-footer">
          <Button onClick={() => setPermOpen(false)}>{t('dataSource.cancel')}</Button>
          <Button
            type="primary"
            loading={permSaving}
            onClick={handleSavePermissions}
          >
            {t('domainKnowledge.savePermission')}
          </Button>
        </div>
      </Modal>

      { }
      <Modal
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={handleCreate}
        confirmLoading={createSubmitting}
        okText={editingKb ? t('common.save') : t('domainKnowledge.create')}
        cancelText={t('dataSource.cancel')}
        width={520}
        title={
          <span>
            {editingKb ? (
              <EditOutlined style={{ color: '#3b82f6', marginRight: 8 }} />
            ) : (
              <PlusOutlined style={{ color: '#3b82f6', marginRight: 8 }} />
            )}
            {editingKb ? t('domainKnowledge.edit') : t('domainKnowledge.create')}
          </span>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <label
              style={{
                display: 'block',
                fontSize: 13,
                fontWeight: 500,
                color: '#475569',
                marginBottom: 4,
              }}
            >
              {t('domainKnowledge.name')} <span style={{ color: '#ef4444' }}>*</span>
            </label>
            <Input
              placeholder={t('domainKnowledge.nameRequired')}
              value={createName}
              onChange={(e) => setCreateName(e.target.value)}
            />
          </div>
          <div>
            <label
              style={{
                display: 'block',
                fontSize: 13,
                fontWeight: 500,
                color: '#475569',
                marginBottom: 4,
              }}
            >
              {t('domainService.space')}
            </label>
            <Input
              value={global.currentSpace?.name || t('domainKnowledge.selectSpace')}
              disabled
              style={{ width: '100%' }}
            />
          </div>
          <div>
            <label
              style={{
                display: 'block',
                fontSize: 13,
                fontWeight: 500,
                color: '#475569',
                marginBottom: 4,
              }}
            >
              {t('domainService.description')}
            </label>
            <Input.TextArea
              rows={3}
              placeholder={t('domainKnowledge.descriptionPlaceholder')}
              value={createDesc}
              onChange={(e) => setCreateDesc(e.target.value)}
            />
          </div>
        </div>
      </Modal>

      { }
      <Modal
        open={!!deletingKb}
        onCancel={() => setDeletingKb(null)}
        footer={
          <div style={{ display: 'flex', justifyContent: 'center', gap: 12 }}>
            <Button onClick={() => setDeletingKb(null)}>{t('dataSource.cancel')}</Button>
            <Button danger type="primary" loading={deleteSubmitting} onClick={handleDelete}>
              {t('validation.confirmDelete')}
            </Button>
          </div>
        }
        width={420}
        title={null}
      >
        <div style={{ textAlign: 'center', padding: '12px 0' }}>
          <DeleteOutlined
            style={{ fontSize: 48, color: '#ef4444', marginBottom: 16, display: 'block' }}
          />
          <p style={{ fontSize: 16, color: '#1e293b', fontWeight: 500 }}>
            {t('domainKnowledge.deleteConfirm', { name: deletingKb?.name || '' })}
          </p>
          <p style={{ fontSize: 13, color: '#94a3b8', marginTop: 8 }}>
            {t('domainKnowledge.deleteWarning')}
          </p>
        </div>
      </Modal>
    </div>
  )
})
