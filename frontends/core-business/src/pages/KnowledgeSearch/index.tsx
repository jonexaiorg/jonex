import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { Button, Card, Empty, Modal, Spin, message } from 'antd'
import { observer } from 'mobx-react-lite'
import { useStore } from '@/store'
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
  LikeOutlined,
  LikeFilled,
  DislikeOutlined,
  DislikeFilled,
  LoadingOutlined,
} from '@ant-design/icons'
import {
  getKnowledgeSearchOverview,
  getKnowledgeSearchDomains,
  getKnowledgeSearchHistory,
  saveKnowledgeSearchHistory,
  deleteKnowledgeSearchHistory,
  clearKnowledgeSearchHistory,
  streamKnowledgeSearch,
  submitSearchFeedback,
  cancelSearchFeedback,
} from '@/api/knowledgeSearch'
import { useDocumentViewer } from '@/components/DocumentViewer'
import type {
  KnowledgeSearchOverview,
  KnowledgeSearchDomain,
  KnowledgeSearchHistoryItem,
  KnowledgeSearchRunStatus,
  KnowledgeReference,
  KnowledgeReferenceLocation,
  ReasoningTrace,
  ReasoningStep,
  SearchFeedbackType,
  SubmitSearchFeedbackParams,
} from '@/types/knowledgeSearch'

