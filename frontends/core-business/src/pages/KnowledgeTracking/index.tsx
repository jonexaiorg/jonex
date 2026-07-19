import React, { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Button, Card, Empty, Modal, Spin, message } from 'antd'
import {
  ArrowLeftOutlined,
  LikeOutlined,
  DislikeOutlined,
  CheckCircleOutlined,
  CheckCircleFilled,
  EyeOutlined,
} from '@ant-design/icons'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import {
  getSearchFeedbackList,
  getSearchFeedbackStats,
  toggleSearchFeedbackAdopted,
  cancelSearchFeedback,
} from '@/api/knowledgeSearch'
import type {
  SearchFeedbackItem,
  SearchFeedbackListResponse,
  SearchFeedbackStats,
  SearchFeedbackType,
} from '@/types/knowledgeSearch'

type TabKey = 'all' | 'like' | 'dislike'

const TAB_CONFIG: { key: TabKey; tKey: string; icon: React.ReactNode; color: string }[] = [
  { key: 'all', tKey: 'knowledgeTracking.all', icon: null, color: '#3b82f6' },
  { key: 'like', tKey: 'knowledgeTracking.helpful', icon: <LikeOutlined />, color: '#059669' },
  { key: 'dislike', tKey: 'knowledgeTracking.unhelpful', icon: <DislikeOutlined />, color: '#dc2626' },
]

