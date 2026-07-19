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
  domain_type?: string
  status?: string
  space_id?: string
  space_name?: string
  kb_ids?: string[]
  kb_names?: string[]
  created_at?: string
  updated_at?: string
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

  kbIds?: string[]
}


export interface KnowledgeReferenceLocation {
  type: 'chunk' | 'char' | 'page' | 'timestamp' | 'document'
  chunk_index?: number | null
  char_start?: number | null
  char_end?: number | null
  page_no?: number | null
  time_start?: number | null
  time_end?: number | null

  text?: string | null
}


export interface KnowledgeReference {
  doc_id: string
  kb_id?: string | null
  file_name: string
  mime_type?: string | null
  file_size?: number | null
  media_type: 'text' | 'pdf' | 'audio' | 'video' | 'image' | 'other'
  raw_url?: string | null
  locations: KnowledgeReferenceLocation[]
}


export interface ReasoningStep {
  stage: string
  title: string
  status: 'running' | 'done' | 'skipped' | 'failed'
  summary?: string | null
  detail?: Record<string, unknown> | null
  duration_ms?: number | null
}


export interface ReasoningTrace {
  steps: ReasoningStep[]
  final_source: string
  total_ms?: number | null
}

export interface KnowledgeSearchStreamMeta {
  source?: string
  references?: KnowledgeReference[]
  reasoning?: ReasoningTrace | null
  rag_used?: boolean
}

export interface KnowledgeSearchStreamHandlers {
  onDelta: (content: string, meta?: KnowledgeSearchStreamMeta) => void
  onDone?: (meta?: KnowledgeSearchStreamMeta) => void
  onError?: (error: Error) => void
}

export type KnowledgeSearchViewStatus =
  | 'initial'
  | 'loading'
  | 'searching'
  | 'done'
  | 'empty'
  | 'error'




export interface SearchFeedbackItem {
  id: string
  tenant_id: string
  user_id: string
  session_id: string
  query: string
  answer_preview: string | null
  knowledge_base_id: string
  knowledge_base_name: string | null
  feedback_type: SearchFeedbackType
  adopted: boolean
  searched_at: string | null
  created_at: string | null
  updated_at: string | null
}


export interface SearchFeedbackListResponse {
  items: SearchFeedbackItem[]
  total: number
  like_count: number
  dislike_count: number
  page: number
  page_size: number
}


export interface SearchFeedbackStats {
  total: number
  like_count: number
  dislike_count: number
}

export type KnowledgeSearchRunStatus =
  | 'idle'
  | 'searching'
  | 'done'
  | 'empty'
  | 'stopped'
  | 'error'


export type SearchFeedbackType = 'like' | 'dislike'


export interface SubmitSearchFeedbackParams {
  sessionId: string
  query: string
  answerPreview: string
  feedbackType: SearchFeedbackType

  kbIds: string[]

  searchedAt?: string
}


export interface SubmitSearchFeedbackResponse {
  success: boolean
  feedbackType: SearchFeedbackType
  likeCount: number
  dislikeCount: number
}


export interface CancelSearchFeedbackParams {
  sessionId: string
  feedbackType: SearchFeedbackType
  kbIds: string[]
}
