import { readAccessToken } from '@jonex/shell-sdk'
import { request, getData } from './request'
import i18next from '@/locales/i18n'
import {
  listMockKnowledgeSearchHistory,
  saveMockKnowledgeSearchHistory,
  deleteMockKnowledgeSearchHistory,
  clearMockKnowledgeSearchHistory,
} from '../mocks/knowledgeSearchHistoryStore'
import type {
  KnowledgeSearchDomain,
  KnowledgeSearchHistoryItem,
  KnowledgeSearchMode,
  KnowledgeSearchOverview,
  KnowledgeSearchStreamHandlers,
  KnowledgeSearchStreamMeta,
  KnowledgeSearchStreamParams,
  SaveKnowledgeSearchHistoryPayload,
  SearchFeedbackType,
  CancelSearchFeedbackParams,
  SubmitSearchFeedbackParams,
  SubmitSearchFeedbackResponse,
} from '../types/knowledgeSearch'

type NormalizedSearchParams = {
  query: string
  mode: KnowledgeSearchMode
  topK: number
  domainId: string
  kbIds: string[]
}

interface RawKnowledgeSearchHistoryItem {
  id: string
  query: string
  searched_at?: string
  searchedAt?: string
  result_count?: number
  resultCount?: number
  domain?: string
  domain_id?: string
  domainId?: string
  status?: KnowledgeSearchHistoryItem['status']
  answer_preview?: string
  answerPreview?: string
  reference_count?: number
  referenceCount?: number
  duration_ms?: number
  durationMs?: number
  mode?: string
  top_k?: number
  topK?: number
  metadata?: {
    domain?: string
    domain_id?: string
    domainId?: string
  }
}

function normalizeSearchParams(params: KnowledgeSearchStreamParams): NormalizedSearchParams {
  return {
    query: params.query,
    mode: params.mode ?? 'mix',
    topK: params.topK ?? 5,
    domainId: params.domainId ?? 'all',
    kbIds: params.kbIds ?? [],
  }
}

function normalizeHistoryItem(item: RawKnowledgeSearchHistoryItem): KnowledgeSearchHistoryItem {
  const metadata = item.metadata ?? {}
  return {
    id: item.id,
    query: item.query,
    searchedAt: item.searchedAt ?? item.searched_at ?? new Date().toISOString(),
    resultCount: item.resultCount ?? item.result_count ?? 0,
    domain: item.domain ?? metadata.domain,
    domainId: item.domainId ?? item.domain_id ?? metadata.domainId ?? metadata.domain_id,
    status: item.status,
    answerPreview: item.answerPreview ?? item.answer_preview,
    referenceCount: item.referenceCount ?? item.reference_count,
    durationMs: item.durationMs ?? item.duration_ms,
    mode: item.mode === 'hybrid' ? 'hybrid' : undefined,
    topK: item.topK ?? item.top_k,
  }
}

export async function getKnowledgeSearchOverview(): Promise<KnowledgeSearchOverview> {

  return getData<KnowledgeSearchOverview>(request.get('/knowledge-base/search/overview'))
}

export async function getKnowledgeSearchDomains(): Promise<KnowledgeSearchDomain[]> {
  const result = await getData<{ items: KnowledgeSearchDomain[] }>(
    request.get('/knowledge-base/services', { params: { limit: 100 } }),
  )
  const items = result.items ?? []
  return [{ id: 'all', name: 'knowledgeSearch.allDomain', description: 'knowledgeSearch.allDomainDesc' }, ...items]
}

export async function getKnowledgeSearchHistory(knowledgeBaseId: string): Promise<KnowledgeSearchHistoryItem[]> {

  const result = await getData<{ items: RawKnowledgeSearchHistoryItem[] }>(
    request.get('/knowledge-base/search/history', { params: { knowledge_base_id: knowledgeBaseId } }),
  )
  return (result.items ?? []).map(normalizeHistoryItem)
}

export async function saveKnowledgeSearchHistory(
  knowledgeBaseId: string,
  payload: SaveKnowledgeSearchHistoryPayload,
): Promise<KnowledgeSearchHistoryItem> {




  const result = await getData<RawKnowledgeSearchHistoryItem | { item: RawKnowledgeSearchHistoryItem }>(
    request.post('/knowledge-base/search/history', { ...payload, knowledge_base_id: knowledgeBaseId }),
  )
  return normalizeHistoryItem(('item' in result ? result.item : result) as RawKnowledgeSearchHistoryItem)
}

export async function deleteKnowledgeSearchHistory(knowledgeBaseId: string, id: string): Promise<void> {




  await getData(request.delete(`/knowledge-base/search/history/${id}`, { params: { knowledge_base_id: knowledgeBaseId } }))
}

export async function clearKnowledgeSearchHistory(knowledgeBaseId: string): Promise<void> {




  await getData(request.delete('/knowledge-base/search/history', { params: { knowledge_base_id: knowledgeBaseId } }))
}

