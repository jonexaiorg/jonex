export type KnowledgeSearchMode = 'local' | 'global' | 'hybrid' | 'naive' | 'mix' | 'bypass'

export interface KnowledgeSearchOverview {
  totalDocuments: number
  totalEntities: number
  totalRelations: number
  todaySearches: number
  avgResponseTimeMs: number
  totalDomains?: number
  sourceFiles?: number
  dataSources?: number
}

export interface KnowledgeSearchDomain {
  id: string
  name: string
  description?: string
  knowledgeCount?: number
}

export interface KnowledgeSearchHistoryItem {
  id: string
  query: string
  searchedAt: string
  resultCount: number
  domain?: string
  domainId?: string
  status?: 'done' | 'stopped' | 'error'
  answerPreview?: string
  referenceCount?: number
  durationMs?: number
  mode?: 'hybrid'
  topK?: number
}

export interface SaveKnowledgeSearchHistoryPayload {
  query: string
  resultCount: number
  domain?: string
  domainId?: string
  status: 'done'
  answerPreview?: string
  referenceCount?: number
  durationMs?: number
  mode?: 'hybrid'
  topK?: number
}

export interface KnowledgeSearchStreamParams {
  query: string
  mode?: KnowledgeSearchMode
  topK?: number
  domainId?: string
}

export interface KnowledgeSearchStreamHandlers {
  onDelta: (content: string, rawChunk?: unknown) => void
  onDone?: () => void
  onError?: (error: Error) => void
}

export type KnowledgeSearchViewStatus =
  | 'initial'
  | 'loading'
  | 'searching'
  | 'done'
  | 'empty'
  | 'error'

export type KnowledgeSearchRunStatus =
  | 'idle'
  | 'searching'
  | 'done'
  | 'empty'
  | 'stopped'
  | 'error'