const STAT_CARD_CONFIG: {
  key: keyof KnowledgeSearchOverview
  labelKey: string
  Icon: React.ComponentType<any>
  bg: string
  color: string
}[] = [
  { key: 'totalDomains', labelKey: 'knowledgeSearch.stats.domains', Icon: BlockOutlined, bg: '#eff6ff', color: '#3b82f6' },
  { key: 'totalEntities', labelKey: 'knowledgeSearch.stats.entities', Icon: NodeIndexOutlined, bg: '#ecfdf5', color: '#10b981' },
  { key: 'sourceFiles', labelKey: 'knowledgeSearch.stats.sourceFiles', Icon: FileTextOutlined, bg: '#f5f3ff', color: '#8b5cf6' },
  { key: 'dataSources', labelKey: 'knowledgeSearch.stats.dataSources', Icon: DatabaseOutlined, bg: '#fff7ed', color: '#f97316' },
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
  source?: string
  references?: KnowledgeReference[]
  reasoning?: ReasoningTrace | null
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

function formatRelativeTime(isoStr: string, t: TFunction): string {
  const now = Date.now()
  const then = new Date(isoStr).getTime()
  const diffMs = now - then
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return t('knowledgeSearch.relativeTime.justNow')
  if (diffMin < 60) return t('knowledgeSearch.relativeTime.minutesAgo', { count: diffMin })
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return t('knowledgeSearch.relativeTime.hoursAgo', { count: diffHr })
  const diffDay = Math.floor(diffHr / 24)
  if (diffDay === 1) return t('knowledgeSearch.relativeTime.yesterday')
  if (diffDay < 7) return t('knowledgeSearch.relativeTime.daysAgo', { count: diffDay })
  return isoStr.substring(0, 10)
}

function isSearchRunning(status?: KnowledgeSearchRunStatus): boolean {
  return status === 'searching'
}

function getSearchStatusLabel(status: KnowledgeSearchRunStatus, t: TFunction): string {
  const statusKey: Record<KnowledgeSearchRunStatus, string> = {
    searching: 'searching',
    done: 'done',
    error: 'error',
    stopped: 'stopped',
    empty: 'empty',
    idle: 'idle',
  }
  return t(`knowledgeSearch.searchStatus.${statusKey[status] ?? 'idle'}`)
}

function formatTimestamp(sec?: number | null): string {
  if (sec == null || Number.isNaN(sec)) return ''
  const s = Math.max(0, Math.floor(sec))
  const m = Math.floor(s / 60)
  const r = s % 60
  return `${String(m).padStart(2, '0')}:${String(r).padStart(2, '0')}`
}

const MEDIA_LABEL_KEY: Record<string, string> = {
  text: 'text', pdf: 'pdf', audio: 'audio', video: 'video', image: 'image', other: 'other',
}

function reasoningStatusMeta(status: string, t: TFunction): { color: string; bg: string; label: string } {
  switch (status) {
    case 'done':
      return { color: '#10b981', bg: '#ecfdf5', label: t('knowledgeSearch.reasoningStatus.done') }
    case 'skipped':
      return { color: '#94a3b8', bg: '#f1f5f9', label: t('knowledgeSearch.reasoningStatus.skipped') }
    case 'failed':
      return { color: '#ef4444', bg: '#fef2f2', label: t('knowledgeSearch.reasoningStatus.failed') }
    case 'running':
      return { color: '#3b82f6', bg: '#eff6ff', label: t('knowledgeSearch.reasoningStatus.running') }
    default:
      return { color: '#64748b', bg: '#f1f5f9', label: status }
  }
}

const REASONING_STAGE_KEYS: Record<string, string> = {
  ontology_match: 'ontology_match',
  route_decision: 'route_decision',
  fact_lookup: 'fact_lookup',
  llm_answer: 'llm_answer',
  rag_fallback: 'rag_fallback',
  fusion: 'fusion',
  retrieval_rerank: 'retrieval_rerank',
  rerank: 'rerank',
}

function getReasoningStepContent(step: ReasoningStep, t: TFunction): { title: string; summary?: string } {
  const stageKey = REASONING_STAGE_KEYS[step.stage]
  if (!stageKey) return { title: step.title, summary: step.summary ?? undefined }
  return {
    title: t(`knowledgeSearch.reasoningStages.${stageKey}.title`),
    summary: t(`knowledgeSearch.reasoningStages.${stageKey}.summary`),
  }
}


function fmtScore(v: unknown): string {
  const n = typeof v === 'number' ? v : Number(v)
  return Number.isFinite(n) ? n.toFixed(2) : String(v ?? '')
}


function ReasoningChip({
  children,
  tone = 'default',
}: {
  children: React.ReactNode
  tone?: 'default' | 'primary' | 'success' | 'danger'
}) {
  const tones = {
    default: { bg: '#f1f5f9', color: '#64748b' },
    primary: { bg: '#f5f3ff', color: '#7c3aed' },
    success: { bg: '#ecfdf5', color: '#10b981' },
    danger: { bg: '#fef2f2', color: '#ef4444' },
  } as const
  const t = tones[tone]
  return (
    <span
      style={{
        fontSize: 11,
        background: t.bg,
        color: t.color,
        borderRadius: 4,
        padding: '1px 7px',
        whiteSpace: 'nowrap',
      }}
    >
      {children}
    </span>
  )
}


function renderStepDetail(step: ReasoningStep, t: TFunction): React.ReactNode {
  if (!step.detail) return null
  const d = step.detail as Record<string, any>

  const wrap = (children: React.ReactNode) => (
    <div
      style={{
        marginTop: 8,
        background: '#fff',
        border: '1px solid #efeafc',
        borderRadius: 8,
        padding: '8px 10px',
      }}
    >
      {children}
    </div>
  )

  switch (step.stage) {
    case 'ontology_match': {
      const hits: any[] = Array.isArray(d.hits) ? d.hits : []
      if (hits.length === 0) return null
      return wrap(
        <>
          <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 6 }}>
            {t('knowledgeSearch.reasoningDetails.entityHits', {
              displayed: hits.length,
              total: d.total_hits ?? hits.length,
              knowledgeBases: d.kb_count ?? '—',
            })}
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {hits.map((h, idx) => (
              <span
                key={idx}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  fontSize: 12,
                  background: '#f7f5fe',
                  border: '1px solid #ece9fb',
                  borderRadius: 6,
                  padding: '2px 8px',
                }}
              >
                <span style={{ fontWeight: 600, color: '#4c1d95' }}>{h.name}</span>
                <span style={{ fontSize: 11, color: '#a78bda' }}>
                  {t('knowledgeSearch.reasoningDetails.score', { score: fmtScore(h.score) })}
                </span>
                {h.kb_id && <span style={{ fontSize: 10, color: '#b6bdc7' }}>{h.kb_id}</span>}
              </span>
            ))}
          </div>
        </>,
      )
    }
    case 'route_decision': {
      const route = d.route
      const routeLabel =
        route === 'ontology'
          ? t('knowledgeSearch.reasoningDetails.ontologyRoute')
          : route === 'rag'
            ? t('knowledgeSearch.reasoningDetails.ragRoute')
            : String(route ?? '—')
      return wrap(
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
          <ReasoningChip tone="primary">
            {t('knowledgeSearch.reasoningDetails.route', { route: routeLabel })}
          </ReasoningChip>
          {d.ft_score != null && (
            <ReasoningChip>
              {t('knowledgeSearch.reasoningDetails.fullTextScore', {
                score: fmtScore(d.ft_score),
                threshold: fmtScore(d.ftscore_threshold),
              })}
            </ReasoningChip>
          )}
          {d.vscore != null && (
            <ReasoningChip>
              {t('knowledgeSearch.reasoningDetails.vectorScore', {
                score: fmtScore(d.vscore),
                threshold: fmtScore(d.vscore_threshold),
              })}
            </ReasoningChip>
          )}
        </div>,
      )
    }
    case 'fact_lookup': {
      return wrap(
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
          {d.entity && (
            <ReasoningChip tone="primary">
              {t('knowledgeSearch.reasoningDetails.entity', { entity: d.entity })}
            </ReasoningChip>
          )}
          {d.fact_count != null && (
            <ReasoningChip tone="success">
              {t('knowledgeSearch.reasoningDetails.factsRetrieved', { count: d.fact_count })}
            </ReasoningChip>
          )}
          {d.kb_id && <ReasoningChip>{d.kb_id}</ReasoningChip>}
        </div>,
      )
    }
    case 'rag_fallback': {
      const ok: string[] = Array.isArray(d.kb_ok) ? d.kb_ok : []
      const failed: string[] = Array.isArray(d.kb_failed) ? d.kb_failed : []
      if (ok.length === 0 && failed.length === 0) return null
      return wrap(
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {ok.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
              <span style={{ fontSize: 11, color: '#94a3b8' }}>
                {t('knowledgeSearch.reasoningDetails.matchedKnowledgeBases')}
              </span>
              {ok.map((k) => (
                <ReasoningChip key={k} tone="success">
                  {k}
                </ReasoningChip>
              ))}
            </div>
          )}
          {failed.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
              <span style={{ fontSize: 11, color: '#94a3b8' }}>
                {t('knowledgeSearch.reasoningDetails.failedKnowledgeBases')}
              </span>
              {failed.map((k) => (
                <ReasoningChip key={k} tone="danger">
                  {k}
                </ReasoningChip>
              ))}
            </div>
          )}
        </div>,
      )
    }
    default:
      return null
  }
}



