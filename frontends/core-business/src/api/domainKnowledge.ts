import type {
  DomainKnowledgeSpace,
  DomainKnowledgeListParams,
  DomainKnowledgeStatus,
  DomainKnowledgeSourceType,
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
  CompiledSchema,
  CompiledSchemaEntityType,
  CompiledSchemaRelationType,
  OntologyEditorState,
  OntologyObjectDef,
  OntologyRelationDef,
  CompileStep,
  EngineSetting,
  SaveOntologyObjectPayload,
  SaveOntologyRelationPayload,
  SaveCompileStepPayload,
  OntologyConstraint,
  SaveOntologyConstraintPayload,
  CompiledSchemaConstraint,
  OntologyInstanceSummary,
  RelationInstanceSummary,
  OntologyInstanceRow,
  OntologyInstanceListParams,
  RelationInstanceRow,
  RelationInstanceListParams,
  OntologyStatistics,
  OntologyGraphData,
  OntologyGraphParams,
  OntologyNeighborData,
} from '@/types/domainKnowledge'
import { normalizeConstraintType } from '@/types/domainKnowledge'
import { request, getData, postData, putData, deleteData } from './request'
import axios from 'axios'
import i18next from '@/locales/i18n'
import { readAccessToken } from '@jonex/shell-sdk'
import { listDataSources } from './dataSource'
import type { DataSourceInstance } from '@/types/dataSource'

export function getDomainKnowledgeSpaces(): Promise<DomainKnowledgeSpace[]> {
  return getData<{ items: DomainKnowledgeSpace[] }>(
    request.get('/knowledge-base/spaces', { params: { limit: 100 } }),
  ).then((res) => res.items)
}

export function getDomainKnowledgeList(
  params: DomainKnowledgeListParams,
): Promise<PaginationResult<DomainKnowledgeItem>> {
  const query: Record<string, string | number | undefined> = {
    keyword: params.keyword,
    space_id: params.spaceId,
    status: params.status,
    source_type: params.sourceType,
    offset: (params.page - 1) * params.pageSize,
    limit: params.pageSize,
    sort_field: params.sortField,
    sort_order: params.sortOrder,
  }

  const cleanQuery: Record<string, string | number> = {}
  for (const [k, v] of Object.entries(query)) {
    if (v !== undefined && v !== '') {
      cleanQuery[k] = v
    }
  }
  return getData<BackendKBListResponse>(
    request.get('/knowledge-base/knowledge-info', { params: cleanQuery }),
  ).then(mapKBList)
}

interface BackendKBItem {
  id: string
  tenant_id: string
  space_id: string
  space_name?: string
  name: string
  description: string | null
  data_source_types: string[]
  document_count: number
  status: string
  owner_id: string | null
  created_at: string | null
  updated_at: string | null

  entity_count?: number
  relation_count?: number

  ontology_degraded?: boolean
}

interface BackendKBListResponse {
  items: BackendKBItem[]
  total: number
  offset: number
  limit: number
}

function mapKBList(resp: BackendKBListResponse): PaginationResult<DomainKnowledgeItem> {
  const list = resp.items.map(mapKBItem)
  const pageSize = resp.limit || list.length
  const page = pageSize > 0 ? Math.floor((resp.offset || 0) / pageSize) + 1 : 1
  return { list, pagination: { page, pageSize, total: resp.total } }
}


export async function createKnowledgeInfo(data: {
  name: string
  space_id: string
  description?: string
  data_source_types?: string[]
}): Promise<DomainKnowledgeItem> {
  const backendItem = await getData<BackendKBItem>(
    request.post('/knowledge-base/knowledge-info', data),
  )
  return mapKBItem(backendItem)
}


export async function updateKnowledgeInfo(
  kbId: string,
  data: { name?: string; space_id?: string; description?: string; status?: string },
): Promise<DomainKnowledgeItem> {
  const backendItem = await getData<BackendKBItem>(
    request.patch(`/knowledge-base/knowledge-info/${kbId}`, data),
  )
  return mapKBItem(backendItem)
}


export async function deleteKnowledgeInfo(kbId: string): Promise<void> {
  await getData(request.delete(`/knowledge-base/knowledge-info/${kbId}`))
}

