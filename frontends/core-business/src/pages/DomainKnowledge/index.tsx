import React, { useState, useEffect, useCallback, useRef } from 'react'
import { Input, Select, Button, Card, Table, Tag, Modal, message, Space } from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  GlobalOutlined,
  SettingOutlined,
  CloseOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import type {
  DomainKnowledgeSpace,
  DomainKnowledgeItem,
  DomainKnowledgePermissionMember,
} from '@/types/domainKnowledge'
import { statusTextMap, sourceTypeTextMap, statusColorMap } from '@/types/domainKnowledge'
import {
  getDomainKnowledgeSpaces,
  getDomainKnowledgeList,
  getDomainKnowledgePermissions,
  saveDomainKnowledgePermissions,
} from '@/api/domainKnowledge'

const PAGE_SIZE = 6

export default function DomainKnowledge() {
  const navigate = useNavigate()

  // ── filter state ────────────────────────────────────
  const [keywordInput, setKeywordInput] = useState('')
  const [keyword, setKeyword] = useState('')
  const [spaceId, setSpaceId] = useState('')
  const [spaces, setSpaces] = useState<DomainKnowledgeSpace[]>([])

  // ── list state ───────────────────────────────────────
  const [list, setList] = useState<DomainKnowledgeItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)

  // ── permission modal state ───────────────────────────
  const [permOpen, setPermOpen] = useState(false)
  const [permLoading, setPermLoading] = useState(false)
  const [permSaving, setPermSaving] = useState(false)
  const [currentKb, setCurrentKb] = useState<DomainKnowledgeItem | null>(null)
  const [permissionMembers, setPermissionMembers] = useState<DomainKnowledgePermissionMember[]>([])
  const [permissionKeyword, setPermissionKeyword] = useState('')

  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  // ── fetch helpers ────────────────────────────────────
  const fetchSpaces = useCallback(async () => {
    try {
      const data = await getDomainKnowledgeSpaces()
      setSpaces(data)
    } catch {
      // spaces load silently
    }
  }, [])

  const fetchList = useCallback(
    async (p: number, kw: string, sid: string) => {
      setLoading(true)
      try {
        const result = await getDomainKnowledgeList({
          page: p,
          pageSize: PAGE_SIZE,
          keyword: kw || undefined,
          spaceId: sid || undefined,
        })
        setList(result.list)
        setTotal(result.pagination.total)
      } catch (err: any) {
        message.error(err?.message || '获取知识库列表失败')
      } finally {
        setLoading(false)
      }
    },
    [],
  )

  // ── initial load ─────────────────────────────────────
  useEffect(() => {
    fetchSpaces()
    fetchList(1, '', '')
  }, [fetchSpaces, fetchList])

  // ── debounced keyword ────────────────────────────────
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setKeyword(keywordInput)
    }, 300)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [keywordInput])

  // ── keyword or spaceId change → reload page 1 ───────
  useEffect(() => {
    fetchList(1, keyword, spaceId)
  }, [keyword, spaceId, fetchList])

  // ── pagination change → reload ───────────────────────
  useEffect(() => {
    if (page !== 1) {
      fetchList(page, keyword, spaceId)
    }
  }, [page])

  // ── permission modal ─────────────────────────────────
  const openPermModal = async (kb: DomainKnowledgeItem) => {
    setCurrentKb(kb)
    setPermissionKeyword('')
    setPermOpen(true)
    setPermLoading(true)
    try {
      const data = await getDomainKnowledgePermissions(kb.id)
      setPermissionMembers(data.members)
    } catch {
      message.error('获取权限成员失败')
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
          // silent
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
      message.success('权限保存成功')
      setPermOpen(false)
    } catch (err: any) {
      message.error(err?.message || '权限保存失败')
    } finally {
      setPermSaving(false)
    }
  }

  // ── columns ──────────────────────────────────────────
  const columns = [
    {
      title: '知识库名称',
      dataIndex: 'name',
      key: 'name',
      width: 180,
      render: (v: string, r: DomainKnowledgeItem) => (
        <span
          className="kb-name"
          style={{ color: '#3b82f6', cursor: 'pointer', fontWeight: 500 }}
          onClick={() => navigate(`/domain-knowledge/${r.id}`)}
        >
          {v}
        </span>
      ),
    },
    { title: '所属空间', dataIndex: 'spaceName', key: 'spaceName', width: 140 },
    {
      title: '数据源类型',
      dataIndex: 'dataSourceTypes',
      key: 'dataSourceTypes',
      width: 200,
      render: (types: string[]) => (
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {types.map((t) => (
            <span
              key={t}
              style={{
                fontSize: 11,
                padding: '2px 8px',
                borderRadius: 4,
                background: '#eff6ff',
                color: '#3b82f6',
                border: '1px solid #bfdbfe',
              }}
            >
              {sourceTypeTextMap[t as keyof typeof sourceTypeTextMap] || t}
            </span>
          ))}
        </div>
      ),
    },
    {
      title: '文档数',
      dataIndex: 'documentCount',
      key: 'documentCount',
      width: 90,
      render: (v: number) => v.toLocaleString(),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (v: string) => (
        <Tag color={statusColorMap[v as keyof typeof statusColorMap]}>
          {statusTextMap[v as keyof typeof statusTextMap] || v}
        </Tag>
      ),
    },
    {
      title: '权限设置',
      key: 'perm',
      width: 110,
      render: (_: unknown, r: DomainKnowledgeItem) => (
        <span
          className="perm-badge"
          onClick={() => openPermModal(r)}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 4,
            fontSize: 12,
            padding: '2px 10px',
            borderRadius: 6,
            background: '#f1f5f9',
            color: '#64748b',
            cursor: 'pointer',
            border: '1px solid #e2e8f0',
          }}
          onMouseEnter={(e) => {
            ;(e.currentTarget as HTMLElement).style.background = '#eff6ff'
            ;(e.currentTarget as HTMLElement).style.color = '#3b82f6'
            ;(e.currentTarget as HTMLElement).style.borderColor = '#bfdbfe'
          }}
          onMouseLeave={(e) => {
            ;(e.currentTarget as HTMLElement).style.background = '#f1f5f9'
            ;(e.currentTarget as HTMLElement).style.color = '#64748b'
            ;(e.currentTarget as HTMLElement).style.borderColor = '#e2e8f0'
          }}
        >
          <SettingOutlined style={{ fontSize: 11 }} /> 设置权限
        </span>
      ),
    },
    { title: '更新时间', dataIndex: 'updatedAt', key: 'updatedAt', width: 150 },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_: unknown, r: DomainKnowledgeItem) => (
        <Space>
          <a className="yx-table-action" onClick={() => navigate(`/domain-knowledge/${r.id}`)}>
            查看
          </a>
          <a className="yx-table-action">编辑</a>
        </Space>
      ),
    },
  ]

  // ── pagination helpers ───────────────────────────────
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  const pageNumbers = (): number[] => {
    const pages: number[] = []
    for (let i = 1; i <= totalPages; i++) pages.push(i)
    return pages
  }

  // ── render ───────────────────────────────────────────
  return (
    <div>
      <div className="yx-page-title">
        <h1>领域知识管理</h1>
        <p className="yx-page-subtitle">
          管理各领域空间下的知识库，每个知识库需关联到所属领域空间
        </p>
      </div>

      {/* Filter Row */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          marginBottom: 20,
          flexWrap: 'wrap',
        }}
      >
        <label
          style={{
            fontSize: 14,
            fontWeight: 500,
            color: '#475569',
            whiteSpace: 'nowrap',
            display: 'flex',
            alignItems: 'center',
            gap: 4,
          }}
        >
          <GlobalOutlined style={{ color: '#3b82f6' }} /> 所属空间：
        </label>
        <Select
          value={spaceId}
          onChange={(val) => {
            setSpaceId(val)
            setPage(1)
          }}
          style={{ minWidth: 180 }}
          options={[
            { value: '', label: '全部空间' },
            ...spaces.map((s) => ({ value: s.id, label: s.name })),
          ]}
        />
        <span style={{ fontSize: 13, color: '#94a3b8', marginLeft: 8 }}>
          共 {total} 个知识库
        </span>
      </div>

      <Card className="yx-card">
        <div className="yx-toolbar">
          <Input
            prefix={<SearchOutlined />}
            placeholder="搜索知识库名称..."
            value={keywordInput}
            onChange={(e) => {
              setKeywordInput(e.target.value)
              setPage(1)
            }}
            style={{ width: 240 }}
          />
          <Button type="primary" icon={<PlusOutlined />}>
            新建知识库
          </Button>
        </div>
        <Table
          columns={columns}
          dataSource={list}
          rowKey="id"
          pagination={false}
          size="middle"
          loading={loading}
        />
        {/* Custom Pagination */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: 6,
            padding: '16px 0 0',
            borderTop: '1px solid #eef2f6',
            marginTop: 16,
          }}
        >
          <span
            className={`yx-page-btn${page <= 1 ? ' disabled' : ''}`}
            onClick={() => page > 1 && setPage((p) => p - 1)}
            style={{
              width: 34,
              height: 34,
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: 8,
              border: '1px solid #e2e8f0',
              cursor: page <= 1 ? 'not-allowed' : 'pointer',
              color: '#94a3b8',
              fontSize: 12,
              opacity: page <= 1 ? 0.4 : 1,
            }}
          >
            {'<'}
          </span>
          {pageNumbers().map((n) => (
            <span
              key={n}
              className={`yx-page-btn${n === page ? ' active' : ''}`}
              onClick={() => setPage(n)}
              style={{
                width: 34,
                height: 34,
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: 8,
                background: n === page ? '#3b82f6' : 'transparent',
                color: n === page ? '#fff' : '#64748b',
                fontWeight: n === page ? 600 : 400,
                fontSize: 13,
                cursor: 'pointer',
                border: n === page ? 'none' : '1px solid #e2e8f0',
              }}
            >
              {n}
            </span>
          ))}
          <span
            className={`yx-page-btn${page >= totalPages ? ' disabled' : ''}`}
            onClick={() => page < totalPages && setPage((p) => p + 1)}
            style={{
              width: 34,
              height: 34,
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: 8,
              border: '1px solid #e2e8f0',
              cursor: page >= totalPages ? 'not-allowed' : 'pointer',
              color: '#94a3b8',
              fontSize: 12,
              opacity: page >= totalPages ? 0.4 : 1,
            }}
          >
            {'>'}
          </span>
          <span style={{ fontSize: 13, color: '#94a3b8', marginLeft: 12 }}>
            共 {total} 条，{page}/{totalPages} 页
          </span>
        </div>
      </Card>

      {/* Permission Modal */}
      <Modal
        open={permOpen}
        onCancel={() => setPermOpen(false)}
        footer={null}
        width={600}
        closable={false}
        styles={{ body: { padding: 0 } }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '20px 24px',
            borderBottom: '1px solid #eef2f6',
          }}
        >
          <h2
            style={{
              fontSize: 17,
              fontWeight: 600,
              color: '#0b2b5c',
              margin: 0,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <SettingOutlined style={{ color: '#3b82f6' }} /> 知识库权限设置
          </h2>
          <button
            onClick={() => setPermOpen(false)}
            style={{
              width: 32,
              height: 32,
              border: 'none',
              background: '#f1f5f9',
              borderRadius: 8,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#64748b',
              fontSize: 16,
            }}
          >
            <CloseOutlined />
          </button>
        </div>
        <div style={{ padding: '20px 24px' }}>
          <p style={{ fontSize: 14, color: '#475569', marginBottom: 16 }}>
            为知识库{' '}
            <strong style={{ color: '#0b2b5c' }}>{currentKb?.name}</strong>{' '}
            添加成员并设置权限
          </p>
          <Input
            prefix={<SearchOutlined />}
            placeholder="搜索用户或角色..."
            value={permissionKeyword}
            onChange={(e) => handlePermKeywordChange(e.target.value)}
            style={{ marginBottom: 12 }}
          />
          {permLoading ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>
              加载中...
            </div>
          ) : (
            permissionMembers.map((u, i) => {
              const checked = u.role
              return (
                <div
                  key={u.userId}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '10px 12px',
                    borderRadius: 8,
                    border: '1px solid #eef2f6',
                    marginBottom: 8,
                  }}
                >
                  <div
                    style={{
                      width: 32,
                      height: 32,
                      borderRadius: 8,
                      background: u.avatarColor,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#fff',
                      fontSize: 13,
                      fontWeight: 600,
                      flexShrink: 0,
                    }}
                  >
                    {u.avatarText}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 14, fontWeight: 500, color: '#1e293b' }}>
                      {u.name}
                    </div>
                    <div style={{ fontSize: 12, color: '#94a3b8' }}>{u.dept}</div>
                  </div>
                  <div style={{ display: 'flex', gap: 4 }}>
                    {(['view', 'manage'] as const).map((role) => {
                      const isActive = checked === role
                      const label = role === 'view' ? '查看' : '管理'
                      return (
                        <label
                          key={role}
                          style={{
                            padding: '4px 12px',
                            borderRadius: 6,
                            fontSize: 12,
                            border: `1px solid ${isActive ? '#3b82f6' : '#e2e8f0'}`,
                            cursor: 'pointer',
                            color: isActive ? '#3b82f6' : '#64748b',
                            background: isActive ? '#eff6ff' : 'transparent',
                            fontWeight: isActive ? 500 : 400,
                          }}
                        >
                          <input
                            type="radio"
                            name={`perm-${i}`}
                            checked={isActive}
                            onChange={() => handlePermRoleChange(u.userId, role)}
                            style={{ display: 'none' }}
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
        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: 12,
            padding: '16px 24px',
            borderTop: '1px solid #eef2f6',
          }}
        >
          <Button onClick={() => setPermOpen(false)}>取消</Button>
          <Button
            type="primary"
            loading={permSaving}
            onClick={handleSavePermissions}
          >
            保存权限
          </Button>
        </div>
      </Modal>
    </div>
  )
}