function FeedbackButtons({
  activeVote,
  loading,
  onVote,
}: {
  activeVote: SearchFeedbackType | null
  loading: SearchFeedbackType | null
  onVote: (type: SearchFeedbackType) => void
}) {
  const { t } = useTranslation('business')
  const isLikeLoading = loading === 'like'
  const isDislikeLoading = loading === 'dislike'
  const isLikeSelected = activeVote === 'like'
  const isDislikeSelected = activeVote === 'dislike'

  return (
    <div
      style={{
        marginTop: 14,
        paddingTop: 12,
        borderTop: '1px solid #e8edf5',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        fontSize: 13,
        color: '#94a3b8',
      }}
    >
      <span style={{ color: '#94a3b8' }}>{t('knowledgeSearch.feedback.question')}</span>

      { }
      <button
        type="button"
        disabled={!!loading}
        onClick={() => onVote('like')}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 5,
          border: 'none',
          fontSize: 13,
          borderRadius: 16,
          padding: '3px 14px',
          cursor: loading ? 'default' : 'pointer',
          lineHeight: '22px',
          fontWeight: isLikeSelected ? 600 : 400,
          color: isLikeSelected ? '#fff' : '#94a3b8',
          background: isLikeLoading ? '#bbf7d0' : isLikeSelected ? '#22c55e' : '#f1f5f9',
          boxShadow: isLikeSelected ? '0 1px 4px rgba(34,197,94,0.35)' : 'none',
          transition: 'all 0.25s ease',
          opacity: loading && !isLikeLoading ? 0.5 : 1,
        }}
        onMouseEnter={(e) => {
          if (!loading && !isLikeSelected) {
            e.currentTarget.style.background = '#dcfce7'
            e.currentTarget.style.color = '#16a34a'
          }
        }}
        onMouseLeave={(e) => {
          if (!loading && !isLikeSelected) {
            e.currentTarget.style.background = '#f1f5f9'
            e.currentTarget.style.color = '#94a3b8'
          }
        }}
      >
        {isLikeLoading ? (
          <LoadingOutlined style={{ fontSize: 14, color: '#16a34a' }} />
        ) : isLikeSelected ? (
          <LikeFilled style={{ fontSize: 14 }} />
        ) : (
          <LikeOutlined style={{ fontSize: 14 }} />
        )}
        {isLikeLoading ? t('knowledgeSearch.feedback.submitting') : t('knowledgeSearch.feedback.helpful')}
      </button>

      { }
      <button
        type="button"
        disabled={!!loading}
        onClick={() => onVote('dislike')}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 5,
          border: 'none',
          fontSize: 13,
          borderRadius: 16,
          padding: '3px 14px',
          cursor: loading ? 'default' : 'pointer',
          lineHeight: '22px',
          fontWeight: isDislikeSelected ? 600 : 400,
          color: isDislikeSelected ? '#fff' : '#94a3b8',
          background: isDislikeLoading ? '#fecaca' : isDislikeSelected ? '#ef4444' : '#f1f5f9',
          boxShadow: isDislikeSelected ? '0 1px 4px rgba(239,68,68,0.35)' : 'none',
          transition: 'all 0.25s ease',
          opacity: loading && !isDislikeLoading ? 0.5 : 1,
        }}
        onMouseEnter={(e) => {
          if (!loading && !isDislikeSelected) {
            e.currentTarget.style.background = '#ffe4e6'
            e.currentTarget.style.color = '#e11d48'
          }
        }}
        onMouseLeave={(e) => {
          if (!loading && !isDislikeSelected) {
            e.currentTarget.style.background = '#f1f5f9'
            e.currentTarget.style.color = '#94a3b8'
          }
        }}
      >
        {isDislikeLoading ? (
          <LoadingOutlined style={{ fontSize: 14, color: '#e11d48' }} />
        ) : isDislikeSelected ? (
          <DislikeFilled style={{ fontSize: 14 }} />
        ) : (
          <DislikeOutlined style={{ fontSize: 14 }} />
        )}
        {isDislikeLoading ? t('knowledgeSearch.feedback.submitting') : t('knowledgeSearch.feedback.unhelpful')}
      </button>
    </div>
  )
}

