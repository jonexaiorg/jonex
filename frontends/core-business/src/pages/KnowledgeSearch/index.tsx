import React, { useCallback, useEffect, useRef, useState } from 'react'
import { Button, Card, Empty, Modal, Spin, message } from 'antd'
import ReactMarkdown from 'react-markdown'
import {
  SearchOutlined,
  ArrowRightOutlined,
  HistoryOutlined,
  BlockOutlined,
  NodeIndexOutlined,
  FileTextOutlined,
  BulbOutlined,
  DatabaseOutlined,
  StopOutlined,
  ReloadOutlined,
  CloseCircleOutlined,
  CaretDownOutlined,
  CaretRightOutlined,
} from '@ant-design/icons'
import {
  getKnowledgeSearchOverview,
  getKnowledgeSearchDomains,
  getKnowledgeSearchHistory,
  saveKnowledgeSearchHistory,
  deleteKnowledgeSearchHistory,
  clearKnowledgeSearchHistory,
  streamKnowledgeSearch,
} from '@/api/knowledgeSearch'
import type {
  KnowledgeSearchOverview,
  KnowledgeSearchDomain,
  KnowledgeSearchHistoryItem,
  KnowledgeSearchRunStatus,
} from '@/types/knowledgeSearch'

const STAT_CARD_CONFIG: {
  key: keyof KnowledgeSearchOverview
  label: string
  Icon: React.ComponentType<any>
  bg: string
  color: string
}[] = [
  { key: 'totalDomains', label: '知识领域', Icon: BlockOutlined, bg: '#eff6ff', color: '#3b82f6' },
  { key: 'totalEntities', label: '知识实体', Icon: NodeIndexOutlined, bg: '#ecfdf5', color: '#10b981' },
  { key: 'sourceFiles', label: '源文件数', Icon: FileTextOutlined, bg: '#f5f3ff', color: '#8b5cf6' },
  { key: 'dataSources', label: '接入数据源', Icon: DatabaseOutlined, bg: '#fff7ed', color: '#f97316' },
]

const EMPTY_OVERVIEW: KnowledgeSearchOverview = {
  totalDocuments: 0,
  totalEntities: 0,
  totalRelations: 0,
  todaySearches: 0,
  avgResponseTimeMs: 0,
  totalDomains: 0,
  sourceFiles: 0,
  dataSources: 0,
}

interface SearchSession {
  id: string
  query: string
  domainId: string
  rawAnswer: string
  status: KnowledgeSearchRunStatus
  errorMessage: string
}

function parseThink(raw: string): { think: string; answer: string; thinking: boolean } {
  const start = raw.indexOf('<think>')
  if (start < 0) return { think: '', answer: raw.trim(), thinking: false }

  const before = raw.slice(0, start)
  const afterStart = raw.slice(start + '<think>'.length)
  const end = afterStart.indexOf('</think>')

  if (end < 0) {
    return { think: afterStart.trim(), answer: before.trim(), thinking: true }
  }

  const think = afterStart.slice(0, end).trim()
  const answer = `${before}${afterStart.slice(end + '</think>'.length)}`.trim()
  return { think, answer, thinking: false }
}