function mapKBItem(item: BackendKBItem): DomainKnowledgeItem {
  return {
    id: item.id,
    name: item.name,
    spaceId: item.space_id,
    spaceName: item.space_name || '',
    dataSourceTypes: item.data_source_types as DomainKnowledgeSourceType[],
    documentCount: item.document_count || 0,
    status: item.status as DomainKnowledgeStatus,
    updatedAt: item.updated_at ? formatLocalDateTime(item.updated_at) : '—',
    ownerName: item.owner_id || undefined,
    description: item.description || undefined,
  }
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



export async function getDomainKnowledgeDetail(kbId: string): Promise<DomainKnowledgeDetail> {





  const info = await getData<BackendKBItem>(
    request.get(`/knowledge-base/knowledge-info/${kbId}`),
  )
  return {
    id: info.id,
    name: info.name,
    spaceId: info.space_id,
    spaceName: info.space_name || '',
    documentCount: info.document_count ?? 0,
    entityCount: info.entity_count ?? 0,
    relationCount: info.relation_count ?? 0,
    compileVersionCount: 0,
    status: (info.status as DomainKnowledgeStatus) || 'synced',
    updatedAt: info.updated_at ? formatLocalDateTime(info.updated_at) : '—',
    ontologyDegraded: info.ontology_degraded ?? false,
  }
}

export function getDomainKnowledgeDataSources(kbId: string): Promise<DataSourceConfig[]> {
  return listDataSources(kbId).then((list) =>
    list.map((ds) => {
      const v = DS_VIEW[ds.accessType] || DS_VIEW.file
      return {
        id: ds.id,
        name: ds.name,
        type: v.typeLabel,
        accessType: ds.accessType,
        configJson: ds.configJson || {},
        docs: ds.documentCount,
        status: normalizeDataSourceStatus(ds),
        iconType: v.iconType,
        iconBg: v.iconBg,
        iconColor: v.iconColor,
        path:
          ds.accessType === 'file'
            ? `/domain-knowledge/${kbId}/datasource/manual`
            : `/domain-knowledge/${kbId}/${v.routePrefix}/${ds.id}`,
        knowledgeBaseId: kbId,
      }
    }),
  )
}

const DS_VIEW: Record<
  string,
  { iconType: DataSourceConfig['iconType']; iconBg: string; iconColor: string; typeLabel: string; routePrefix: string }
> = {
  api: { iconType: 'api', iconBg: '#ecfdf5', iconColor: '#10b981', typeLabel: 'dataSource.typeApi', routePrefix: 'datasource/sync' },
  storage: { iconType: 'storage', iconBg: '#fff7ed', iconColor: '#f97316', typeLabel: 'dataSource.storageDirect', routePrefix: 'datasource/storage' },
  api_push: { iconType: 'api', iconBg: '#eff6ff', iconColor: '#3b82f6', typeLabel: 'dataSource.apiPush', routePrefix: 'datasource/api-push' },
  file: { iconType: 'upload', iconBg: '#eff6ff', iconColor: '#3b82f6', typeLabel: 'dataSource.fileUpload', routePrefix: 'datasource/manual' },
}

function normalizeDataSourceStatus(ds: DataSourceInstance): DataSourceConfig['status'] {
  if (ds.status === 'paused') return 'paused'
  if (ds.status === 'error' || ds.lastSyncStatus === 'failed') return 'error'
  return 'running'
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
    knowledge_base_id: params.knowledgeBaseId,
    page: params.page,
    page_size: params.pageSize,
  }
  if (params.keyword) query.keyword = params.keyword
  if (params.entityType) query.entity_type = params.entityType

  return getData<BackendPaginatedResult<BackendEntityItem>>(
    request.get(`/knowledge-base/parse-results/entities`, { params: query }),
  ).then((res) => ({
    list: res.items.map(mapEntityItem),
    pagination: { page: res.page, pageSize: res.page_size, total: res.total },
  }))
}



export function getDomainKnowledgeLogicRules(kbId: string): Promise<LogicRule[]> {
  return getData(request.get(`/core-business/domain-knowledge/${kbId}/logic-rules`))
}

export function getDomainKnowledgeActionRules(kbId: string): Promise<ActionRule[]> {
  return getData(request.get(`/core-business/domain-knowledge/${kbId}/action-rules`))
}

export function getDomainKnowledgeResultStats(kbId: string): Promise<DomainKnowledgeResultStats> {

  return getData<BackendParseResultSummary>(
    request.get(`/knowledge-base/parse-results/summary`, { params: { knowledge_base_id: kbId } }),
  ).then(mapResultStats)
}



let _graphSummaryCache: BackendGraphSummary | null = null

