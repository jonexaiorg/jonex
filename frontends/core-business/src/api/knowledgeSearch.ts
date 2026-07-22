import { readAccessToken } from '@jonex/shell-sdk'
import { request, getData } from './request'
import type {
  KnowledgeSearchDomain,
  KnowledgeSearchHistoryItem,
  KnowledgeSearchOverview,
  KnowledgeSearchStreamHandlers,
  KnowledgeSearchStreamParams,
  SaveKnowledgeSearchHistoryPayload,
} from '../types/knowledgeSearch'


type NormalizedSearchParams = Required<KnowledgeSearchStreamParams>

function normalizeSearchParams(params: KnowledgeSearchStreamParams): NormalizedSearchParams {
  return {
    query: params.query,
    mode: params.mode ?? 'mix',
    topK: params.topK ?? 5,
    domainId: params.domainId ?? 'all',
  }
}

export async function getKnowledgeSearchOverview(): Promise<KnowledgeSearchOverview> {
  return getData<KnowledgeSearchOverview>(request.get('/knowledge-base/search/overview'))
}

export async function getKnowledgeSearchDomains(): Promise<KnowledgeSearchDomain[]> {
  return getData<KnowledgeSearchDomain[]>(request.get('/knowledge-base/search/domains'))
}

export async function getKnowledgeSearchHistory(): Promise<KnowledgeSearchHistoryItem[]> {
  const result = await getData<{ items: KnowledgeSearchHistoryItem[] }>(
    request.get('/knowledge-base/search/history'),
  )
  return result.items
}

export async function saveKnowledgeSearchHistory(
  payload: SaveKnowledgeSearchHistoryPayload,
): Promise<KnowledgeSearchHistoryItem> {
  const result = await getData<{ item: KnowledgeSearchHistoryItem }>(
    request.post('/knowledge-base/search/history', payload),
  )
  return result.item
}

export async function deleteKnowledgeSearchHistory(id: string): Promise<void> {
  await getData(request.delete(`/knowledge-base/search/history/${id}`))
}

export async function clearKnowledgeSearchHistory(): Promise<void> {
  await getData(request.delete('/knowledge-base/search/history'))
}

export async function streamKnowledgeSearch(
  params: KnowledgeSearchStreamParams,
  handlers: KnowledgeSearchStreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const normalized = normalizeSearchParams(params)


  const token = readAccessToken()
  const baseUrl = (import.meta as any).env?.VITE_API_BASE_URL || '/api/v1'
  const url = new URL(`${baseUrl}/knowledge-base/documents/search/stream`, window.location.origin)

  url.searchParams.set('query', normalized.query)
  url.searchParams.set('mode', normalized.mode)
  url.searchParams.set('top_k', String(normalized.topK))
  if (normalized.domainId && normalized.domainId !== 'all') {
    url.searchParams.set('domain_id', normalized.domainId)
  }

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    signal,
  })

  if (response.status === 401) {
    handlers.onError?.(new Error('登录已失效，请重新登录'))
    return
  }

  if (!response.ok || !response.body) {
    throw new Error(`搜索失败：${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed.startsWith('data:')) continue

        const payload = trimmed.slice(5).trim()
        if (payload === '[DONE]') {
          handlers.onDone?.()
          return
        }

        try {
          const chunk = JSON.parse(payload)
          const delta = chunk.choices?.[0]?.delta?.content
          if (delta) handlers.onDelta(delta, chunk)
        } catch {
          // skip unparseable SSE lines, continue processing
        }
      }
    }
  } catch (error) {
    if (signal?.aborted) return
    handlers.onError?.(
      error instanceof Error ? error : new Error('知识检索连接中断，请重试'),
    )
    throw error
  }
}