function parseReferences(text: string): { refs: string[]; body: string } {
  const refs: string[] = []
  const normalized = text.replace(/\r\n/g, '\n')
  const sourcePathPattern = /(?:\/app\/inputs\/|\/app\/outputs\/|\/tmp\/rag_output\/)/

  const normalizeReferenceLine = (line: string) =>
    line
      .replace(/^\s*(?:#{1,6}\s*)?(?:References|参考文献|原文引用|引用来源)\s*[:：]?\s*/i, '')
      .replace(/^\s*[-*+]\s*/, '')
      .replace(/^\s*\d+[.)]\s*/, '')
      .replace(/^\s*\[\d+\]\s*/, '')
      .trim()

  const collectRef = (line: string) => {
    const cleaned = normalizeReferenceLine(line)
    if (cleaned) refs.push(cleaned)
  }

  const isReferenceHeading = (line: string) =>
    /^\s{0,3}(?:#{1,6}\s*)?(?:References|参考文献|原文引用|引用来源)\s*[:：]?\s*/i.test(line)
  const hasReferencePayload = (line: string) =>
    sourcePathPattern.test(normalizeReferenceLine(line))
  const isSourcePathLine = (line: string) =>
    sourcePathPattern.test(normalizeReferenceLine(line))

  const bodyLines: string[] = []
  let inReferenceBlock = false

  normalized.split('\n').forEach((line) => {
    if (isReferenceHeading(line)) {
      inReferenceBlock = true
      if (hasReferencePayload(line)) collectRef(line)
      return
    }

    if (inReferenceBlock) {
      if (line.trim()) collectRef(line)
      return
    }

    if (isSourcePathLine(line)) {
      collectRef(line)
      return
    }

    bodyLines.push(line)
  })

  const body = bodyLines
    .join('\n')
    .replace(/^\s*(?:[-*+]\s*)?(?:\d+[.)]\s*)?(?:\[\d+\]\s*)?(?:\/app\/inputs\/|\/app\/outputs\/|\/tmp\/rag_output\/)[^\n]*/gm, (line) => {
      collectRef(line)
      return ''
    })
    .replace(/^\s*(?:[-*+]\s*)?(?:\d+[.)]\s*)?(?:\[\d+\]\s*)?(?:References|参考文献|原文引用|引用来源)\s*[:：]\s*(?:\/app\/inputs\/|\/app\/outputs\/|\/tmp\/rag_output\/)[^\n]*/gim, (line) => {
      collectRef(line)
      return ''
    })
    .trim()

  return { refs: Array.from(new Set(refs)), body }
}

function buildAnswerPreview(raw: string, maxLen = 100): string {
  const { answer } = parseThink(raw)
  const { body } = parseReferences(answer)
  const cleaned = body.replace(/\s+/g, ' ').trim()
  if (!cleaned) return ''
  return cleaned.length > maxLen ? cleaned.slice(0, maxLen) + '...' : cleaned
}

function formatRelativeTime(isoStr: string): string {
  const now = Date.now()
  const then = new Date(isoStr).getTime()
  const diffMs = now - then
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin} 分钟前`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr} 小时前`
  const diffDay = Math.floor(diffHr / 24)
  if (diffDay === 1) return '昨天'
  if (diffDay < 7) return `${diffDay} 天前`
  return isoStr.substring(0, 10)
}

function isSearchRunning(status?: KnowledgeSearchRunStatus): boolean {
  return status === 'searching'
}

function getSearchStatusLabel(status: KnowledgeSearchRunStatus): string {
  switch (status) {
    case 'searching':
      return '检索中'
    case 'done':
      return '已完成'
    case 'error':
      return '检索失败'
    case 'stopped':
      return '已停止'
    case 'empty':
      return '无结果'
    default:
      return '待检索'
  }
}

