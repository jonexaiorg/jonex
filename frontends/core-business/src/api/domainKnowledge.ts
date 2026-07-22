import type {
  DomainKnowledgeSpace,
  DomainKnowledgeListParams,
  PaginationResult,
  DomainKnowledgeItem,
  DomainKnowledgePermissionMember,
  DomainKnowledgePermissionPayload,
  DomainKnowledgeDetail,
  DataSourceConfig,
  ParserFileConfig,
  OntologyTemplate,
  ValidationRule,
  PromptTemplate,
  CompileEntity,
  EntityListParams,
  EntityDistribution,
  RelationDistribution,
  LogicRule,
  ActionRule,
  DomainKnowledgeResultStats,
  GraphSummary,
  ManualDocItem,
  ManualDocListParams,
  BackendParseResultSummary,
  BackendEntityItem,
  BackendGraphSummary,
  BackendPaginatedResult,
} from '@/types/domainKnowledge'
import { request, getData } from './request'

export function getDomainKnowledgeSpaces(): Promise<DomainKnowledgeSpace[]> {
  return getData(request.get('/core-business/domain-knowledge/spaces'))
}

export function getDomainKnowledgeList(
  params: DomainKnowledgeListParams,
): Promise<PaginationResult<DomainKnowledgeItem>> {
  return getData(request.get('/core-business/domain-knowledge', { params }))
}

export function getDomainKnowledgePermissions(
  knowledgeBaseId: string,
  keyword?: string,
): Promise<{ knowledgeBaseId: string; members: DomainKnowledgePermissionMember[] }> {
  return getData(
    request.get(`/core-business/domain-knowledge/${knowledgeBaseId}/permissions`, {
      params: keyword ? { keyword } : undefined,
    }),
  )
}

export function saveDomainKnowledgePermissions(
  knowledgeBaseId: string,
  payload: DomainKnowledgePermissionPayload,
): Promise<boolean> {
  return getData(
    request.put(`/core-business/domain-knowledge/${knowledgeBaseId}/permissions`, payload),
  )
}

// ─── Detail APIs ────────────────────────────────────────

export function getDomainKnowledgeDetail(kbId: string): Promise<DomainKnowledgeDetail> {
  return getData(request.get(`/core-business/domain-knowledge/${kbId}/detail`))
}

export function getDomainKnowledgeDataSources(kbId: string): Promise<DataSourceConfig[]> {
  return getData(request.get(`/core-business/domain-knowledge/${kbId}/data-sources`))
}

export function getDomainKnowledgeParserConfigs(kbId: string): Promise<ParserFileConfig[]> {
  return getData(request.get(`/core-business/domain-knowledge/${kbId}/parser-configs`))
}

export function getDomainKnowledgeOntologyTemplates(kbId: string): Promise<OntologyTemplate[]> {
  return getData(request.get(`/core-business/domain-knowledge/${kbId}/ontology-templates`))
}

export function getDomainKnowledgeValidationRules(kbId: string): Promise<ValidationRule[]> {
  return getData(request.get(`/core-business/domain-knowledge/${kbId}/validation-rules`))
}

export function getDomainKnowledgePrompts(kbId: string): Promise<PromptTemplate[]> {
  return getData(request.get(`/core-business/domain-knowledge/${kbId}/prompts`))
}

export function getDomainKnowledgeEntities(
  params: EntityListParams,
): Promise<PaginationResult<CompileEntity>> {

  const query: Record<string, string | number> = {
    page: params.page,
    page_size: params.pageSize,
  }
  if (params.keyword) query.keyword = params.keyword
  if (params.entityType) query.entity_type = params.entityType

  return getData<BackendPaginatedResult<BackendEntityItem>>(
    request.get(`/knowledge-base/bases/${params.knowledgeBaseId}/parse-result/entities`, { params: query }),
  ).then((res) => ({
    list: res.items.map(mapEntityItem),
    pagination: { page: res.page, pageSize: res.page_size, total: res.total },
  }))
}

// entity/relation distribution now derived from graph-summary cache (see below)

export function getDomainKnowledgeLogicRules(kbId: string): Promise<LogicRule[]> {
  return getData(request.get(`/core-business/domain-knowledge/${kbId}/logic-rules`))
}

export function getDomainKnowledgeActionRules(kbId: string): Promise<ActionRule[]> {
  return getData(request.get(`/core-business/domain-knowledge/${kbId}/action-rules`))
}

export function getDomainKnowledgeResultStats(kbId: string): Promise<DomainKnowledgeResultStats> {
  return getData<BackendParseResultSummary>(
    request.get(`/knowledge-base/bases/${kbId}/parse-result/summary`),
  ).then(mapResultStats)
}

// ── graph summary (real endpoint, cached for distribution derivation) ──

let _graphSummaryCache: BackendGraphSummary | null = null