export async function streamKnowledgeSearch(
  params: KnowledgeSearchStreamParams,
  handlers: KnowledgeSearchStreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const normalized = normalizeSearchParams(params)

  const token = readAccessToken()
  const baseUrl = (import.meta as any).env?.VITE_API_BASE_URL || '/api/v1'
  const url = new URL(`${baseUrl}/knowledge-base/search/ontology`, window.location.origin)

  const body: Record<string, unknown> = {
    query: normalized.query,
    mode: normalized.mode,
    top_k: normalized.topK,
    with_reasoning: true,
  }
  if (normalized.domainId && normalized.domainId !== 'all') {
    body.domain_id = normalized.domainId
  }
  if (normalized.kbIds.length > 0) {
    body.knowledge_base_ids = normalized.kbIds
  }

  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
    signal,
  })

  if (response.status === 401) {
    handlers.onError?.(new Error(i18next.t('knowledgeSearch.sessionExpired')))
    return
  }

  if (!response.ok) {
    throw new Error(`${i18next.t('knowledgeSearch.searchFailed')}: ${response.status}`)
  }

  try {
    const result = await response.json()

    if (!result.success || !result.data?.answer) {
      handlers.onDelta(i18next.t('knowledgeSearch.noResult'), { source: result.data?.source })
      handlers.onDone?.()
      return
    }


    const answer = result.data.answer
    const meta = {
      source: result.data.source,
      references: result.data.references ?? [],
      reasoning: result.data.reasoning ?? null,
      rag_used: result.data.rag_used,
    }
    for (let i = 0; i < answer.length; i += 2) {
      if (signal?.aborted) return
      handlers.onDelta(answer.slice(i, i + 2), meta)
      await new Promise<void>((resolve) => setTimeout(resolve, 25))
    }
    handlers.onDone?.(meta)
  } catch (error) {
    if (signal?.aborted) return
    handlers.onError?.(
      error instanceof Error ? error : new Error(i18next.t('knowledgeSearch.searchFailed')),
    )
  }
}


export async function submitSearchFeedback(
  params: SubmitSearchFeedbackParams,
): Promise<SubmitSearchFeedbackResponse> {
  const token = readAccessToken()
  const response = await fetch('/api/v1/knowledge-base/search/feedback', {
    method: 'POST',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: params.query,
      session_id: params.sessionId,
      answer_preview: params.answerPreview,
      feedback_type: params.feedbackType,
      knowledge_base_ids: params.kbIds,
      searched_at: params.searchedAt,
    }),
  })
  if (!response.ok) {
    throw new Error(i18next.t('knowledgeSearch.feedbackSubmitFailed'))
  }
  const result = await response.json()
  return result.data ?? { success: true, feedbackType: params.feedbackType, likeCount: 1, dislikeCount: 0 }
}


export async function cancelSearchFeedback(
  params: CancelSearchFeedbackParams,
): Promise<SubmitSearchFeedbackResponse> {
  const token = readAccessToken()
  const response = await fetch('/api/v1/knowledge-base/search/feedback', {
    method: 'DELETE',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: params.sessionId,
      feedback_type: params.feedbackType,
      knowledge_base_ids: params.kbIds,
    }),
  })
  if (!response.ok) {
    throw new Error(i18next.t('knowledgeSearch.feedbackCancelFailed'))
  }
  const result = await response.json()
  return result.data ?? { success: true, feedbackType: params.feedbackType, likeCount: 0, dislikeCount: 0 }
}




export async function getSearchFeedbackList(
  knowledgeBaseId: string,
  params?: { feedbackType?: SearchFeedbackType; page?: number; pageSize?: number },
): Promise<import('../types/knowledgeSearch').SearchFeedbackListResponse> {
  const token = readAccessToken()
  const searchParams = new URLSearchParams({ knowledge_base_id: knowledgeBaseId })
  if (params?.feedbackType) searchParams.set('feedback_type', params.feedbackType)
  if (params?.page) searchParams.set('page', String(params.page))
  if (params?.pageSize) searchParams.set('page_size', String(params.pageSize))

  const response = await fetch(`/api/v1/knowledge-base/search/feedback?${searchParams}`, {
    headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  })
  if (!response.ok) throw new Error(i18next.t('knowledgeSearch.feedbackListFailed'))
  const result = await response.json()
  return result.data ?? { items: [], total: 0, like_count: 0, dislike_count: 0, page: 1, page_size: 50 }
}


export async function toggleSearchFeedbackAdopted(feedbackId: string): Promise<void> {
  const token = readAccessToken()
  const response = await fetch('/api/v1/knowledge-base/search/feedback/toggle-adopt', {
    method: 'POST',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ feedback_id: feedbackId }),
  })
  if (!response.ok) throw new Error(i18next.t('knowledgeSearch.feedbackStatusFailed'))
}


export async function getSearchFeedbackStats(
  knowledgeBaseId: string,
): Promise<import('../types/knowledgeSearch').SearchFeedbackStats> {
  const token = readAccessToken()
  const response = await fetch(`/api/v1/knowledge-base/search/feedback/stats?knowledge_base_id=${knowledgeBaseId}`, {
    headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  })
  if (!response.ok) throw new Error(i18next.t('knowledgeSearch.feedbackStatsFailed'))
  const result = await response.json()
  return result.data ?? { total: 0, like_count: 0, dislike_count: 0 }
}