export default function KnowledgeTracking() {
  const { t } = useTranslation()
  const { id: knowledgeBaseId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<TabKey>('all')


  const [feedbackData, setFeedbackData] = useState<SearchFeedbackListResponse | null>(null)
  const [stats, setStats] = useState<SearchFeedbackStats | null>(null)


  const [viewModal, setViewModal] = useState<{ open: boolean; item: SearchFeedbackItem | null }>({
    open: false,
    item: null,
  })


  const kbName = searchParams.get('name') || t('knowledgeTracking.knowledgeBaseFallback')

  const loadData = useCallback(async () => {
    if (!knowledgeBaseId) return
    setLoading(true)
    setError('')
    try {
      const feedbackType = activeTab === 'all' ? undefined : activeTab
      const [listResult, statsResult] = await Promise.all([
        getSearchFeedbackList(knowledgeBaseId, { feedbackType, page: 1, pageSize: 50 }),
        getSearchFeedbackStats(knowledgeBaseId),
      ])
      setFeedbackData(listResult)
      setStats(statsResult)
    } catch (err) {
      setError(err instanceof Error ? err.message : t('common.loadFailed'))
    } finally {
      setLoading(false)
    }
  }, [knowledgeBaseId, activeTab, t])

  useEffect(() => {
    void loadData()
  }, [loadData])

  const handleToggleAdopt = useCallback(
    async (item: SearchFeedbackItem) => {
      try {
        await toggleSearchFeedbackAdopted(item.id)

        setFeedbackData((prev) => {
          if (!prev) return prev
          return {
            ...prev,
            items: prev.items.map((i) =>
              i.id === item.id ? { ...i, adopted: !i.adopted } : i,
            ),
          }
        })
        message.success(item.adopted ? t('knowledgeTracking.adoptCanceled') : t('knowledgeTracking.adopted'))
      } catch {
        message.error(t('knowledgeTracking.operationFailed'))
      }
    },
    [],
  )

  const handleView = useCallback((item: SearchFeedbackItem) => {
    setViewModal({ open: true, item })
  }, [])


  const handleDeleteFeedback = useCallback(
    async (item: SearchFeedbackItem) => {
      Modal.confirm({
        title: t('knowledgeTracking.feedbackDeleted'),
        content: t('validation.confirmDelete'),
        okText: t('validation.confirmDelete'),
        okButtonProps: { danger: true },
        cancelText: t('dataSource.cancel'),
        onOk: async () => {
          try {
            await cancelSearchFeedback({
              sessionId: item.session_id,
              feedbackType: item.feedback_type,
              kbIds: [item.knowledge_base_id],
            })

            setFeedbackData((prev) => {
              if (!prev) return prev
              const newItems = prev.items.filter((i) => i.id !== item.id)

              const likeCount = item.feedback_type === 'like' ? prev.like_count - 1 : prev.like_count
              const dislikeCount = item.feedback_type === 'dislike' ? prev.dislike_count - 1 : prev.dislike_count
              return {
                ...prev,
                items: newItems,
                total: prev.total - 1,
                like_count: Math.max(0, likeCount),
                dislike_count: Math.max(0, dislikeCount),
              }
            })
            message.success(t('knowledgeTracking.feedbackDeleted'))
          } catch {
            message.error(t('knowledgeTracking.deleteFailed'))
          }
        },
      })
    },
    [],
  )



  const renderStats = () => {
    const cards = [
      {
        label: t('knowledgeTracking.totalFeedback'),
        value: stats?.total ?? '-',
        icon: null,
        bg: '#eff6ff',
        color: '#3b82f6',
      },
      {
        label: t('knowledgeTracking.helpful'),
        value: stats?.like_count ?? '-',
        icon: <LikeOutlined />,
        bg: '#ecfdf5',
        color: '#059669',
      },
      {
        label: t('knowledgeTracking.unhelpful'),
        value: stats?.dislike_count ?? '-',
        icon: <DislikeOutlined />,
        bg: '#fef2f2',
        color: '#dc2626',
      },
      {
        label: t('knowledgeTracking.positiveRate'),
        value:
          stats && stats.total > 0
            ? `${((stats.like_count / stats.total) * 100).toFixed(1)}%`
            : '-',
        icon: null,
        bg: '#f5f3ff',
        color: '#7c3aed',
      },
    ]

    return (
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        {cards.map((c) => (
          <Card
            key={c.label}
            style={{ borderRadius: 12 }}
            styles={{ body: { padding: '18px 20px', display: 'flex', alignItems: 'center', gap: 14 } }}
          >
            {c.icon && (
              <div
                style={{
                  width: 42,
                  height: 42,
                  borderRadius: 10,
                  background: c.bg,
                  color: c.color,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 18,
                  flexShrink: 0,
                }}
              >
                {c.icon}
              </div>
            )}
            <div>
              <div
                style={{
                  fontSize: 24,
                  fontWeight: 700,
                  color: '#0b2b5c',
                  lineHeight: 1.2,
                }}
              >
                {loading ? '-' : c.value}
              </div>
              <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 2 }}>{c.label}</div>
            </div>
          </Card>
        ))}
      </div>
    )
  }



  const renderTabs = () => (
    <div
      style={{
        display: 'flex',
        gap: 0,
        borderBottom: '2px solid #eef2f6',
        marginBottom: 20,
      }}
    >
      {TAB_CONFIG.map((tab) => {
        const isActive = activeTab === tab.key
        return (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: '10px 24px',
              fontSize: 14,
              fontWeight: 500,
              color: isActive ? tab.color : '#94a3b8',
              cursor: 'pointer',
              borderBottom: `2px solid ${isActive ? tab.color : 'transparent'}`,
              marginBottom: -2,
              transition: 'all 0.2s',
              background: 'none',
              borderTop: 'none',
              borderLeft: 'none',
              borderRight: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            {tab.icon}
            {t(tab.tKey)}
          </button>
        )
      })}
    </div>
  )



  const formatTime = (iso: string | null) => {
    if (!iso) return '-'
    try {
      const d = new Date(iso)
      const pad = (n: number) => String(n).padStart(2, '0')
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
    } catch {
      return iso
    }
  }

  const truncateText = (text: string | null, max = 80) => {
    if (!text) return '-'
    const cleaned = text.replace(/\s+/g, ' ').trim()
    return cleaned.length > max ? cleaned.slice(0, max) + '...' : cleaned
  }



  const renderTable = () => {
    const items = feedbackData?.items ?? []

    if (items.length === 0) {
      return (
        <div style={{ padding: '60px 0' }}>
          <Empty description={t('knowledgeTracking.noFeedback')} />
        </div>
      )
    }

    const tableStyle: React.CSSProperties = {
      width: '100%',
      borderCollapse: 'collapse',
      fontSize: 13,
    }

    const thStyle: React.CSSProperties = {
      textAlign: 'left',
      padding: '10px 12px',
      fontWeight: 600,
      color: '#64748b',
      borderBottom: '1px solid #eef2f6',
      fontSize: 12,
    }

    const tdStyle: React.CSSProperties = {
      padding: '12px',
      borderBottom: '1px solid #f8fafc',
      color: '#475569',
      verticalAlign: 'top',
    }

    return (
      <div style={{ overflowX: 'auto' }}>
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={{ ...thStyle, width: 150 }}>{t('dataSource.documentTime')}</th>
              <th style={{ ...thStyle, width: '25%' }}>{t('knowledgeSearch.fileName')}</th>
              <th style={{ ...thStyle, width: '35%' }}>{t('knowledgeSearch.compileResults')}</th>
              <th style={{ ...thStyle, width: 130 }}>{t('knowledgeSearch.fileType')}</th>
              <th style={{ ...thStyle, width: 120 }}>{t('domainService.status')}</th>
              <th style={{ ...thStyle, width: 120 }}>{t('knowledgeSearch.actions')}</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr
                key={item.id}
                style={{ cursor: 'default' }}
                onMouseEnter={(e) => {
                  ;(e.currentTarget as HTMLElement).style.background = '#fafcff'
                }}
                onMouseLeave={(e) => {
                  ;(e.currentTarget as HTMLElement).style.background = ''
                }}
              >
                <td style={{ ...tdStyle, whiteSpace: 'nowrap', color: '#94a3b8', fontSize: 12 }}>
                  {formatTime(item.searched_at)}
                </td>
                <td style={{ ...tdStyle, fontWeight: 500, color: '#1e293b', maxWidth: 200 }}>
                  <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={item.query}>
                    {item.query}
                  </div>
                </td>
                <td style={{ ...tdStyle, maxWidth: 300, color: '#64748b', fontSize: 12, lineHeight: 1.6 }}>
                  <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                    {truncateText(item.answer_preview, 120)}
                  </div>
                </td>
                <td style={tdStyle}>
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 4,
                      padding: '2px 10px',
                      borderRadius: 6,
                      fontSize: 12,
                      fontWeight: 500,
                      background: item.feedback_type === 'like' ? '#ecfdf5' : '#fef2f2',
                      color: item.feedback_type === 'like' ? '#059669' : '#dc2626',
                    }}
                  >
                    {item.feedback_type === 'like' ? <LikeOutlined /> : <DislikeOutlined />}
                    {item.feedback_type === 'like' ? t('knowledgeTracking.helpful') : t('knowledgeTracking.unhelpful')}
                  </span>
                </td>
                <td style={tdStyle}>
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 4,
                      fontSize: 12,
                      color: item.adopted ? '#059669' : '#94a3b8',
                    }}
                  >
                    {item.adopted ? <CheckCircleFilled style={{ color: '#059669' }} /> : <CheckCircleOutlined />}
                    {item.adopted ? t('knowledgeTracking.adopted') : t('knowledgeTracking.notAdopted')}
                  </span>
                </td>
                <td style={tdStyle}>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button
                      type="button"
                      onClick={() => handleView(item)}
                      style={{
                        padding: '3px 12px',
                        fontSize: 12,
                        color: '#64748b',
                        background: '#f1f5f9',
                        border: '1px solid #e2e8f0',
                        borderRadius: 6,
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        transition: 'all 0.2s',
                      }}
                      onMouseEnter={(e) => {
                        ;(e.target as HTMLElement).style.background = '#e2e8f0'
                      }}
                      onMouseLeave={(e) => {
                        ;(e.target as HTMLElement).style.background = '#f1f5f9'
                      }}
                    >
                      <EyeOutlined /> {t('knowledgeTracking.view')}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleToggleAdopt(item)}
                      style={{
                        padding: '3px 12px',
                        fontSize: 12,
                        color: item.adopted ? '#059669' : '#3b82f6',
                        background: item.adopted ? '#ecfdf5' : '#eff6ff',
                        border: `1px solid ${item.adopted ? '#a7f3d0' : '#bfdbfe'}`,
                        borderRadius: 6,
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        transition: 'all 0.2s',
                      }}
                    >
                      {item.adopted ? t('knowledgeTracking.adopted') : t('knowledgeTracking.adopt')}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeleteFeedback(item)}
                      style={{
                        padding: '3px 12px',
                        fontSize: 12,
                        color: '#ef4444',
                        background: '#fef2f2',
                        border: '1px solid #fecaca',
                        borderRadius: 6,
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        transition: 'all 0.2s',
                      }}
                      onMouseEnter={(e) => {
                        ;(e.target as HTMLElement).style.background = '#fee2e2'
                      }}
                      onMouseLeave={(e) => {
                        ;(e.target as HTMLElement).style.background = '#fef2f2'
                      }}
                    >
                      {t('common.delete')}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }



  return (
    <div>
      { }
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          marginBottom: 24,
        }}
      >
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate(-1)}
          style={{
            fontSize: 14,
            color: '#64748b',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            borderRadius: 8,
          }}
        >
          {t('common.back')}
        </Button>
        <h1
          style={{
            fontSize: 22,
            fontWeight: 700,
            color: '#0b2b5c',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          {t('knowledgeTracking.title')}
          <span style={{ fontSize: 14, fontWeight: 400, color: '#94a3b8' }}>
            — {kbName}
          </span>
        </h1>
      </div>

      { }
      {renderStats()}

      { }
      <Card style={{ borderRadius: 12 }} styles={{ body: { padding: '20px 24px' } }}>
        {renderTabs()}

        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px 0' }}>
            <Spin size="large" />
          </div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: '60px 0' }}>
            <div style={{ color: '#ef4444', fontSize: 14, marginBottom: 12 }}>{error}</div>
            <Button onClick={() => void loadData()}>{t('common.retry')}</Button>
          </div>
        ) : (
          renderTable()
        )}
      </Card>

      { }
      <Modal
        title={
          <span style={{ fontSize: 16, fontWeight: 600, color: '#0b2b5c' }}>
            {t('knowledgeTracking.feedbackDetail')}
          </span>
        }
        open={viewModal.open}
        onCancel={() => setViewModal({ open: false, item: null })}
        footer={
          <Button onClick={() => setViewModal({ open: false, item: null })}>
            {t('common.close')}
          </Button>
        }
        width={600}
      >
        {viewModal.item && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#0b2b5c', marginBottom: 6 }}>
                {t('knowledgeTracking.question')}
              </label>
              <div
                style={{
                  padding: '12px 14px',
                  background: '#f8fafc',
                  border: '1px solid #eef2f6',
                  borderRadius: 8,
                  fontSize: 14,
                  color: '#0b2b5c',
                  lineHeight: 1.6,
                }}
              >
                {viewModal.item.query}
              </div>
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#0b2b5c', marginBottom: 6 }}>
                {t('knowledgeTracking.answerSummary')}
              </label>
              <div
                style={{
                  padding: '12px 14px',
                  background: '#f8fafc',
                  border: '1px solid #eef2f6',
                  borderRadius: 8,
                  fontSize: 14,
                  color: '#475569',
                  lineHeight: 1.6,
                  maxHeight: 300,
                  overflow: 'auto',
                }}
              >
                {viewModal.item.answer_preview || t('knowledgeTracking.noSummary')}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 20, fontSize: 13, color: '#94a3b8' }}>
              <span>
                {t('knowledgeTracking.searchTime')}：{formatTime(viewModal.item.searched_at)}
              </span>
              <span>
                {t('knowledgeTracking.feedbackType')}：
                {viewModal.item.feedback_type === 'like' ? t('knowledgeTracking.helpful') : t('knowledgeTracking.unhelpful')}
              </span>
              <span>
                {t('domainService.status')}：{viewModal.item.adopted ? t('knowledgeTracking.adopted') : t('knowledgeTracking.notAdopted')}
              </span>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
