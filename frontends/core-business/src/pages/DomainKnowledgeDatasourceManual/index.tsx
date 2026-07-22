import React, { useState, useEffect, useCallback, useRef, type ChangeEvent } from 'react'
import { Button, Card, Table, Tag, Input, Space, message } from 'antd'
import {
  ArrowLeftOutlined,
  UploadOutlined,
  PlusOutlined,
  FolderOpenOutlined,
  TagOutlined,
  GlobalOutlined,
  FileTextOutlined,
  FileOutlined,
  SearchOutlined,
  SettingOutlined,
  LeftOutlined,
  RightOutlined,
} from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import type { ManualDocItem, DomainKnowledgeDetail as DomainKnowledgeDetailType } from '@/types/domainKnowledge'
import { getDomainKnowledgeDetail } from '@/api/domainKnowledge'
import { getManualDocList, uploadManualDocument } from '@/api/domainKnowledge'

const PAGE_SIZE = 7

const FORMATS = 'PDF, DOCX, XLSX, PPTX, 图片'

export default function DomainKnowledgeDatasourceManual() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  // ── header info ──────────────────────────────────────
  const [detail, setDetail] = useState<DomainKnowledgeDetailType | null>(null)
  const [detailLoading, setDetailLoading] = useState(true)

  // ── doc list ──────────────────────────────────────────
  const [docs, setDocs] = useState<ManualDocItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [keywordInput, setKeywordInput] = useState('')
  const [keyword, setKeyword] = useState('')
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)

  const debounceRef = useRef<ReturnType<typeof setTimeout>>()
  const fileInputRef = useRef<HTMLInputElement>(null)

  // ── fetch header ──────────────────────────────────────
  useEffect(() => {
    if (!id) return
    setDetailLoading(true)
    getDomainKnowledgeDetail(id)
      .then(setDetail)
      .catch((err: any) => message.error(err?.message || '获取知识库信息失败'))
      .finally(() => setDetailLoading(false))
  }, [id])

  // ── fetch doc list ────────────────────────────────────
  const fetchList = useCallback(
    async (p: number, kw: string) => {
      if (!id) return
      setLoading(true)
      try {
        const result = await getManualDocList({
          knowledgeBaseId: id,
          page: p,
          pageSize: PAGE_SIZE,
          keyword: kw || undefined,
        })
        setDocs(result.list)
        setTotal(result.pagination.total)
      } catch (err: any) {
        message.error(err?.message || '获取文档列表失败')
      } finally {
        setLoading(false)
      }
    },
    [id],
  )

  useEffect(() => {
    fetchList(1, '')
  }, [fetchList])

  // ── keyword debounce ──────────────────────────────────
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
    fetchList(1, keyword)
    setPage(1)
  }, [keyword, fetchList])

  // ── pagination ────────────────────────────────────────
  useEffect(() => {
    if (page !== 1) {
      fetchList(page, keyword)
    }
  }, [page])

  // ── upload handler ────────────────────────────────────
  const handleUpload = useCallback(
    async (file: File) => {
      if (!id) return
      setUploading(true)
      try {
        await uploadManualDocument(id, file)
        message.success(`「${file.name}」上传成功`)
        fetchList(1, keyword)
        setPage(1)
      } catch (err: any) {
        message.error(err?.message || '上传失败')
      } finally {
        setUploading(false)
      }
    },
    [id, keyword, fetchList],
  )

  const handleFileChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) handleUpload(file)
      // reset so same file can be re-selected
      e.target.value = ''
    },
    [handleUpload],
  )

  // ── status helper ─────────────────────────────────────
  const STATUS_STEPS = ['入库', '解析', '编译']
  type StepState = 'done' | 'active' | 'pending'
  const stepColors: Record<StepState, { bg: string; text: string }> = {
    done: { bg: '#ecfdf5', text: '#10b981' },
    active: { bg: '#eff6ff', text: '#3b82f6' },
    pending: { bg: '#f1f5f9', text: '#cbd5e1' },
  }

  const getStepStates = (status: string): StepState[] => {
    const steps = status.split('·').map((s) => s.trim())
    const result: StepState[] = ['pending', 'pending', 'pending']
    for (let i = 0; i < Math.min(steps.length, 3); i++) {
      result[i] = steps[i].includes('中') ? 'active' : 'done'
    }
    return result
  }

  const renderStatus = (v: string) => {
    // non-chain status (failed etc.)
    if (!v.includes('·')) {
      const isError = v === 'failed'
      return (
        <Tag
          style={{
            fontSize: 11, padding: '2px 8px', border: 'none', fontWeight: 500,
            background: isError ? '#fef2f2' : '#f1f5f9',
            color: isError ? '#ef4444' : '#64748b',
          }}
        >
          {isError ? '解析失败' : v}
        </Tag>
      )
    }
    // chain status — use plain spans to avoid antd Tag border-radius override
    const states = getStepStates(v)
    return (
      <Space size={4}>
        {STATUS_STEPS.map((label, i) => {
          const s = states[i]
          return (
            <React.Fragment key={i}>
              <span
                style={{
                  display: 'inline-block',
                  fontSize: 11, padding: '2px 8px', border: 'none', fontWeight: 500,
                  background: stepColors[s].bg, color: stepColors[s].text,
                  borderRadius: 4, lineHeight: '18px',
                }}
              >
                {label}
              </span>
              {i < STATUS_STEPS.length - 1 && (
                <span style={{ color: '#d1d5db', fontSize: 10 }}>·</span>
              )}
            </React.Fragment>
          )
        })}
      </Space>
    )
  }

  // ── columns ───────────────────────────────────────────
  const columns = [
    {
      title: '文档名称',
      dataIndex: 'name',
      key: 'name',
      width: 240,
      render: (v: string) => <a className="yx-table-action">{v}</a>,
    },
    { title: '类型', dataIndex: 'type', key: 'type', width: 80 },
    { title: '大小', dataIndex: 'size', key: 'size', width: 90 },
    { title: '上传人', dataIndex: 'uploader', key: 'uploader', width: 90 },
    {
      title: '上传时间',
      dataIndex: 'uploadTime',
      key: 'uploadTime',
      width: 150,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 200,
      render: (v: string) => renderStatus(v),
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: () => (
        <>
          <a className="yx-table-action">查看</a>
          <a className="yx-table-action">删除</a>
        </>
      ),
    },
  ]

  // ── row selection ──────────────────────────────────────
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])

  // ── pagination helpers ────────────────────────────────
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const pageNumbers = (): number[] => {
    const pages: number[] = []
    for (let i = 1; i <= totalPages; i++) pages.push(i)
    return pages
  }

  return (
    <div>
      <a
        onClick={() => navigate(`/domain-knowledge/${id}`)}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          marginBottom: 16,
          fontSize: 14,
          color: '#64748b',
          cursor: 'pointer',
        }}
      >
        <ArrowLeftOutlined /> 返回知识库详情
      </a>

      <Card
        style={{
          borderRadius: 14,
          marginBottom: 24,
          border: '1px solid #eef2f6',
          boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
        }}
        bodyStyle={{
          padding: '20px 24px',
          display: 'flex',
          alignItems: 'center',
          gap: 16,
        }}
      >
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: 12,
            background: '#eff6ff',
            color: '#3b82f6',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 22,
            flexShrink: 0,
          }}
        >
          <UploadOutlined />
        </div>
        <div style={{ flex: 1 }}>
          <h2
            style={{
              fontSize: 18,
              fontWeight: 700,
              color: '#0b2b5c',
              margin: 0,
            }}
          >
            {detailLoading
              ? '加载中...'
              : detail
                ? `${detail.name} · 手动上传`
                : '手动上传数据源'}
          </h2>
          <div
            style={{
              display: 'flex',
              gap: 16,
              marginTop: 4,
              fontSize: 13,
              color: '#64748b',
              flexWrap: 'wrap',
            }}
          >
            <span><TagOutlined style={{ marginRight: 4 }} />手动上传</span>
            <span><GlobalOutlined style={{ marginRight: 4 }} />{detail?.spaceName || '--'}</span>
            <span><FileTextOutlined style={{ marginRight: 4 }} />{total} 文档</span>
            <span><FileOutlined style={{ marginRight: 4 }} />{FORMATS}</span>
          </div>
        </div>
        <Button icon={<SettingOutlined />} style={{ borderRadius: 8, padding: '6px 16px', fontSize: 13, height: 'auto' }}>
          配置
        </Button>
      </Card>

      {/* Upload Zone — native input for full-width */}
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileChange}
        style={{ display: 'none' }}
      />
      <div
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: '2px dashed #cbd5e1',
          borderRadius: 12,
          padding: '40px 20px',
          textAlign: 'center',
          background: '#f8fafc',
          marginBottom: 20,
          cursor: 'pointer',
          transition: 'all 0.2s',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = '#3b82f6'
          e.currentTarget.style.background = '#eff6ff'
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = '#cbd5e1'
          e.currentTarget.style.background = '#f8fafc'
        }}
      >
        {uploading ? (
          <>
            <UploadOutlined
              style={{
                fontSize: 40,
                color: '#3b82f6',
                marginBottom: 12,
              }}
            />
            <p
              style={{ fontSize: 14, color: '#64748b', margin: 0 }}
            >
              正在上传...
            </p>
          </>
        ) : (
          <>
            <UploadOutlined
              style={{
                fontSize: 40,
                color: '#94a3b8',
                marginBottom: 12,
              }}
            />
            <p
              style={{ fontSize: 14, color: '#64748b', margin: 0 }}
            >
              拖拽文件到此处，或点击{' '}
              <strong style={{ color: '#3b82f6' }}>选择文件</strong> 上传
            </p>
            <p
              style={{
                fontSize: 12,
                color: '#94a3b8',
                margin: '4px 0 0',
              }}
            >
              支持 PDF、DOCX、XLSX、PPTX、图片等格式，单文件最大 500MB
            </p>
          </>
        )}
      </div>

      <Card
        style={{
          borderRadius: 14,
          border: '1px solid #eef2f6',
          boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
        }}
        bodyStyle={{ padding: 0 }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 20px',
            borderBottom: '1px solid #eef2f6',
          }}
        >
          <Space>
            <span
              style={{
                fontSize: 14,
                fontWeight: 600,
                color: '#0b2b5c',
              }}
            >
              文档列表
            </span>
            <Input
              prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
              placeholder="搜索文档名称..."
              style={{ width: 240 }}
              value={keywordInput}
              onChange={(e) => {
                setKeywordInput(e.target.value)
                setPage(1)
              }}
            />
          </Space>
          <Space>
            {/* <Button type="primary" icon={<PlusOutlined />} style={{ borderRadius: 8, padding: '6px 16px', fontSize: 13, height: 'auto' }}>
              添加文档
            </Button> */}
            <Button icon={<FolderOpenOutlined />} style={{ borderRadius: 8, padding: '6px 16px', fontSize: 13, height: 'auto' }}>批量上传</Button>
          </Space>
        </div>
        <Table
          columns={columns}
          dataSource={docs}
          rowKey="id"
          pagination={false}
          size="middle"
          loading={loading}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys),
          }}
          components={{
            header: {
              cell: (props: any) => (
                <th
                  {...props}
                  style={{
                    fontSize: 12,
                    color: '#94a3b8',
                    fontWeight: 500,
                    padding: '12px 16px',
                    borderBottom: '1px solid #e2e8f0',
                    background: '#fafcff',
                    ...props.style,
                  }}
                />
              ),
            },
            body: {
              cell: (props: any) => (
                <td
                  {...props}
                  style={{
                    fontSize: 13,
                    color: '#475569',
                    padding: '12px 16px',
                    borderBottom: '1px solid #f1f5f9',
                    ...props.style,
                  }}
                />
              ),
            },
          }}
        />
        {/* Custom Pagination */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: 6,
            padding: '16px 20px',
            borderTop: '1px solid #eef2f6',
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
            <LeftOutlined />
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
            <RightOutlined />
          </span>
          <span style={{ fontSize: 13, color: '#94a3b8', marginLeft: 12 }}>
            共 {total} 条，{page}/{totalPages} 页
          </span>
        </div>
      </Card>
    </div>
  )
}