export default function KnowledgeSearch() {
  const [query, setQuery] = useState('')
  const [selectedDomain, setSelectedDomain] = useState('all')

  const [overview, setOverview] = useState<KnowledgeSearchOverview | null>(null)
  const [domains, setDomains] = useState<KnowledgeSearchDomain[]>([])
  const [history, setHistory] = useState<KnowledgeSearchHistoryItem[]>([])

  const [activeSearch, setActiveSearch] = useState<SearchSession | null>(null)
  const [pageLoading, setPageLoading] = useState(true)
  const [pageError, setPageError] = useState('')
  const [activeHistoryIndex, setActiveHistoryIndex] = useState<number | null>(null)
  const [thinkExpandedMap, setThinkExpandedMap] = useState<Record<string, boolean>>({})

  const abortRef = useRef<AbortController | null>(null)
  const isSearching = isSearchRunning(activeSearch?.status)

  // ── initial data load ──────────────────────────────────
  useEffect(() => {
    let mounted = true

    async function loadInitialData() {
      setPageLoading(true)
      try {
        const results = await Promise.allSettled([
          getKnowledgeSearchOverview(),
          getKnowledgeSearchDomains(),
          getKnowledgeSearchHistory(),
        ] as const)

        if (!mounted) return

        const failedLabels: string[] = []
        const [overviewResult, domainResult, historyResult] = results

        if (overviewResult.status === 'fulfilled') {
          setOverview(overviewResult.value)
        } else {
          failedLabels.push('检索概览')
          setOverview(EMPTY_OVERVIEW)
        }

        if (domainResult.status === 'fulfilled') {
          setDomains(domainResult.value)
        } else {
          failedLabels.push('领域列表')
          setDomains([])
        }

        if (historyResult.status === 'fulfilled') {
          setHistory(historyResult.value)
        } else {
          failedLabels.push('检索历史')
          setHistory([])
        }

        setPageError('')
        if (failedLabels.length) {
          message.warning({
            key: 'knowledge-search-initial-data-warning',
            content: `部分接口请求失败：${failedLabels.join('、')}，已使用空数据展示。`,
          })
        }
        setPageLoading(false)
      } catch (error) {
        if (!mounted) return
        setPageError(error instanceof Error ? error.message : '知识检索数据加载失败')
        setPageLoading(false)
      }
    }

    loadInitialData()

    return () => {
      mounted = false
      abortRef.current?.abort()
    }
  }, [])

  // ── search ─────────────────────────────────────────────
  const handleSearch = useCallback(async (
    nextQuery?: string,
    options?: { keepHistoryActive?: boolean; domainId?: string },
  ) => {
    const trimmedQuery = (nextQuery ?? query).trim()
    if (!trimmedQuery) return

    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    const sessionId = Date.now().toString()
    const domainId = options?.domainId ?? selectedDomain
    const searchParams = { query: trimmedQuery, mode: 'mix' as const, topK: 5, domainId }
    let streamError: Error | null = null
    let accumulatedAnswer = ''
    const startTime = Date.now()

    setQuery(trimmedQuery)
    if (!options?.keepHistoryActive) setActiveHistoryIndex(null)
    setActiveSearch({
      id: sessionId,
      query: trimmedQuery,
      domainId,
      rawAnswer: '',
      status: 'searching',
      errorMessage: '',
    })

    try {
      await streamKnowledgeSearch(
        searchParams,
        {
          onDelta: (delta) => {
            accumulatedAnswer += delta
            setThinkExpandedMap((prev) => {
              if (!delta.includes('<think>')) return prev
              return { ...prev, [sessionId]: true }
            })
            setActiveSearch((prev) =>
              prev?.id === sessionId ? { ...prev, rawAnswer: prev.rawAnswer + delta } : prev,
            )
          },
          onError: (error) => {
            streamError = error
            setActiveSearch((prev) =>
              prev?.id === sessionId
                ? { ...prev, status: 'error' as const, errorMessage: error.message }
                : prev,
            )
          },
        },
        controller.signal,
      )

      if (streamError) throw streamError
      if (controller.signal.aborted) return

      const domainName = getDomainName(domainId)
      const preview = buildAnswerPreview(accumulatedAnswer)
      const { refs } = parseReferences(parseThink(accumulatedAnswer).answer)

      setActiveSearch((prev) =>
        prev?.id === sessionId
          ? { ...prev, status: 'done' as const }
          : prev,
      )
      setThinkExpandedMap((prev) => ({ ...prev, [sessionId]: false }))

      saveKnowledgeSearchHistory({
        query: trimmedQuery,
        domainId,
        domain: domainName,
        answerPreview: preview,
        referenceCount: refs.length,
        resultCount: refs.length,
        status: 'done',
        durationMs: Date.now() - startTime,
      })
        .then((item) => {
          setHistory((prev) => [item, ...prev])
          setActiveHistoryIndex(0)
        })
        .catch(() => {
          // save failed, silently ignore
        })
    } catch (error) {
      if (controller.signal.aborted) return
      const msg = error instanceof Error ? error.message : '知识检索失败'
      setActiveSearch((prev) =>
        prev?.id === sessionId
          ? { ...prev, status: 'error' as const, errorMessage: msg }
          : prev,
      )
      setThinkExpandedMap((prev) => ({ ...prev, [sessionId]: false }))
    } finally {
      if (abortRef.current === controller) abortRef.current = null
    }
  }, [query, selectedDomain])

  const handleHistoryClick = useCallback(
    (item: KnowledgeSearchHistoryItem, index: number) => {
      setQuery(item.query)
      setActiveHistoryIndex(index)
      if (item.domainId) setSelectedDomain(item.domainId)
      void handleSearch(item.query, {
        keepHistoryActive: true,
        domainId: item.domainId ?? selectedDomain,
      })
    },
    [handleSearch, selectedDomain],
  )

  const handleStopSearch = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setActiveSearch((prev) => {
      if (!prev || !isSearchRunning(prev.status)) return prev
      setThinkExpandedMap((map) => ({ ...map, [prev.id]: false }))
      return { ...prev, status: 'stopped' as const }
    })
    message.info('已停止本次检索')
  }, [])

  const handleClearSearch = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setActiveSearch(null)
    setActiveHistoryIndex(null)
  }, [])

  const handleDomainChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedDomain(e.target.value)
  }, [])

  const handleDeleteHistory = useCallback(
    (id: string, index: number) => {
      deleteKnowledgeSearchHistory(id)
        .then(() => {
          setHistory((prev) => prev.filter((h) => h.id !== id))
          if (activeHistoryIndex === index) setActiveHistoryIndex(null)
        })
        .catch(() => {})
    },
    [activeHistoryIndex],
  )

  const handleClearHistory = useCallback(() => {
    Modal.confirm({
      title: '清空检索历史',
      content: '确认清空全部检索历史？此操作不可撤销。',
      okText: '确认清空',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: () => {
        clearKnowledgeSearchHistory()
          .then(() => {
            setHistory([])
            setActiveHistoryIndex(null)
          })
          .catch(() => {})
      },
    })
  }, [])

  const getDomainName = useCallback(
    (domainId?: string) => domains.find((d) => d.id === domainId)?.name ?? '全领域检索',
    [domains],
  )

  // ── render helpers ─────────────────────────────────────

  const renderStats = () => (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16, marginBottom: 28 }}>
      {STAT_CARD_CONFIG.map((cfg) => {
        const value = overview ? overview[cfg.key] : '-'
        const displayValue = typeof value === 'number' ? value.toLocaleString() : value
        return (
          <Card
            key={cfg.key}
            style={{ borderRadius: 12 }}
            styles={{
              body: { padding: '18px 20px', display: 'flex', alignItems: 'center', gap: 14 },
            }}
          >
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: 12,
                background: cfg.bg,
                color: cfg.color,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 22,
                flexShrink: 0,
              }}
            >
              <cfg.Icon />
            </div>
            <div>
              <div style={{ fontSize: 22, fontWeight: 700, color: '#0b2b5c', lineHeight: 1.2 }}>
                {pageLoading ? '-' : displayValue}
              </div>
              <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 2 }}>{cfg.label}</div>
            </div>
          </Card>
        )
      })}
    </div>
  )

  const renderSearchPanel = () => (
    <Card style={{ borderRadius: 16, marginBottom: 24 }} styles={{ body: { padding: '24px 28px' } }}>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '0 16px',
            background: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: 10,
            height: 48,
            flexShrink: 0,
          }}
        >
          <BlockOutlined style={{ color: '#3b82f6', fontSize: 16 }} />
          <select
            className="filter-select"
            value={selectedDomain}
            onChange={handleDomainChange}
            style={{
              border: 'none',
              background: 'transparent',
              fontSize: 14,
              color: '#1e293b',
              outline: 'none',
              cursor: 'pointer',
              fontWeight: 500,
              minWidth: 120,
            }}
          >
            {!domains.some((d) => d.id === 'all') && (
              <option value="all">全领域检索</option>
            )}
            {domains.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </div>
        <div style={{ flex: 1, position: 'relative' }}>
          <SearchOutlined
            style={{
              position: 'absolute',
              left: 16,
              top: '50%',
              transform: 'translateY(-50%)',
              color: '#94a3b8',
              fontSize: 16,
              zIndex: 1,
            }}
          />
          <input
            type="text"
            placeholder="输入检索关键词，如「设备故障诊断」「风险评估模型」…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                void handleSearch()
              }
            }}
            style={{
              width: '100%',
              height: 48,
              padding: '0 16px 0 44px',
              border: '1px solid #e2e8f0',
              borderRadius: 10,
              fontSize: 15,
              outline: 'none',
              background: '#f8fafc',
              boxSizing: 'border-box',
            }}
          />
        </div>
        <Button
          type="primary"
          icon={<ArrowRightOutlined />}
          onClick={() => void handleSearch()}
          loading={isSearching}
          style={{ height: 48, padding: '0 28px', fontSize: 15, borderRadius: 10, flexShrink: 0 }}
        >
          检索
        </Button>
        {isSearching && (
          <Button
            icon={<StopOutlined />}
            onClick={handleStopSearch}
            style={{ height: 48, padding: '0 18px', fontSize: 15, borderRadius: 10, flexShrink: 0 }}
          >
            停止
          </Button>
        )}
      </div>
    </Card>
  )

  const renderSessionCard = (session: SearchSession) => {
    const parsedAnswer = parseThink(session.rawAnswer)
    const { refs, body: responseBody } = parseReferences(parsedAnswer.answer)
    const running = isSearchRunning(session.status)
    const hasThink = parsedAnswer.think.length > 0
    const hasAnswerContent = responseBody.length > 0
    const hasContent = hasThink || hasAnswerContent
    const thinkExpanded = parsedAnswer.thinking || thinkExpandedMap[session.id] === true
    const domainName = getDomainName(session.domainId)
    const statusLabel = getSearchStatusLabel(session.status)

    return (
      <Card
        key={session.id}
        style={{ borderRadius: 12, marginBottom: 20 }}
        styles={{ body: { padding: '20px 24px' } }}
      >
        <div
          style={{
            marginBottom: 16,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 12,
          }}
        >
          <div
            style={{
              minWidth: 0,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 16,
              fontWeight: 600,
              color: '#0b2b5c',
            }}
          >
            <SearchOutlined style={{ color: '#3b82f6', flexShrink: 0 }} />
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {session.query}
            </span>
            <span
              style={{
                fontSize: 12,
                color: '#64748b',
                fontWeight: 400,
                background: '#f1f5f9',
                borderRadius: 999,
                padding: '2px 8px',
                flexShrink: 0,
              }}
            >
              {domainName}
            </span>
            {running && (
              <span style={{ fontSize: 12, color: '#94a3b8', fontWeight: 400, marginLeft: 8, flexShrink: 0 }}>
                <Spin size="small" style={{ marginRight: 4 }} />
                检索中...
              </span>
            )}
            {session.status === 'error' && (
              <span style={{ fontSize: 12, color: '#ef4444', fontWeight: 400, flexShrink: 0 }}>
                {statusLabel}
              </span>
            )}
            {session.status === 'stopped' && (
              <span style={{ fontSize: 12, color: '#f97316', fontWeight: 400, flexShrink: 0 }}>
                {statusLabel}
              </span>
            )}
            {session.status === 'done' && (
              <span style={{ fontSize: 12, color: '#10b981', fontWeight: 400, flexShrink: 0 }}>
                {statusLabel}
              </span>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
            {running ? (
              <Button size="small" icon={<StopOutlined />} onClick={handleStopSearch}>
                停止生成
              </Button>
            ) : (
              <Button
                size="small"
                icon={<ReloadOutlined />}
                onClick={() => void handleSearch(session.query, { domainId: session.domainId })}
              >
                重新检索
              </Button>
            )}
            <Button size="small" icon={<CloseCircleOutlined />} onClick={handleClearSearch}>
              清空
            </Button>
          </div>
        </div>

        {session.status === 'error' && (
          <div
            style={{
              padding: '12px 14px',
              background: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: 10,
              color: '#dc2626',
              fontSize: 13,
              marginBottom: 16,
              lineHeight: 1.7,
            }}
          >
            {session.errorMessage || '知识检索失败，请稍后重试'}
          </div>
        )}

        {/* Thinking stream */}
        {hasThink && (
          <div
            style={{
              padding: '12px 14px',
              background: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: 10,
              marginBottom: 12,
            }}
          >
            <button
              type="button"
              onClick={() =>
                setThinkExpandedMap((prev) => ({
                  ...prev,
                  [session.id]: !thinkExpanded,
                }))
              }
              style={{
                width: '100%',
                border: 'none',
                background: 'transparent',
                padding: 0,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                cursor: 'pointer',
                color: '#64748b',
                textAlign: 'left',
              }}
            >
              {thinkExpanded ? <CaretDownOutlined /> : <CaretRightOutlined />}
              <span style={{ fontSize: 13, fontWeight: 600, color: '#475569' }}>思考过程</span>
              {parsedAnswer.thinking ? (
                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 4,
                    fontSize: 12,
                    color: '#94a3b8',
                  }}
                >
                  <Spin size="small" />
                  生成中
                </span>
              ) : (
                <span style={{ fontSize: 12, color: '#94a3b8' }}>
                  {thinkExpanded ? '点击折叠' : '已折叠'}
                </span>
              )}
            </button>
            {thinkExpanded ? (
              <div
                style={{
                  marginTop: 10,
                  padding: '10px 12px',
                  background: '#ffffff',
                  borderRadius: 8,
                  fontSize: 13,
                  color: '#64748b',
                  lineHeight: 1.75,
                  whiteSpace: 'pre-wrap',
                }}
              >
                {parsedAnswer.think}
              </div>
            ) : (
              <div
                style={{
                  marginTop: 8,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  fontSize: 12,
                  color: '#94a3b8',
                }}
              >
                {parsedAnswer.think.split('\n').find(Boolean) || '已完成推理分析'}
              </div>
            )}
          </div>
        )}

        {/* Streamed answer */}
        {(responseBody || running) && (
          <div
            style={{
              padding: '14px 16px',
              background: '#fafcff',
              border: '1px solid #e8edf5',
              borderRadius: 10,
              marginBottom: 16,
            }}
          >
            <div
              style={{
                fontSize: 13,
                fontWeight: 600,
                color: '#6366f1',
                marginBottom: 10,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <BulbOutlined />
              检索结果
              <span style={{ fontWeight: 400, fontSize: 12, color: '#94a3b8' }}>
                基于知识库的关联分析 · {domainName}
              </span>
            </div>
            <div style={{ fontSize: 14, color: '#334155', lineHeight: 1.8 }}>
              <ReactMarkdown
                components={{
                  h1: ({ children }) => (
                    <h1 style={{ fontSize: 20, lineHeight: 1.45, margin: '12px 0 8px', color: '#0f172a' }}>
                      {children}
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 style={{ fontSize: 18, lineHeight: 1.5, margin: '12px 0 8px', color: '#0f172a' }}>
                      {children}
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 style={{ fontSize: 16, lineHeight: 1.5, margin: '10px 0 6px', color: '#0f172a' }}>
                      {children}
                    </h3>
                  ),
                  p: ({ children }) => <p style={{ margin: '0 0 10px' }}>{children}</p>,
                  ul: ({ children }) => <ul style={{ margin: '0 0 10px', paddingLeft: 20 }}>{children}</ul>,
                  ol: ({ children }) => <ol style={{ margin: '0 0 10px', paddingLeft: 20 }}>{children}</ol>,
                  li: ({ children }) => <li style={{ marginBottom: 4 }}>{children}</li>,
                  strong: ({ children }) => <strong style={{ color: '#0f172a' }}>{children}</strong>,
                }}
              >
                {responseBody || (running ? '正在分析...' : '')}
              </ReactMarkdown>
            </div>
            {running && hasContent && (
              <div style={{ marginTop: 8 }}>
                <Spin size="small" />
              </div>
            )}
          </div>
        )}

        {/* References — citation block */}
        {refs.length > 0 && (
          <div
            style={{
              background: '#f8fafc',
              borderLeft: '3px solid #3b82f6',
              borderRadius: '0 8px 8px 0',
              padding: '14px 18px',
              marginBottom: 16,
            }}
          >
            <div
              style={{
                fontSize: 12,
                color: '#3b82f6',
                fontWeight: 600,
                marginBottom: 6,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              原文引用
            </div>
            {refs.map((ref, i) => (
              <div
                key={i}
                style={{ fontSize: 13, color: '#64748b', lineHeight: 1.8, fontStyle: 'italic' }}
              >
                {ref}
              </div>
            ))}
          </div>
        )}

        {/* Searching spinner when no content yet */}
        {running && !hasContent && (
          <div style={{ textAlign: 'center', padding: '30px 0' }}>
            <Spin size="default" />
            <div style={{ marginTop: 10, color: '#94a3b8', fontSize: 13 }}>正在检索相关知识...</div>
          </div>
        )}
      </Card>
    )
  }

  const renderHistorySidebar = () => (
    <div
      style={{
        width: 280,
        flexShrink: 0,
        background: '#fff',
        borderRadius: 12,
        border: '1px solid #eef2f6',
        boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
        overflow: 'hidden',
        position: 'sticky',
        top: 28,
      }}
    >
      <div
        style={{
          padding: '16px 20px',
          fontSize: 15,
          fontWeight: 600,
          color: '#0b2b5c',
          borderBottom: '1px solid #f1f5f9',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <HistoryOutlined />
        检索历史
        {history.length > 0 && (
          <button
            type="button"
            onClick={handleClearHistory}
            style={{
              marginLeft: 'auto',
              border: 'none',
              background: 'transparent',
              color: '#94a3b8',
              fontSize: 12,
              cursor: 'pointer',
              padding: 0,
            }}
          >
            清空
          </button>
        )}
      </div>
      {history.length === 0 ? (
        <div
          style={{
            padding: '40px 20px',
            textAlign: 'center',
            color: '#94a3b8',
            fontSize: 13,
          }}
        >
          暂无检索历史
        </div>
      ) : (
        history.map((h, i) => (
          <div
            key={h.id}
            style={{
              padding: '14px 20px',
              borderBottom: i < history.length - 1 ? '1px solid #f8fafc' : 'none',
              cursor: 'pointer',
              transition: 'background 0.2s',
              background: activeHistoryIndex === i ? '#eff6ff' : undefined,
              borderLeft: activeHistoryIndex === i ? '3px solid #3b82f6' : '3px solid transparent',
              display: 'flex',
              alignItems: 'flex-start',
              gap: 8,
            }}
          >
            <div
              onClick={() => handleHistoryClick(h, i)}
              style={{ flex: 1, minWidth: 0 }}
            >
              <div
                style={{
                  fontSize: 13,
                  fontWeight: 500,
                  color: '#1e293b',
                  marginBottom: 4,
                  lineHeight: 1.4,
                }}
              >
                {h.query}
              </div>
              <div style={{ display: 'flex', gap: 10, fontSize: 11, color: '#94a3b8' }}>
                <span>{h.resultCount} 条结果</span>
                <span>{formatRelativeTime(h.searchedAt)}</span>
              </div>
            </div>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                handleDeleteHistory(h.id, i)
              }}
              style={{
                border: 'none',
                background: 'transparent',
                color: '#cbd5e1',
                cursor: 'pointer',
                padding: '2px 4px',
                fontSize: 14,
                flexShrink: 0,
                lineHeight: 1,
              }}
              title="删除此条历史"
            >
              ×
            </button>
          </div>
        ))
      )}
    </div>
  )

  const renderMainContent = () => {
    if (pageLoading) {
      return (
        <div style={{ textAlign: 'center', padding: '80px 0' }}>
          <Spin size="large" />
        </div>
      )
    }

    if (pageError) {
      return (
        <div style={{ textAlign: 'center', padding: '80px 0' }}>
          <div style={{ color: '#ef4444', fontSize: 14, marginBottom: 12 }}>{pageError}</div>
          <Button onClick={() => window.location.reload()}>刷新页面</Button>
        </div>
      )
    }

    if (!activeSearch) {
      return (
        <Card style={{ borderRadius: 12 }} styles={{ body: { padding: '60px 20px' } }}>
          <Empty description="输入关键词或选择领域开始智能检索" />
        </Card>
      )
    }

    return renderSessionCard(activeSearch)
  }

  // ── main render ────────────────────────────────────────
  return (
    <div>
      <div className="yx-page-title">
        <h1>领域知识检索</h1>
        <p className="yx-page-subtitle">选择业务领域，检索知识内容</p>
      </div>

      {renderStats()}
      {renderSearchPanel()}

      <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          {renderMainContent()}
        </div>
        {renderHistorySidebar()}
      </div>

      <div style={{ textAlign: 'center', padding: '32px 0 8px', fontSize: 13, color: '#cbd5e1' }}>
        Jonex智能知识平台 &copy; 2026 — 以知识驱动智能
      </div>
    </div>
  )
}