export async function getDomainKnowledgeGraphSummary(kbId: string): Promise<GraphSummary> {

  const backend = await getData<BackendGraphSummary>(
    request.get(`/knowledge-base/parse-results/graph-summary`, { params: { knowledge_base_id: kbId } }),
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

export function getOntologyEditorState(kbId: string): Promise<OntologyEditorState> {
  return getData<OntologyEditorState>(
    request.get('/knowledge-base/ontology/editor-state', { params: { knowledge_base_id: kbId } }),
  )
}

export function saveOntologyCompiledSchema(
  kbId: string,
  entityTypes: CompiledSchemaEntityType[],
  relationTypes: CompiledSchemaRelationType[],
  expectedSchemaVersion: number,
  constraints?: CompiledSchemaConstraint[],
): Promise<CompiledSchema> {
  return putData<CompiledSchema>('/knowledge-base/ontology/compiled-schema', {
    knowledge_base_id: kbId,
    entity_types: entityTypes,
    relation_types: relationTypes,

    expected_schema_version: expectedSchemaVersion,

    ...(constraints !== undefined ? { constraints } : {}),
  })
}

export function reseedOntologyCompiledSchema(
  kbId: string,
  templateScenarioId: string,
  templateDomainId?: string,
): Promise<CompiledSchema> {
  return postData<CompiledSchema>('/knowledge-base/ontology/compiled-schema/reseed', {
    knowledge_base_id: kbId,
    template_domain_id: templateDomainId,
    template_scenario_id: templateScenarioId,
    source_type: 'business_template',
  })
}



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
  page: number
  page_size: number
}

function formatFileSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${bytes} B`
}

function formatLocalDateTime(isoStr: string): string {
  const d = new Date(isoStr)
  if (isNaN(d.getTime())) return '—'
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function mapBackendDoc(doc: BackendDocItem, knowledgeBaseId: string): ManualDocItem {
  const meta = doc.extra_metadata || {}
  return {
    id: doc.id,
    name: doc.file_name,
    type: (doc.file_type || ((doc.file_name || '').split('.').pop() || 'unknown')).toUpperCase(),
    size: typeof doc.file_size === 'number' ? formatFileSize(doc.file_size) : '-',
    uploader: (meta.uploader as string) || '-',
    uploadTime: doc.created_at ? formatLocalDateTime(doc.created_at) : '-',
    status: doc.status === 'ready' ? '入库·解析·编译' : doc.status === 'parsing' ? '入库·解析中' : doc.status === 'pending' ? '入库' : doc.status,
    knowledgeBaseId,
  }
}

export async function getManualDocList(
  params: ManualDocListParams,
): Promise<PaginationResult<ManualDocItem>> {


  const backendParams: Record<string, string | number> = {
    knowledge_base_id: params.knowledgeBaseId,
    page: params.page,
    page_size: params.pageSize,
  }
  if (params.status) backendParams.status = params.status
  if (params.keyword) backendParams.keyword = params.keyword

  const backendResult = await getData<BackendDocListResponse>(
    request.get('/knowledge-base/documents', { params: backendParams }),
  )



  const list = backendResult.items.map((d) => mapBackendDoc(d, params.knowledgeBaseId))
  return {
    list,
    pagination: {
      page: backendResult.page ?? params.page,
      pageSize: backendResult.page_size ?? params.pageSize,
      total: backendResult.total ?? list.length,
    },
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

export async function deleteManualDocument(
  knowledgeBaseId: string,
  documentId: string,
): Promise<void> {
  await getData(
    request.delete(`/knowledge-base/documents/${documentId}`, {
      params: { knowledge_base_id: knowledgeBaseId },
    }),
  )
}

const RAW_API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || '/api/v1'







export async function fetchManualDocumentRawUrl(documentId: string): Promise<string> {
  const token = readAccessToken()
  const resp = await axios.get(
    `${RAW_API_BASE}/knowledge-base/documents/${documentId}/raw`,
    {
      responseType: 'blob',
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    },
  )
  let blob = resp.data as Blob



  const baseType = (blob.type || '').split(';')[0].trim().toLowerCase()
  const isText =
    baseType.startsWith('text/') ||
    baseType === 'application/json' ||
    baseType === 'application/xml' ||
    baseType === 'application/javascript'
  if (isText) {
    const text = await blob.text()
    blob = new Blob([text], { type: 'text/plain; charset=utf-8' })
  }
  return URL.createObjectURL(blob)
}






export async function getDocumentViewTicket(
  documentId: string,
): Promise<{ url: string; expiresIn: number }> {
  const res = await getData<{ url: string; expires_in: number }>(
    request.get(`/knowledge-base/documents/${documentId}/view-ticket`),
  )
  return { url: res.url, expiresIn: res.expires_in }
}



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
      ? formatLocalDateTime(new Date(b.created_at * 1000).toISOString())
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



const UI_ID_SEP = '|'

function encodeUiId(prefix: string, ...parts: Array<string | null | undefined>): string {
  return [prefix, ...parts.map((part) => encodeURIComponent(part || ''))].join(UI_ID_SEP)
}

function decodeUiId(id: string, expectedPrefix: string): string[] {
  const parts = (id || '').split(UI_ID_SEP)
  if (parts[0] !== expectedPrefix) return []
  return parts.slice(1).map((part) => decodeURIComponent(part))
}

function slugifyOntologyName(value: string): string {
  return (value || '')
    .trim()
    .replace(/[\s/\\]+/g, '_')
    .replace(/[^a-zA-Z0-9_\u4e00-\u9fff]/g, '') || 'unknown'
}

function ensureUniqueName(base: string, existing: Set<string>): string {
  let next = base || 'unknown'
  let idx = 2
  while (existing.has(next)) {
    next = `${base || 'unknown'}_${idx}`
    idx += 1
  }
  return next
}

function compiledAttrToOntologyType(type?: string): OntologyObjectDef['attributes'][number]['type'] {
  const mapping: Record<string, OntologyObjectDef['attributes'][number]['type']> = {
    string: '字符串',
    text: '文本',
    number: '数值',
    date: '日期',
    enum: '枚举',
    boolean: '布尔',
  }
  return mapping[(type || '').toLowerCase()] || '字符串'
}

function ontologyAttrToCompiledType(type?: OntologyObjectDef['attributes'][number]['type']): CompiledSchemaEntityType['attributes'][number]['type'] {
  const mapping: Record<string, CompiledSchemaEntityType['attributes'][number]['type']> = {
    '字符串': 'string',
    '文本': 'text',
    '数值': 'number',
    '日期': 'date',
    '枚举': 'enum',
    '布尔': 'boolean',
  }
  return mapping[type || ''] || 'string'
}

function compiledCardinalityToOntologyType(cardinality?: string): OntologyRelationDef['relationType'] {
  const mapping: Record<string, OntologyRelationDef['relationType']> = {
    one_to_one: '一对一',
    one_to_many: '一对多',
    many_to_one: '多对一',
    many_to_many: '多对多',
    custom: '自定义',
  }
  return mapping[(cardinality || '').toLowerCase()] || '自定义'
}

function ontologyRelationToCompiledCardinality(type?: OntologyRelationDef['relationType']): CompiledSchemaRelationType['cardinality'] {
  const mapping: Record<string, CompiledSchemaRelationType['cardinality']> = {
    '一对一': 'one_to_one',
    '一对多': 'one_to_many',
    '多对一': 'many_to_one',
    '多对多': 'many_to_many',
    '自定义': 'custom',
  }
  return mapping[type || ''] || 'custom'
}

function buildEntityDisplayMap(entityTypes: CompiledSchemaEntityType[]): Map<string, string> {
  return new Map(entityTypes.map((entity) => [entity.name, entity.display_name || entity.name]))
}

function normalizeCompiledSchemaForEditing(schema: CompiledSchema, kbId: string): CompiledSchema {
  const entityTypes = (schema.entity_types || []).map((entity) => ({
    ...entity,
    name: entity.name || slugifyOntologyName(entity.display_name || `entity_${kbId}`),
    display_name: entity.display_name || entity.name,
    description: entity.description || '',
    requirement: entity.requirement || '',
    status: entity.status || 'active',
    aliases: entity.aliases || [],
    attributes: (entity.attributes || []).map((attr) => ({
      ...attr,
      name: attr.name || slugifyOntologyName(attr.display_name || 'attr'),
      display_name: attr.display_name || attr.name,
      description: attr.description || '',
      type: ontologyAttrToCompiledType(compiledAttrToOntologyType(attr.type)),
      required: Boolean(attr.is_primary_key ?? attr.required),
      is_primary_key: Boolean(attr.is_primary_key ?? attr.required),
    })),
  }))

  const codeByDisplay = new Map<string, string>()
  entityTypes.forEach((entity) => {
    codeByDisplay.set(entity.name, entity.name)
    codeByDisplay.set(entity.display_name || entity.name, entity.name)
  })

  const relationTypes = (schema.relation_types || []).map((relation) => ({
    ...relation,
    name: relation.name || slugifyOntologyName(relation.display_name || 'relation'),
    display_name: relation.display_name || relation.name,
    description: relation.description || '',
    status: relation.status || 'active',
    aliases: relation.aliases || [],
    source: codeByDisplay.get(relation.source) || relation.source,
    target: codeByDisplay.get(relation.target) || relation.target,
    cardinality: ontologyRelationToCompiledCardinality(compiledCardinalityToOntologyType(relation.cardinality)),
  }))

  return {
    ...schema,
    entity_types: entityTypes,
    relation_types: relationTypes,
  }
}

function mapCompiledEntityToOntology(kbId: string, entity: CompiledSchemaEntityType): OntologyObjectDef {
  return {
    id: encodeUiId('obj', entity.name, entity.source_object_id || ''),
    knowledgeBaseId: kbId,
    name: entity.display_name || entity.name,
    description: entity.description || '',
    requirement: entity.requirement || '',
    status: entity.status || 'active',
    attributes: (entity.attributes || []).map((attr) => ({
      id: encodeUiId('attr', entity.name, attr.name, attr.source_attribute_id || ''),
      name: attr.display_name || attr.name,
      description: attr.description || '',
      type: compiledAttrToOntologyType(attr.type),
      isPrimaryKey: Boolean(attr.is_primary_key ?? attr.required),
    })),
  }
}

function mapCompiledRelationToOntology(
  kbId: string,
  relation: CompiledSchemaRelationType,
  entityDisplayMap: Map<string, string>,
): OntologyRelationDef {
  return {
    id: encodeUiId('rel', relation.name, relation.source, relation.target, relation.source_relation_id || ''),
    knowledgeBaseId: kbId,
    sourceObject: entityDisplayMap.get(relation.source) || relation.source,
    name: relation.display_name || relation.name,
    targetObject: entityDisplayMap.get(relation.target) || relation.target,
    description: relation.description || '',
    relationType: compiledCardinalityToOntologyType(relation.cardinality),
    status: relation.status || 'active',
  }
}

async function fetchCompiledSchemaForEditing(kbId: string): Promise<CompiledSchema> {
  let schema: CompiledSchema | null = null
  try {
    schema = await getData<CompiledSchema | null>(
      request.get('/knowledge-base/ontology/compiled-schema', { params: { knowledge_base_id: kbId } }),
    )
  } catch (error: any) {
    if (error?.response?.status === 405) {
      const editorState = await getOntologyEditorState(kbId)
      schema = editorState?.compiled_schema || null
    } else {
      throw error
    }
  }
  const fallbackSchema = schema || {
    knowledge_base_id: kbId,
    source_version: 1,
    schema_version: 1,
    entity_types: [],
    relation_types: [],
    constraints: [],
    disambiguation: {},
    prompt_schema: {},
    status: 'active',
    schema_mode: 'manual_edited',
    sync_status: 'synced',
  }
  return normalizeCompiledSchemaForEditing(fallbackSchema, kbId)
}

async function persistCompiledOntology(
  kbId: string,
  entityTypes: CompiledSchemaEntityType[],
  relationTypes: CompiledSchemaRelationType[],
  expectedSchemaVersion: number,
  constraints?: CompiledSchemaConstraint[],
): Promise<CompiledSchema> {
  return saveOntologyCompiledSchema(kbId, entityTypes, relationTypes, expectedSchemaVersion, constraints)
}


function readSchemaConstraints(schema: CompiledSchema): CompiledSchemaConstraint[] {
  return ((schema.constraints as unknown as CompiledSchemaConstraint[]) || []).filter(
    (c) => c && typeof (c as any).target_code === 'string' && (c as any).target_code,
  )
}


function pruneDanglingConstraints(
  constraints: CompiledSchemaConstraint[],
  entityTypes: CompiledSchemaEntityType[],
  relationTypes: CompiledSchemaRelationType[],
): CompiledSchemaConstraint[] {
  const entityCodes = new Set(entityTypes.map((e) => e.name))
  const attrCodes = new Set(
    entityTypes.flatMap((e) => (e.attributes || []).map((a) => `${e.name}.${a.name}`)),
  )
  const relationCodes = new Set(relationTypes.map((r) => r.name))
  return constraints.filter((c) => {
    if (c.target_type === 'entity') return entityCodes.has(c.target_code)
    if (c.target_type === 'attribute') return attrCodes.has(c.target_code)
    if (c.target_type === 'relation') return relationCodes.has(c.target_code)
    return false
  })
}

function mapCompiledConstraintToUi(c: CompiledSchemaConstraint): OntologyConstraint | null {
  if (!c || !c.target_code) return null
  return {
    id: encodeUiId('constraint', c.name),
    name: c.name,
    targetType: c.target_type,
    targetCode: c.target_code,
    targetLabel: c.target_label ?? undefined,
    constraintType: normalizeConstraintType(c.constraint_type),
    expression: c.expression || '',
    suggestion: c.suggestion || '',
  }
}

function buildCompiledConstraintFromPayload(p: SaveOntologyConstraintPayload): CompiledSchemaConstraint {
  return {
    name: (p.name || '').trim(),
    target_type: p.targetType,
    target_code: p.targetCode,
    target_label: p.targetLabel || null,
    constraint_type: normalizeConstraintType(p.constraintType),
    expression: (p.expression || '').trim(),
    suggestion: (p.suggestion || '').trim(),
  }
}

function decodeEntityMeta(id: string): { compiledName: string; sourceObjectId?: string | null } {
  const [compiledName, sourceObjectId] = decodeUiId(id, 'obj')
  return { compiledName: compiledName || '', sourceObjectId: sourceObjectId || null }
}

function decodeAttrMeta(id?: string): { compiledName: string; sourceAttributeId?: string | null } {
  const [, compiledName, sourceAttributeId] = decodeUiId(id || '', 'attr')
  return { compiledName: compiledName || '', sourceAttributeId: sourceAttributeId || null }
}

function decodeRelationMeta(id: string): {
  compiledName: string
  source: string
  target: string
  sourceRelationId?: string | null
} {
  const [compiledName, source, target, sourceRelationId] = decodeUiId(id, 'rel')
  return {
    compiledName: compiledName || '',
    source: source || '',
    target: target || '',
    sourceRelationId: sourceRelationId || null,
  }
}

function buildCompiledEntityFromPayload(
  payload: SaveOntologyObjectPayload,
  existingNames: Set<string>,
  existing?: CompiledSchemaEntityType,
): CompiledSchemaEntityType {
  const compiledName = existing?.name || ensureUniqueName(slugifyOntologyName(payload.name), existingNames)
  const attrNames = new Set<string>()
  return {
    name: compiledName,
    display_name: payload.name,
    description: payload.description || '',
    requirement: payload.requirement || '',
    status: payload.status || 'active',
    aliases: existing?.aliases || [],
    source_object_id: existing?.source_object_id || null,
    attributes: (payload.attributes || []).map((attr) => {
      const attrMeta = decodeAttrMeta(attr.id)
      const attrName = attrMeta.compiledName || ensureUniqueName(slugifyOntologyName(attr.name), attrNames)
      attrNames.add(attrName)
      return {
        name: attrName,
        display_name: attr.name,
        description: attr.description || '',
        type: ontologyAttrToCompiledType(attr.type),
        required: Boolean(attr.isPrimaryKey),
        is_primary_key: Boolean(attr.isPrimaryKey),
        source_attribute_id: attrMeta.sourceAttributeId || null,
      }
    }),
  }
}

function buildCompiledRelationFromPayload(
  payload: SaveOntologyRelationPayload,
  entityTypes: CompiledSchemaEntityType[],
  existingNames: Set<string>,
  existing?: CompiledSchemaRelationType,
): CompiledSchemaRelationType {
  const entityCodeByDisplay = new Map<string, string>()
  entityTypes.forEach((entity) => {
    entityCodeByDisplay.set(entity.display_name || entity.name, entity.name)
    entityCodeByDisplay.set(entity.name, entity.name)
  })

  const sourceCode = entityCodeByDisplay.get(payload.sourceObject)
  const targetCode = entityCodeByDisplay.get(payload.targetObject)
  if (!sourceCode || !targetCode) {
    throw new Error(i18next.t('ontology.relationEntityMissing'))
  }

  return {
    name: existing?.name || ensureUniqueName(slugifyOntologyName(payload.name), existingNames),
    display_name: payload.name,
    description: payload.description || '',
    status: payload.status || 'active',
    aliases: existing?.aliases || [],
    source: sourceCode,
    target: targetCode,
    source_relation_id: existing?.source_relation_id || null,
    cardinality: ontologyRelationToCompiledCardinality(payload.relationType),
  }
}

export async function getOntologyObjects(kbId: string): Promise<OntologyObjectDef[]> {
  const schema = await fetchCompiledSchemaForEditing(kbId)
  return (schema.entity_types || []).map((entity) => mapCompiledEntityToOntology(kbId, entity))
}

export async function createOntologyObject(kbId: string, p: SaveOntologyObjectPayload): Promise<OntologyObjectDef> {
  const schema = await fetchCompiledSchemaForEditing(kbId)
  const entityTypes = schema.entity_types || []
  const nextEntity = buildCompiledEntityFromPayload(p, new Set(entityTypes.map((entity) => entity.name)))

  await persistCompiledOntology(kbId, [...entityTypes, nextEntity], schema.relation_types || [], schema.schema_version)
  return mapCompiledEntityToOntology(kbId, nextEntity)
}

export async function updateOntologyObject(kbId: string, id: string, p: SaveOntologyObjectPayload): Promise<OntologyObjectDef> {
  const schema = await fetchCompiledSchemaForEditing(kbId)
  const entityTypes = schema.entity_types || []
  const relationTypes = schema.relation_types || []
  const meta = decodeEntityMeta(id)
  const current = entityTypes.find((entity) => entity.name === meta.compiledName)
  if (!current) throw new Error(i18next.t('ontology.objectNotFound'))

  const nextEntity = buildCompiledEntityFromPayload(p, new Set(entityTypes.map((entity) => entity.name)), current)
  const nextEntities = entityTypes.map((entity) => (entity.name === current.name ? nextEntity : entity))

  const nextConstraints = pruneDanglingConstraints(readSchemaConstraints(schema), nextEntities, relationTypes)
  await persistCompiledOntology(kbId, nextEntities, relationTypes, schema.schema_version, nextConstraints)
  return mapCompiledEntityToOntology(kbId, nextEntity)
}

export async function deleteOntologyObject(kbId: string, id: string): Promise<boolean> {
  const schema = await fetchCompiledSchemaForEditing(kbId)
  const meta = decodeEntityMeta(id)
  const nextEntities = (schema.entity_types || []).filter((entity) => entity.name !== meta.compiledName)
  const nextRelations = (schema.relation_types || []).filter(
    (relation) => relation.source !== meta.compiledName && relation.target !== meta.compiledName,
  )

  const nextConstraints = pruneDanglingConstraints(readSchemaConstraints(schema), nextEntities, nextRelations)
  await persistCompiledOntology(kbId, nextEntities, nextRelations, schema.schema_version, nextConstraints)
  return true
}

export async function getOntologyRelations(kbId: string): Promise<OntologyRelationDef[]> {
  const schema = await fetchCompiledSchemaForEditing(kbId)
  const entityDisplayMap = buildEntityDisplayMap(schema.entity_types || [])
  return (schema.relation_types || []).map((relation) => mapCompiledRelationToOntology(kbId, relation, entityDisplayMap))
}

export async function createOntologyRelation(kbId: string, p: SaveOntologyRelationPayload): Promise<OntologyRelationDef> {
  const schema = await fetchCompiledSchemaForEditing(kbId)
  const relationTypes = schema.relation_types || []
  const nextRelation = buildCompiledRelationFromPayload(
    p,
    schema.entity_types || [],
    new Set(relationTypes.map((relation) => relation.name)),
  )
  const nextRelations = [...relationTypes, nextRelation]
  await persistCompiledOntology(kbId, schema.entity_types || [], nextRelations, schema.schema_version)
  const entityDisplayMap = buildEntityDisplayMap(schema.entity_types || [])
  return mapCompiledRelationToOntology(kbId, nextRelation, entityDisplayMap)
}

export async function updateOntologyRelation(kbId: string, id: string, p: SaveOntologyRelationPayload): Promise<OntologyRelationDef> {
  const schema = await fetchCompiledSchemaForEditing(kbId)
  const entityTypes = schema.entity_types || []
  const relationTypes = schema.relation_types || []
  const meta = decodeRelationMeta(id)
  const current = relationTypes.find(
    (relation) => relation.name === meta.compiledName && relation.source === meta.source && relation.target === meta.target,
  )
  if (!current) throw new Error(i18next.t('ontology.relationNotFound'))

  const nextRelation = buildCompiledRelationFromPayload(
    p,
    entityTypes,
    new Set(relationTypes.map((relation) => relation.name)),
    current,
  )
  const nextRelations = relationTypes.map((relation) =>
    relation.name === current.name && relation.source === current.source && relation.target === current.target
      ? nextRelation
      : relation,
  )
  await persistCompiledOntology(kbId, entityTypes, nextRelations, schema.schema_version)
  return mapCompiledRelationToOntology(kbId, nextRelation, buildEntityDisplayMap(entityTypes))
}

export async function deleteOntologyRelation(kbId: string, id: string): Promise<boolean> {
  const schema = await fetchCompiledSchemaForEditing(kbId)
  const meta = decodeRelationMeta(id)
  const nextRelations = (schema.relation_types || []).filter(
    (relation) =>
      !(relation.name === meta.compiledName && relation.source === meta.source && relation.target === meta.target),
  )

  const nextConstraints = pruneDanglingConstraints(readSchemaConstraints(schema), schema.entity_types || [], nextRelations)
  await persistCompiledOntology(kbId, schema.entity_types || [], nextRelations, schema.schema_version, nextConstraints)
  return true
}




export interface ConstraintTargetOption {
  value: string
  label: string
}
export interface ConstraintTargetOptions {
  entity: ConstraintTargetOption[]
  attribute: ConstraintTargetOption[]
  relation: ConstraintTargetOption[]
}

export async function getConstraintTargetOptions(kbId: string): Promise<ConstraintTargetOptions> {
  const schema = await fetchCompiledSchemaForEditing(kbId)
  const entity = (schema.entity_types || []).map((e) => ({
    value: e.name,
    label: e.display_name || e.name,
  }))
  const attribute = (schema.entity_types || []).flatMap((e) =>
    (e.attributes || []).map((a) => ({
      value: `${e.name}.${a.name}`,
      label: `${e.display_name || e.name}.${a.display_name || a.name}`,
    })),
  )
  const relation = (schema.relation_types || []).map((r) => ({
    value: r.name,
    label: r.display_name || r.name,
  }))
  return { entity, attribute, relation }
}

export async function getOntologyConstraints(kbId: string): Promise<OntologyConstraint[]> {
  const schema = await fetchCompiledSchemaForEditing(kbId)
  return readSchemaConstraints(schema)
    .map(mapCompiledConstraintToUi)
    .filter((c): c is OntologyConstraint => c !== null)
}

export async function createOntologyConstraint(
  kbId: string,
  p: SaveOntologyConstraintPayload,
): Promise<OntologyConstraint> {
  const schema = await fetchCompiledSchemaForEditing(kbId)
  const constraints = readSchemaConstraints(schema)
  const name = (p.name || '').trim()
  if (constraints.some((c) => c.name === name)) {
    throw new Error(i18next.t('common.createFailed') + `：${name}`)
  }
  const next = buildCompiledConstraintFromPayload({ ...p, name })
  await persistCompiledOntology(
    kbId,
    schema.entity_types || [],
    schema.relation_types || [],
    schema.schema_version,
    [...constraints, next],
  )
  return mapCompiledConstraintToUi(next) as OntologyConstraint
}

export async function updateOntologyConstraint(
  kbId: string,
  id: string,
  p: SaveOntologyConstraintPayload,
): Promise<OntologyConstraint> {
  const schema = await fetchCompiledSchemaForEditing(kbId)
  const constraints = readSchemaConstraints(schema)
  const [originalName] = decodeUiId(id, 'constraint')
  const current = constraints.find((c) => c.name === originalName)
  if (!current) throw new Error(i18next.t('ontology.constraintNotFound'))
  const nextName = (p.name || '').trim()
  if (nextName !== originalName && constraints.some((c) => c.name === nextName)) {
    throw new Error(i18next.t('common.updateFailed') + `：${nextName}`)
  }
  const next = buildCompiledConstraintFromPayload({ ...p, name: nextName })
  const nextConstraints = constraints.map((c) => (c.name === originalName ? next : c))
  await persistCompiledOntology(
    kbId,
    schema.entity_types || [],
    schema.relation_types || [],
    schema.schema_version,
    nextConstraints,
  )
  return mapCompiledConstraintToUi(next) as OntologyConstraint
}

export async function deleteOntologyConstraint(kbId: string, id: string): Promise<boolean> {
  const schema = await fetchCompiledSchemaForEditing(kbId)
  const constraints = readSchemaConstraints(schema)
  const [originalName] = decodeUiId(id, 'constraint')
  const nextConstraints = constraints.filter((c) => c.name !== originalName)
  await persistCompiledOntology(
    kbId,
    schema.entity_types || [],
    schema.relation_types || [],
    schema.schema_version,
    nextConstraints,
  )
  return true
}

export async function getCompileSteps(kbId: string): Promise<CompileStep[]> {

  return []
}
export async function createCompileStep(kbId: string, p: SaveCompileStepPayload): Promise<CompileStep> {

  throw new Error(i18next.t('ontology.notImplemented'))
}
export async function updateCompileStep(kbId: string, id: string, p: SaveCompileStepPayload): Promise<CompileStep> {

  throw new Error(i18next.t('ontology.notImplemented'))
}
export async function deleteCompileStep(kbId: string, id: string): Promise<boolean> {

  throw new Error(i18next.t('ontology.notImplemented'))
}
export async function getEngineSetting(kbId: string): Promise<EngineSetting> {

  return { knowledgeBaseId: kbId, semanticModel: 'claude-sonnet-4-6' }
}
export async function saveEngineSetting(kbId: string, semanticModel: string): Promise<EngineSetting> {

  return { knowledgeBaseId: kbId, semanticModel }
}


export interface ParserConfigItem {
  id: string
  tenant_id: string
  name: string
  parser_type: string
  file_types: string[]
  config_json: Record<string, any>
  status: string
  created_at: string
  updated_at: string
}

export async function getParserConfigs(
  offset = 0,
  limit = 100,
): Promise<{ items: ParserConfigItem[]; total: number }> {
  return getData<{ items: ParserConfigItem[]; total: number }>(
    request.get('/ecosystem/parser-configs', { params: { offset, limit } }),
  )
}

export interface ParserSettingItem {
  id: string
  tenant_id: string
  knowledge_base_id: string
  file_type: string
  file_type_label: string
  parser_config_id?: string | null
  parser_name?: string
  parser_type?: string
  parser_file_types?: string[]
  parser_status?: string | null
  preprocessing_json: string[]
  postprocessing_json: string[]
  prompt_text?: string
  prompt_template_id?: string | null
  prompt_template_version?: string | null
  summary_prompt_text?: string
  summary_template_id?: string | null
  summary_template_version?: string | null
  tag_prompt_text?: string
  tag_template_id?: string | null
  tag_template_version?: string | null
  status: string
  created_at?: string | null
  updated_at?: string | null
}

export interface ParserSettingPayload {
  knowledge_base_id: string
  file_type: string
  file_type_label: string
  parser_config_id?: string | null
  preprocessing_json?: string[]
  postprocessing_json?: string[]
  prompt_text?: string
  prompt_template_id?: string | null
  prompt_template_version?: string | null
  summary_prompt_text?: string
  summary_template_id?: string | null
  summary_template_version?: string | null
  tag_prompt_text?: string
  tag_template_id?: string | null
  tag_template_version?: string | null
  status?: string
}

export async function getParserSettings(
  knowledgeBaseId: string,
): Promise<{ items: ParserSettingItem[]; total: number }> {
  return getData<{ items: ParserSettingItem[]; total: number }>(
    request.get('/knowledge-base/parser-settings', {
      params: { knowledge_base_id: knowledgeBaseId },
    }),
  )
}

export async function createParserSetting(payload: ParserSettingPayload): Promise<ParserSettingItem> {
  return postData<ParserSettingItem>('/knowledge-base/parser-settings', payload)
}

export async function updateParserSetting(
  settingId: string,
  payload: Partial<ParserSettingPayload>,
): Promise<ParserSettingItem> {
  return getData<ParserSettingItem>(
    request.patch(`/knowledge-base/parser-settings/${settingId}`, payload),
  )
}

export async function deleteParserSetting(settingId: string): Promise<{ deleted: boolean; id: string }> {
  return deleteData<{ deleted: boolean; id: string }>(`/knowledge-base/parser-settings/${settingId}`)
}

export interface PromptTemplateVersionItem {
  version: string
  content: string
  updated_by?: string
  updated_at?: string
  remark?: string
}

export interface PromptTemplateListItem {
  id: string
  tenant_id: string | null
  name: string
  category: string
  scope: 'system' | 'domain'
  description?: string
  status: string
  current_version: string
  versions_json: PromptTemplateVersionItem[]
  created_by?: string
  created_at: string | null
  updated_at: string | null
}

export async function listPromptTemplates(params: {
  scope?: string
  category?: string
  keyword?: string
  offset?: number
  limit?: number
} = {}): Promise<{ items: PromptTemplateListItem[]; total: number; offset: number; limit: number }> {
  return getData<{ items: PromptTemplateListItem[]; total: number; offset: number; limit: number }>(
    request.get('/ecosystem/prompt-templates', { params }),
  )
}

export async function importOntologyObjectsFromTemplate(
  kbId: string,
  items: SaveOntologyObjectPayload[],
): Promise<{ created: OntologyObjectDef[]; skipped: number }> {
  const schema = await fetchCompiledSchemaForEditing(kbId)
  const entityTypes = [...(schema.entity_types || [])]
  const existingDisplayNames = new Set(entityTypes.map((entity) => entity.display_name || entity.name))
  const existingCodes = new Set(entityTypes.map((entity) => entity.name))
  const createdCompiled: CompiledSchemaEntityType[] = []
  let skipped = 0

  for (const item of items) {
    if (existingDisplayNames.has(item.name)) {
      skipped += 1
      continue
    }
    const nextEntity = buildCompiledEntityFromPayload(item, existingCodes)
    existingDisplayNames.add(item.name)
    existingCodes.add(nextEntity.name)
    entityTypes.push(nextEntity)
    createdCompiled.push(nextEntity)
  }

  if (createdCompiled.length > 0) {
    await persistCompiledOntology(kbId, entityTypes, schema.relation_types || [], schema.schema_version)
  }

  return {
    created: createdCompiled.map((entity) => mapCompiledEntityToOntology(kbId, entity)),
    skipped,
  }
}

export async function importOntologyRelationsFromTemplate(
  kbId: string,
  items: SaveOntologyRelationPayload[],
): Promise<{ created: OntologyRelationDef[]; skipped: number }> {
  const schema = await fetchCompiledSchemaForEditing(kbId)
  const entityTypes = schema.entity_types || []
  const relationTypes = [...(schema.relation_types || [])]
  const existingKeys = new Set(relationTypes.map((relation) => `${relation.source}|${relation.display_name || relation.name}|${relation.target}`))
  const existingNames = new Set(relationTypes.map((relation) => relation.name))
  const createdCompiled: CompiledSchemaRelationType[] = []
  let skipped = 0

  for (const item of items) {
    const entityCodeByDisplay = new Map<string, string>()
    entityTypes.forEach((entity) => {
      entityCodeByDisplay.set(entity.display_name || entity.name, entity.name)
      entityCodeByDisplay.set(entity.name, entity.name)
    })
    const sourceCode = entityCodeByDisplay.get(item.sourceObject)
    const targetCode = entityCodeByDisplay.get(item.targetObject)
    if (!sourceCode || !targetCode) {
      skipped += 1
      continue
    }
    const key = `${sourceCode}|${item.name}|${targetCode}`
    if (existingKeys.has(key)) {
      skipped += 1
      continue
    }
    const nextRelation = buildCompiledRelationFromPayload(item, entityTypes, existingNames)
    existingKeys.add(`${nextRelation.source}|${nextRelation.display_name || nextRelation.name}|${nextRelation.target}`)
    existingNames.add(nextRelation.name)
    relationTypes.push(nextRelation)
    createdCompiled.push(nextRelation)
  }

  if (createdCompiled.length > 0) {
    await persistCompiledOntology(kbId, entityTypes, relationTypes, schema.schema_version)
  }

  const entityDisplayMap = buildEntityDisplayMap(entityTypes)
  return {
    created: createdCompiled.map((relation) => mapCompiledRelationToOntology(kbId, relation, entityDisplayMap)),
    skipped,
  }
}






export function getOntologyStatistics(kbId: string): Promise<OntologyStatistics> {
  return getData<OntologyStatistics>(
    request.get('/knowledge-base/ontology/statistics', {
      params: { knowledge_base_id: kbId },
    }),
  )
}


export function getOntologyEntityTypes(kbId: string): Promise<{ items: OntologyInstanceSummary[]; total: number }> {
  return getData<{ items: OntologyInstanceSummary[]; total: number }>(
    request.get('/knowledge-base/ontology/entity-types', {
      params: { knowledge_base_id: kbId },
    }),
  )
}


export function getOntologyRelationTypes(kbId: string): Promise<{ items: RelationInstanceSummary[]; total: number }> {
  return getData<{ items: RelationInstanceSummary[]; total: number }>(
    request.get('/knowledge-base/ontology/relation-types', {
      params: { knowledge_base_id: kbId },
    }),
  )
}


export function getOntologyInstances(
  params: OntologyInstanceListParams,
): Promise<{ items: OntologyInstanceRow[]; total: number; page: number; page_size: number }> {
  const query: Record<string, string | number | undefined> = {
    knowledge_base_id: params.kbId,
    page: params.page,
    page_size: params.pageSize,
    entity_type: params.entityType,
    keyword: params.keyword,
  }
  const cleanQuery: Record<string, string | number> = {}
  for (const [k, v] of Object.entries(query)) {
    if (v !== undefined && v !== '') cleanQuery[k] = v
  }
  return getData<{ items: OntologyInstanceRow[]; total: number; page: number; page_size: number }>(
    request.get('/knowledge-base/ontology/instances', { params: cleanQuery }),
  )
}


export function getOntologyRelationInstances(
  params: RelationInstanceListParams,
): Promise<{ items: RelationInstanceRow[]; total: number; page: number; page_size: number }> {
  const query: Record<string, string | number | undefined> = {
    knowledge_base_id: params.kbId,
    page: params.page,
    page_size: params.pageSize,
    relation_type: params.relationType,
    source_name: params.sourceName,
    target_name: params.targetName,
    source_type: params.sourceType,
    target_type: params.targetType,
  }
  const cleanQuery: Record<string, string | number> = {}
  for (const [k, v] of Object.entries(query)) {
    if (v !== undefined && v !== '') cleanQuery[k] = v
  }
  return getData<{ items: RelationInstanceRow[]; total: number; page: number; page_size: number }>(
    request.get('/knowledge-base/ontology/relations', { params: cleanQuery }),
  )
}


export function getOntologyGraph(
  kbId: string,
  params?: OntologyGraphParams,
): Promise<OntologyGraphData> {
  return getData<OntologyGraphData>(
    request.get('/knowledge-base/ontology/graph', {
      params: {
        knowledge_base_id: kbId,
        limit: params?.limit,
        entity_types: params?.entityTypes,
      },

      paramsSerializer: { indexes: null },
    }),
  )
}


export function expandOntologyNeighbors(
  kbId: string,
  entityType: string,
  canonicalName: string,
  limit = 50,
): Promise<OntologyNeighborData> {
  return getData<OntologyNeighborData>(
    request.get('/knowledge-base/ontology/neighbors', {
      params: {
        knowledge_base_id: kbId,
        entity_type: entityType,
        canonical_name: canonicalName,
        limit,
      },
    }),
  )
}
