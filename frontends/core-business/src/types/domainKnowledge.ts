export type DomainKnowledgeStatus = 'synced' | 'syncing' | 'failed' | 'disabled'

export type DomainKnowledgeSourceType =
  | 'api_sync'
  | 'manual_upload'
  | 'storage_direct'

export interface DomainKnowledgeSpace {
  id: string
  name: string
}

export interface DomainKnowledgeItem {
  id: string
  name: string
  spaceId: string
  spaceName: string
  dataSourceTypes: DomainKnowledgeSourceType[]
  documentCount: number
  status: DomainKnowledgeStatus
  updatedAt: string
  ownerName?: string
  description?: string
}

export interface DomainKnowledgeListParams {
  keyword?: string
  spaceId?: string
  status?: DomainKnowledgeStatus
  sourceType?: DomainKnowledgeSourceType
  page: number
  pageSize: number
  sortField?: 'updatedAt' | 'documentCount' | 'name'
  sortOrder?: 'ascend' | 'descend'
}

export interface PaginationResult<T> {
  list: T[]
  pagination: {
    page: number
    pageSize: number
    total: number
  }
}

export type DomainKnowledgePermissionRole = 'view' | 'manage'

export interface DomainKnowledgePermissionMember {
  userId: string
  name: string
  dept: string
  avatarText: string
  avatarColor: string
  role: DomainKnowledgePermissionRole
}

export interface DomainKnowledgePermissionPayload {
  members: Array<{
    userId: string
    role: DomainKnowledgePermissionRole
  }>
}

export const statusTextMap: Record<DomainKnowledgeStatus, string> = {
  synced: '已同步',
  syncing: '同步中',
  failed: '同步失败',
  disabled: '已停用',
}

export const sourceTypeTextMap: Record<DomainKnowledgeSourceType, string> = {
  api_sync: 'API同步',
  manual_upload: '手动上传',
  storage_direct: '文件存储直连',
}

export const statusColorMap: Record<DomainKnowledgeStatus, string> = {
  synced: 'success',
  syncing: 'processing',
  failed: 'error',
  disabled: 'default',
}

// ─── Detail Page Types ──────────────────────────────────

export interface DomainKnowledgeDetail {
  id: string
  name: string
  spaceId: string
  spaceName: string
  documentCount: number
  entityCount: number
  relationCount: number
  compileVersionCount: number
  status: DomainKnowledgeStatus
  updatedAt: string
}

export interface DataSourceConfig {
  id: string
  name: string
  type: string
  docs: number
  status: string
  desc: string
  iconType: 'api' | 'upload' | 'storage'
  iconBg: string
  iconColor: string
  path: string
  knowledgeBaseId: string
}

export interface ParserFileConfig {
  type: string
  iconType: 'pdf' | 'word' | 'excel' | 'ppt' | 'image' | 'audio' | 'video'
  iconColor: string
  parser: string
  status: string
  knowledgeBaseId: string
}

export interface OntologyTemplate {
  id: string
  type: string
  attrs: string
  relations: string
  version: string
  status: string
  knowledgeBaseId: string
}

export type ValidationSeverity = '高' | '中' | '低'

export interface ValidationRule {
  id: string
  name: string
  entity: string
  condition: string
  severity: ValidationSeverity
  status: string
  knowledgeBaseId: string
}

export const severityColorMap: Record<ValidationSeverity, string> = {
  '高': 'error',
  '中': 'warning',
  '低': 'processing',
}

export interface PromptTemplate {
  id: string
  name: string
  stage: string
  model: string
  author: string
  date: string
  status: string
  knowledgeBaseId: string
}

export interface CompileEntity {
  id: string
  name: string
  type: string
  attrs: number
  relations: number
  createdAt: string
  knowledgeBaseId: string
}

export interface EntityListParams {
  keyword?: string
  entityType?: string
  page: number
  pageSize: number
  knowledgeBaseId: string
}

export interface EntityDistribution {
  label: string
  pct: number
  count: number
  color: string
}

export interface RelationDistribution {
  label: string
  pct: number
  count: number
  color: string
}

export interface LogicRule {
  id: string
  name: string
  type: string
  condition: string
  conclusion: string
  confidence: string
  status: string
  knowledgeBaseId: string
}

export interface RuleTextSegment {
  text: string
  bold?: boolean
  color?: string
}

export interface ActionRule {
  id: string
  name: string
  status: string
  triggerIconType: string
  triggerIconBg: string
  triggerIconColor: string
  triggerLabel: string
  triggerText: RuleTextSegment[]
  actionIconType: string
  actionIconBg: string
  actionIconColor: string
  actionLabel: string
  actionText: RuleTextSegment[]
  knowledgeBaseId: string
}

export interface DomainKnowledgeResultStats {
  entityCount: number
  relationCount: number
  compileVersionCount: number
  sourceFileCount: number
}

export interface GraphSummary {
  entityTypeCount: number
  relationTotalCount: number
  relationTypeCount: number
  avgDegree: number
}

// ─── Manual Datasource Types ────────────────────────────

export interface ManualDocItem {
  id: string
  name: string
  type: string
  size: string
  uploader: string
  uploadTime: string
  status: string
  knowledgeBaseId: string
}

export interface ManualDocListParams {
  knowledgeBaseId: string
  page: number
  pageSize: number
  keyword?: string
  status?: string
}

// ─── Backend parse-result types (snake_case) ──────────────

export interface BackendParseResultSummary {
  knowledge_base_id: string
  tenant_id: string
  source: string
  scope_mode: string
  scope_warning?: string
  status: string
  documents_count: number
  processed_documents_count: number
  failed_documents_count: number
  chunks_count: number
  entities_count: number
  relationships_count: number
  compile_versions_count: number
  last_updated_at: string | null
  storage_files: Record<string, boolean>
}

export interface BackendEntityItem {
  id: string
  name: string
  type: string
  description: string
  source_id: string
  file_path: string
  created_at: number | null
  relations_count: number
}

export interface BackendGraphSummary {
  nodes_count: number
  edges_count: number
  entity_type_count: number
  relation_type_count: number
  avg_degree: number
  entity_type_distribution: { label: string; count: number; pct: number }[]
  relation_distribution: { label: string; count: number; pct: number }[]
}

export interface BackendPaginatedResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  scope_mode?: string
  scope_warning?: string
}