export async function getDomainKnowledgeGraphSummary(kbId: string): Promise<GraphSummary> {
  const backend = await getData<BackendGraphSummary>(
    request.get(`/knowledge-base/bases/${kbId}/parse-result/graph-summary`),
  )
  _graphSummaryCache = backend
  return mapGraphSummary(backend)
}

export function getDomainKnowledgeEntityDistribution(): Promise<EntityDistribution[]> {
  if (_graphSummaryCache) return Promise.resolve(deriveEntityDistribution(_graphSummaryCache))
  return Promise.resolve([])
}

export function getDomainKnowledgeRelationDistribution(): Promise<RelationDistribution[]> {
  if (_graphSummaryCache) return Promise.resolve(deriveRelationDistribution(_graphSummaryCache))
  return Promise.resolve([])
}

// ─── Manual Datasource APIs ─────────────────────────────

interface BackendDocItem {
  id: string
  file_name: string
  file_type?: string
  file_size?: number
  status: string
  created_at?: string
  updated_at?: string
  extra_metadata?: Record<string, unknown>
}

interface BackendDocListResponse {
  items: BackendDocItem[]
  total: number
  offset: number
  limit: number
}

function formatFileSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${bytes} B`
}

function mapBackendDoc(doc: BackendDocItem, knowledgeBaseId: string): ManualDocItem {
  const meta = doc.extra_metadata || {}
  return {
    id: doc.id,
    name: doc.file_name,
    type: (doc.file_type || (doc.file_name.split('.').pop() || 'unknown')).toUpperCase(),
    size: typeof doc.file_size === 'number' ? formatFileSize(doc.file_size) : '-',
    uploader: (meta.uploader as string) || '-',
    uploadTime: doc.created_at
      ? new Date(doc.created_at).toISOString().replace('T', ' ').substring(0, 19)
      : '-',
    status: doc.status === 'ready' ? '入库·解析·编译' : doc.status === 'parsing' ? '入库·解析中' : doc.status === 'pending' ? '入库' : doc.status,
    knowledgeBaseId,
  }
}

export async function getManualDocList(
  params: ManualDocListParams,
): Promise<PaginationResult<ManualDocItem>> {

  const backendParams: Record<string, string | number> = {
    page: params.page,
    page_size: params.pageSize,
  }
  if (params.status) backendParams.status = params.status

  const backendResult = await getData<BackendDocListResponse>(
    request.get('/knowledge-base/documents', { params: backendParams }),
  )

  // client-side keyword filter (backend doesn't support keyword yet)
  let filtered = backendResult.items
  if (params.keyword) {
    const kw = params.keyword.toLowerCase()
    filtered = filtered.filter((d) => d.file_name.toLowerCase().includes(kw))
  }

  const list = filtered.map((d) => mapBackendDoc(d, params.knowledgeBaseId))
  return {
    list,
    pagination: { page: params.page, pageSize: params.pageSize, total: list.length },
  }
}

export async function uploadManualDocument(
  knowledgeBaseId: string,
  file: File,
): Promise<ManualDocItem> {

  const formData = new FormData()
  formData.append('file', file)
  formData.append('knowledge_base_id', knowledgeBaseId)

  const result = await getData<BackendDocItem>(
    request.post('/knowledge-base/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  )

  return mapBackendDoc(result, knowledgeBaseId)
}

// ── Parse Result Mappers ─────────────────────────────────

const DIST_COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
  '#8b5cf6', '#ec4899', '#06b6d4', '#f97316',
]

function mapResultStats(b: BackendParseResultSummary): DomainKnowledgeResultStats {
  return {
    entityCount: b.entities_count,
    relationCount: b.relationships_count,
    compileVersionCount: b.compile_versions_count,
    sourceFileCount: b.documents_count,
  }
}

function mapEntityItem(b: BackendEntityItem): CompileEntity {
  return {
    id: b.id,
    name: b.name,
    type: b.type,
    attrs: 0,
    relations: b.relations_count,
    createdAt: b.created_at
      ? new Date(b.created_at * 1000).toISOString().replace('T', ' ').substring(0, 19)
      : '-',
    knowledgeBaseId: '',
  }
}

function mapGraphSummary(b: BackendGraphSummary): GraphSummary {
  return {
    entityTypeCount: b.entity_type_count,
    relationTotalCount: b.edges_count,
    relationTypeCount: b.relation_type_count,
    avgDegree: b.avg_degree,
  }
}

function deriveEntityDistribution(b: BackendGraphSummary): EntityDistribution[] {
  return b.entity_type_distribution.map((d, i) => ({
    ...d,
    color: DIST_COLORS[i % DIST_COLORS.length],
  }))
}

function deriveRelationDistribution(b: BackendGraphSummary): RelationDistribution[] {
  return b.relation_distribution.map((d, i) => ({
    ...d,
    color: DIST_COLORS[i % DIST_COLORS.length],
  }))
}