export default observer(function KnowledgeSearch() {
  const { t } = useTranslation('business')
  const { global } = useStore()
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

  const voteCacheRef = useRef<Record<string, SearchFeedbackType>>({})

  const [sessionVote, setSessionVote] = useState<SearchFeedbackType | null>(null)

  const [feedbackLoading, setFeedbackLoading] = useState<SearchFeedbackType | null>(null)

  const abortRef = useRef<AbortController | null>(null)
  const reasoningRef = useRef<Record<string, unknown> | null>(null)
  const isSearching = isSearchRunning(activeSearch?.status)


  const visibleDomains = useMemo(
    () => domains.filter((d) => d.id === 'all' || d.space_id === global.currentSpaceId),
    [domains, global.currentSpaceId],
  )


  useEffect(() => {
    setSelectedDomain((prev) =>
      prev === 'all' || visibleDomains.some((d) => d.id === prev) ? prev : 'all',
    )
  }, [visibleDomains])


  const { openDocument, viewer } = useDocumentViewer()

  const [reasoningExpandedMap, setReasoningExpandedMap] = useState<Record<string, boolean>>({})

  const [refsExpandedMap, setRefsExpandedMap] = useState<Record<string, boolean>>({})


  const openReference = useCallback(
    (ref: KnowledgeReference, loc?: KnowledgeReferenceLocation) => {
      openDocument({
        docId: ref.doc_id,
        fileName: ref.file_name,
        mediaType: ref.media_type,
        timeStart: loc?.time_start ?? null,
        timeEnd: loc?.time_end ?? null,
      })
    },
    [openDocument],
  )


  useEffect(() => {
    let mounted = true

    async function loadInitialData() {
      setPageLoading(true)
      try {
        const results = await Promise.allSettled([
          getKnowledgeSearchOverview(),
          getKnowledgeSearchDomains(),
          getKnowledgeSearchHistory(''),
        ] as const)

        if (!mounted) return

        const failedLabels: string[] = []
        const [overviewResult, domainResult, historyResult] = results

        if (overviewResult.status === 'fulfilled') {
          setOverview(overviewResult.value)
        } else {
          failedLabels.push(t('knowledgeSearch.loadSections.overview'))
          setOverview(EMPTY_OVERVIEW)
        }

        if (domainResult.status === 'fulfilled') {
          setDomains(domainResult.value)
        } else {
          failedLabels.push(t('knowledgeSearch.loadSections.domains'))
          setDomains([])
        }

        if (historyResult.status === 'fulfilled') {
          setHistory(historyResult.value)
        } else {
          failedLabels.push(t('knowledgeSearch.loadSections.history'))
          setHistory([])
        }

        setPageError('')
        if (failedLabels.length) {
          message.warning(t('knowledgeSearch.partialLoadFailed', { labels: failedLabels.join(t('knowledgeSearch.listSeparator')) }))
        }
        setPageLoading(false)
      } catch (error) {
        if (!mounted) return
        setPageError(error instanceof Error ? error.message : t('knowledgeSearch.dataLoadFailed'))
        setPageLoading(false)
      }
    }

    loadInitialData()

    return () => {
      mounted = false
      abortRef.current?.abort()
    }
  }, [t])

  const getDomainName = useCallback(
    (domainId?: string) => {
      const name = domains.find((d) => d.id === domainId)?.name
      return name ? t(name) : t('knowledgeSearch.allDomain')
    },
    [domains, t],
  )

  const getSelectedKbIds = useCallback(
    (domainId?: string): string[] => {
      if (!domainId || domainId === 'all') {

        const allIds = new Set<string>()
        visibleDomains.forEach((d) => d.kb_ids?.forEach((kid) => allIds.add(kid)))
        return Array.from(allIds)
      }
      const domain = visibleDomains.find((d) => d.id === domainId)
      return domain?.kb_ids ?? []
    },
    [visibleDomains],
  )


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
    const kbIds = getSelectedKbIds(domainId)
    if (kbIds.length === 0) {
      message.warning(t('knowledgeSearch.noSearchableKb'))
      return
    }
    const searchParams = { query: trimmedQuery, mode: 'mix' as const, topK: 5, domainId, kbIds }
    let streamError: Error | null = null
    let accumulatedAnswer = ''
    let finalReferences: KnowledgeReference[] = []
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
          onDelta: (delta, meta?: any) => {
            accumulatedAnswer += delta
            setThinkExpandedMap((prev) => {
              if (!delta.includes('<think>')) return prev
              return { ...prev, [sessionId]: true }
            })
            setActiveSearch((prev) =>
              prev?.id === sessionId ? { ...prev, rawAnswer: prev.rawAnswer + delta, source: meta?.source || prev.source } : prev,
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
          onDone: (meta) => {
            reasoningRef.current = (meta?.reasoning as any) ?? null


            const noAnswerPatterns = [
              /sorry/i, /unable to answer/i, /no answer/i,
              /cannot provide/i, /no relevant/i, /\[no-context\]/i,
              /无法回答/i, /无法提供/i, /未找到相关/i,
            ]
            const isNoAnswer = noAnswerPatterns.some((p) => p.test(accumulatedAnswer))
            const filteredRefs = isNoAnswer ? [] : (meta?.references ?? [])

            finalReferences = filteredRefs
            setActiveSearch((prev) =>
              prev?.id === sessionId
                ? { ...prev, references: filteredRefs, reasoning: meta?.reasoning ?? null, source: meta?.source || prev.source }
                : prev,
            )

            const cached = voteCacheRef.current[trimmedQuery]
            if (cached) {
              setSessionVote(cached)
            } else {
              setSessionVote(null)
            }
          },
        },
        controller.signal,
      )

      if (streamError) throw streamError
      if (controller.signal.aborted) return

      const domainName = getDomainName(domainId)
      const preview = buildAnswerPreview(accumulatedAnswer)
      const refCount = finalReferences.length

      setActiveSearch((prev) =>
        prev?.id === sessionId
          ? { ...prev, status: 'done' as const }
          : prev,
      )
      setThinkExpandedMap((prev) => ({ ...prev, [sessionId]: false }))

      saveKnowledgeSearchHistory('', {
        query: trimmedQuery,
        domainId,
        domain: domainName,
        answerPreview: preview,
        referenceCount: refCount,
        resultCount: refCount,
        status: 'done',
        durationMs: Date.now() - startTime,
      })
        .then((item) => {
          setHistory((prev) => [item, ...prev])
          setActiveHistoryIndex(0)
        })
        .catch(() => {

        })
    } catch (error) {
      if (controller.signal.aborted) return
      const msg = error instanceof Error ? error.message : t('knowledgeSearch.searchFailed')
      setActiveSearch((prev) =>
        prev?.id === sessionId
          ? { ...prev, status: 'error' as const, errorMessage: msg }
          : prev,
      )
      setThinkExpandedMap((prev) => ({ ...prev, [sessionId]: false }))
    } finally {
      if (abortRef.current === controller) abortRef.current = null
    }
  }, [query, selectedDomain, getSelectedKbIds, getDomainName, t])

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
    message.info(t('knowledgeSearch.stopSearch'))
  }, [t])

  const handleClearSearch = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setActiveSearch(null)
    setActiveHistoryIndex(null)
  }, [])


  const handleVoteAnswer = useCallback(
    async (feedbackType: SearchFeedbackType) => {
      if (!activeSearch || feedbackLoading) return
      const sessionId = activeSearch.id


      const kbIds: string[] = []
      if (activeSearch.references) {
        const seen = new Set<string>()
        activeSearch.references.forEach((ref) => {
          if (ref.kb_id && !seen.has(ref.kb_id)) {
            seen.add(ref.kb_id)
            kbIds.push(ref.kb_id)
          }
        })
      }
      if (kbIds.length === 0) {
        message.warning(t('knowledgeSearch.noRefForFeedback'))
        return
      }

      setFeedbackLoading(feedbackType)

      try {

        if (sessionVote === feedbackType) {
          await cancelSearchFeedback({ sessionId, feedbackType, kbIds })
          setSessionVote(null)
          if (activeSearch) delete voteCacheRef.current[activeSearch.query]
        }

        else {
          const answerText = parseThink(activeSearch.rawAnswer).answer
          const { body: cleanBody } = parseReferences(answerText)
          const preview = cleanBody.replace(/\s+/g, ' ').trim().slice(0, 100)


          if (sessionVote) {
            await cancelSearchFeedback({ sessionId, feedbackType: sessionVote, kbIds }).catch(() => {})
          }

          await submitSearchFeedback({
            sessionId,
            query: activeSearch.query,
            answerPreview: preview,
            feedbackType,
            kbIds,
            searchedAt: new Date().toISOString(),
          })

          setSessionVote(feedbackType)
          if (activeSearch) voteCacheRef.current[activeSearch.query] = feedbackType
        }
      } catch {
        message.error(t('knowledgeSearch.operationRetry'))
      } finally {
        setFeedbackLoading(null)
      }
    },
    [activeSearch, sessionVote, feedbackLoading, t],
  )

  const handleDomainChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedDomain(e.target.value)
  }, [])

  const handleDeleteHistory = useCallback(
    (id: string, index: number) => {
      deleteKnowledgeSearchHistory('', id)
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
      title: t('common.prompt'),
      content: t('knowledgeSearch.clearHistory.content'),
      okText: t('knowledgeSearch.clearHistory.confirm'),
      cancelText: t('knowledgeSearch.clearHistory.cancel'),
      okButtonProps: { danger: true },
      onOk: () => {
        clearKnowledgeSearchHistory('')
          .then(() => {
            setHistory([])
            setActiveHistoryIndex(null)
          })
          .catch(() => {})
      },
    })
  }, [t])



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
              <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 2 }}>{t(cfg.labelKey)}</div>
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
            {!visibleDomains.some((d) => d.id === 'all') && (
              <option value="all">{t('knowledgeSearch.allDomain')}</option>
            )}
            {visibleDomains.map((d) => (
              <option key={d.id} value={d.id}>
                {t(d.name)}
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
            placeholder={t('knowledgeSearch.search.placeholder')}
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
          {t('knowledgeSearch.search.action')}
        </Button>
        {isSearching && (
          <Button
            icon={<StopOutlined />}
            onClick={handleStopSearch}
            style={{ height: 48, padding: '0 18px', fontSize: 15, borderRadius: 10, flexShrink: 0 }}
          >
            {t('knowledgeSearch.search.stop')}
          </Button>
        )}
      </div>
    </Card>
  )

  const renderSessionCard = (session: SearchSession) => {
    const parsedAnswer = parseThink(session.rawAnswer)
    const { body: responseBody } = parseReferences(parsedAnswer.answer)
    const running = isSearchRunning(session.status)
    const hasThink = parsedAnswer.think.length > 0
    const hasAnswerContent = responseBody.length > 0
    const hasContent = hasThink || hasAnswerContent
    const thinkExpanded = parsedAnswer.thinking || thinkExpandedMap[session.id] === true
    const domainName = getDomainName(session.domainId)
    const statusLabel = getSearchStatusLabel(session.status, t)

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
                {t('knowledgeSearch.search.searching')}
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
            {session.source && (
              <span
                style={{
                  fontSize: 11,
                  color: '#8b5cf6',
                  fontWeight: 400,
                  background: '#f5f3ff',
                  borderRadius: 999,
                  padding: '2px 10px',
                  flexShrink: 0,
                  marginLeft: 'auto',
                }}
              >
                {t('knowledgeSearch.session.source', { source: session.source })}
              </span>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
            {running ? (
              <Button size="small" icon={<StopOutlined />} onClick={handleStopSearch}>
                {t('knowledgeSearch.session.stopGenerating')}
              </Button>
            ) : (
              <Button
                size="small"
                icon={<ReloadOutlined />}
                onClick={() => void handleSearch(session.query, { domainId: session.domainId })}
              >
                {t('knowledgeSearch.session.searchAgain')}
              </Button>
            )}
            <Button size="small" icon={<CloseCircleOutlined />} onClick={handleClearSearch}>
              {t('knowledgeSearch.session.clear')}
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
            {session.errorMessage || t('knowledgeSearch.searchFailed')}
          </div>
        )}

        { }
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
              <span style={{ fontSize: 13, fontWeight: 600, color: '#475569' }}>{t('knowledgeSearch.thinking.title')}</span>
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
                  {t('knowledgeSearch.thinking.generating')}
                </span>
              ) : (
                <span style={{ fontSize: 12, color: '#94a3b8' }}>
                  {thinkExpanded ? t('knowledgeSearch.thinking.collapseHint') : t('knowledgeSearch.thinking.collapsed')}
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
                {parsedAnswer.think.split('\n').find(Boolean) || t('knowledgeSearch.thinking.completed')}
              </div>
            )}
          </div>
        )}

        { }
        {(session.reasoning?.steps?.length ?? 0) > 0 && (
          <div
            style={{
              background: '#fbfaff',
              border: '1px solid #ece9fb',
              borderRadius: 10,
              padding: '12px 16px',
              marginBottom: 16,
            }}
          >
            <button
              type="button"
              onClick={() =>
                setReasoningExpandedMap((prev) => ({ ...prev, [session.id]: !prev[session.id] }))
              }
              style={{
                width: '100%', border: 'none', background: 'transparent', padding: 0,
                display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', textAlign: 'left',
              }}
            >
              {reasoningExpandedMap[session.id] ? <CaretDownOutlined /> : <CaretRightOutlined />}
              <NodeIndexOutlined style={{ color: '#8b5cf6' }} />
              <span style={{ fontSize: 13, fontWeight: 600, color: '#6d28d9' }}>{t('knowledgeSearch.reasoning.title')}</span>
              <span style={{ fontSize: 12, color: '#a78bda' }}>
                {t('knowledgeSearch.reasoning.summary', {
                  steps: session.reasoning!.steps.length,
                  source: session.reasoning!.final_source,
                })}
                {session.reasoning!.total_ms != null
                  ? t('knowledgeSearch.reasoning.duration', { duration: session.reasoning!.total_ms })
                  : ''}
              </span>
            </button>
            {reasoningExpandedMap[session.id] && (
              <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
                {session.reasoning!.steps.map((step, i) => {
                  const meta = reasoningStatusMeta(step.status, t)
                  const content = getReasoningStepContent(step, t)
                  return (
                    <div key={`${step.stage}-${i}`} style={{ display: 'flex', gap: 10 }}>
                      <div
                        style={{
                          width: 22, height: 22, borderRadius: '50%', flexShrink: 0,
                          background: meta.bg, color: meta.color, fontSize: 11, fontWeight: 700,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                        }}
                      >
                        {i + 1}
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                          <span style={{ fontSize: 13, fontWeight: 600, color: '#334155' }}>
                            {content.title}
                          </span>
                          <span
                            style={{
                              fontSize: 11, color: meta.color, background: meta.bg,
                              borderRadius: 4, padding: '0 6px',
                            }}
                          >
                            {meta.label}
                          </span>
                          {step.duration_ms != null && (
                            <span style={{ fontSize: 11, color: '#a3adbb' }}>
                              {t('knowledgeSearch.reasoning.stepDuration', { duration: step.duration_ms })}
                            </span>
                          )}
                        </div>
                        {content.summary && (
                          <div style={{ fontSize: 12, color: '#64748b', marginTop: 2, lineHeight: 1.6 }}>
                            {content.summary}
                          </div>
                        )}
                        {renderStepDetail(step, t)}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        { }
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
              {t('knowledgeSearch.answer.title')}
              <span style={{ fontWeight: 400, fontSize: 12, color: '#94a3b8' }}>
                {t('knowledgeSearch.answer.subtitle', { domain: domainName })}
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
                {responseBody || (running ? t('knowledgeSearch.answer.analyzing') : '')}
              </ReactMarkdown>
            </div>
            {running && hasContent && (
              <div style={{ marginTop: 8 }}>
                <Spin size="small" />
              </div>
            )}

            { }
            {session.status === 'done' && (
              <FeedbackButtons
                activeVote={sessionVote}
                loading={feedbackLoading}
                onVote={handleVoteAnswer}
              />
            )}
          </div>
        )}

        { }
        {(session.references?.length ?? 0) > 0 && (
          <div
            style={{
              background: '#f8fafc',
              borderLeft: '3px solid #3b82f6',
              borderRadius: '0 8px 8px 0',
              padding: '14px 18px',
              marginBottom: 16,
            }}
          >
            <button
              type="button"
              onClick={() =>
                setRefsExpandedMap((prev) => ({ ...prev, [session.id]: !prev[session.id] }))
              }
              style={{
                width: '100%', border: 'none', background: 'transparent', padding: 0,
                display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', textAlign: 'left',
                fontSize: 12, color: '#3b82f6', fontWeight: 600,
              }}
            >
              {refsExpandedMap[session.id] ? <CaretDownOutlined /> : <CaretRightOutlined />}
              <FileTextOutlined />
              {t('knowledgeSearch.references.title', { count: session.references!.length })}
            </button>
            {refsExpandedMap[session.id] && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 12 }}>
              {session.references!.map((ref, i) => {
                const locs = ref.locations || []
                const tsLoc = locs.find((l) => l.type === 'timestamp' && l.time_start != null)
                const snippet = locs.find((l) => l.text)?.text || ''
                return (
                  <div
                    key={`${ref.doc_id}-${i}`}
                    style={{
                      background: '#fff',
                      border: '1px solid #e8edf5',
                      borderRadius: 8,
                      padding: '10px 12px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      <span
                        style={{
                          fontSize: 11, color: '#64748b', background: '#f1f5f9',
                          borderRadius: 4, padding: '1px 7px', flexShrink: 0,
                        }}
                      >
                        {t(`knowledgeSearch.mediaTypes.${MEDIA_LABEL_KEY[ref.media_type] || 'other'}`)}
                      </span>
                      <span
                        style={{
                          fontSize: 13, fontWeight: 600, color: '#0b2b5c',
                          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                          maxWidth: 360,
                        }}
                        title={ref.file_name}
                      >
                        {ref.file_name}
                      </span>
                      {tsLoc && (
                        <span style={{ fontSize: 12, color: '#8b5cf6', flexShrink: 0 }}>
                          {formatTimestamp(tsLoc.time_start)}
                          {tsLoc.time_end != null ? ` - ${formatTimestamp(tsLoc.time_end)}` : ''}
                        </span>
                      )}
                      <a
                        className="yx-table-action"
                        style={{ marginLeft: 'auto', fontSize: 12, flexShrink: 0 }}
                        onClick={() => openReference(ref, tsLoc || locs[0])}
                      >
                        {ref.media_type === 'video'
                          ? (tsLoc
                              ? t('knowledgeSearch.references.locatePlayback')
                              : t('knowledgeSearch.references.viewVideo'))
                          : ref.media_type === 'audio'
                            ? t('knowledgeSearch.references.playAudio')
                            : ref.media_type === 'image'
                              ? t('knowledgeSearch.references.viewImage')
                              : t('knowledgeSearch.references.viewSource')}
                      </a>
                    </div>
                    {snippet && (
                      <div
                        style={{
                          marginTop: 8, fontSize: 13, color: '#475569', lineHeight: 1.7,
                          background: '#fafcff', borderRadius: 6, padding: '8px 10px',
                          maxHeight: 120, overflow: 'auto', whiteSpace: 'pre-wrap',
                        }}
                      >
                        {snippet}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
            )}
          </div>
        )}

        { }
        {running && !hasContent && (
          <div style={{ textAlign: 'center', padding: '30px 0' }}>
            <Spin size="default" />
            <div style={{ marginTop: 10, color: '#94a3b8', fontSize: 13 }}>{t('knowledgeSearch.search.searchingKnowledge')}</div>
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
        {t('knowledgeSearch.history.title')}
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
            {t('knowledgeSearch.history.clear')}
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
          {t('knowledgeSearch.history.empty')}
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
                <span>{t('knowledgeSearch.history.resultCount', { count: h.resultCount })}</span>
                <span>{formatRelativeTime(h.searchedAt, t)}</span>
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
              title={t('knowledgeSearch.history.deleteItem')}
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
          <Button onClick={() => window.location.reload()}>{t('knowledgeSearch.empty.refresh')}</Button>
        </div>
      )
    }

    if (!activeSearch) {
      return (
        <Card style={{ borderRadius: 12 }} styles={{ body: { padding: '60px 20px' } }}>
          <Empty description={t('knowledgeSearch.empty.description')} />
        </Card>
      )
    }

    return renderSessionCard(activeSearch)
  }


  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('knowledgeSearch.title')}</h1>
        <p className="yx-page-subtitle">
          {t('knowledgeSearch.space.summary', {
            space: global.currentSpace?.name || t('knowledgeSearch.space.notSelected'),
          })}
        </p>
      </div>
      { }
      { }
      {renderSearchPanel()}

      <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          {renderMainContent()}
        </div>
        {renderHistorySidebar()}
      </div>

      <div style={{ textAlign: 'center', padding: '32px 0 8px', fontSize: 13, color: '#cbd5e1' }}>
        {t('knowledgeSearch.footer', { year: 2026 })}
      </div>

      { }
      {viewer}
    </div>
  )
})
