export type DomainKnowledgeStatus = 'synced' | 'syncing' | 'failed' | 'disabled'

export type DomainKnowledgeSourceType =
  | 'api'
  | 'api_push'
  | 'storage'
  | 'file'

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
  synced: 'status.synced',
  syncing: 'status.syncing',
  failed: 'status.failed',
  disabled: 'status.inactive',
}

export const statusColorMap: Record<DomainKnowledgeStatus, string> = {
  synced: 'success',
  syncing: 'processing',
  failed: 'error',
  disabled: 'default',
}



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

  ontologyDegraded?: boolean
}

export type DataSourceDisplayStatus = 'running' | 'paused' | 'error'

export interface DataSourceConfig {
  id: string
  name: string
  type: string
  accessType: string
  configJson: Record<string, any>
  docs: number
  status: DataSourceDisplayStatus
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




export interface OntologyStatistics {
  knowledge_base_id: string
  knowledge_base_name: string

  last_update_time?: string | null
  source_file_count: number
  ontology_instance_count: number
  ontology_relation_count: number

  ontology_degraded?: boolean
}


export interface OntologyInstanceSummary {
  name: string
  display_name: string
  description: string
  status: string
  build_status: string
  instance_count: number
  attributes: Array<{ name: string; display_name: string; type: string; description?: string }>
}


export interface RelationInstanceSummary {
  name: string
  display_name: string
  description: string
  source: string
  target: string
  source_display_name: string
  target_display_name: string
  cardinality: string
  status: string
  build_status: string
  instance_count: number
}


export interface OntologyInstanceRow {
  name: string
  type: string
  aliases: string[]
  attributes: Record<string, unknown> | null
  description: string
  confidence: number | null
  doc_ids: string[]
}


export interface OntologyInstanceListParams {
  kbId: string
  entityType?: string
  keyword?: string
  page: number
  pageSize: number
}


export interface RelationInstanceRow {
  source: string
  source_type: string
  relation_type: string
  target: string
  target_type: string
  attributes: Record<string, unknown> | null
  confidence: number | null
}


export interface RelationInstanceListParams {
  kbId: string
  relationType?: string
  sourceName?: string
  targetName?: string
  sourceType?: string
  targetType?: string
  keyword?: string
  page: number
  pageSize: number
}


export interface OntologyGraphNode {
  id: string
  name: string
  type: string
  aliases: string[]
  attributes: Record<string, unknown> | null
  description: string
  confidence: number | null
  doc_ids: string[]
}


export interface OntologyGraphEdge {
  source: string
  source_type: string
  target: string
  target_type: string
  label: string
  confidence: number | null
}


export interface OntologyGraphData {
  nodes: OntologyGraphNode[]
  edges: OntologyGraphEdge[]

  total_nodes: number

  total_relations: number

  type_counts: Record<string, number>

  returned_nodes: number

  returned_edges: number

  truncated: boolean

  limit: number

  degraded?: boolean

  degraded_reason?: string
}


export interface OntologyGraphParams {
  limit?: number

  entityTypes?: string[]
}


export interface OntologyNeighborData {
  nodes: OntologyGraphNode[]
  edges: OntologyGraphEdge[]

  degraded?: boolean

  degraded_reason?: string
}

export interface GraphSummary {
  entityTypeCount: number
  relationTotalCount: number
  relationTypeCount: number
  avgDegree: number
}



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

export type CompiledAttrType = 'string' | 'text' | 'number' | 'date' | 'enum' | 'boolean'
export type CompiledRelationCardinality = 'one_to_one' | 'one_to_many' | 'many_to_one' | 'many_to_many' | 'custom'
export type SchemaMode = 'template_seeded' | 'manual_edited'
export type SchemaSyncStatus = 'synced' | 'outdated'

export interface CompiledSchemaAttribute {
  name: string
  display_name: string
  description?: string
  type: CompiledAttrType
  required: boolean
  is_primary_key?: boolean
  source_attribute_id?: string | null
}

export interface CompiledSchemaEntityType {
  name: string
  display_name: string
  description?: string
  requirement?: string
  status?: 'active' | 'inactive'
  aliases: string[]
  source_object_id?: string | null
  attributes: CompiledSchemaAttribute[]
}

export interface CompiledSchemaRelationType {
  name: string
  display_name: string
  description?: string
  status?: 'active' | 'inactive'
  aliases: string[]
  source: string
  target: string
  source_relation_id?: string | null
  cardinality: CompiledRelationCardinality
}

export interface CompiledSchema {
  id?: number
  tenant_id?: string
  knowledge_base_id?: string
  template_domain_id?: string | null
  template_scenario_id?: string | null
  source_type?: string
  source_version: number
  source_hash?: string | null
  schema_version: number
  entity_types: CompiledSchemaEntityType[]
  relation_types: CompiledSchemaRelationType[]
  constraints: Record<string, unknown>[]
  disambiguation: Record<string, unknown>
  prompt_schema: Record<string, unknown>
  status: string
  schema_mode: SchemaMode
  sync_status: SchemaSyncStatus
  edited_at?: string | null
  edited_by?: string | null
  compiled_at?: string | null
}

export interface OntologyBinding {
  id: number
  tenant_id: string
  knowledge_base_id: string
  template_domain_id?: string | null
  template_scenario_id?: string | null
  source_type: string
  status: string
  created_at?: string | null
  updated_at?: string | null
}

export interface OntologyTemplateSummary {
  domain_id?: string | null
  domain_name?: string | null
  scenario_id?: string | null
  scenario_name?: string | null
  source_version?: number | null
  source_hash?: string | null
}

export interface OntologyEditorState {
  knowledge_base_id: string
  binding?: OntologyBinding | null
  compiled_schema?: CompiledSchema | null
  current_template?: OntologyTemplateSummary | null
}



export type OntologyDefStatus = 'active' | 'inactive'

export const ontologyStatusTextMap: Record<OntologyDefStatus, string> = {
  active: 'status.active',
  inactive: 'status.inactive',
}

export type OntologyAttrType = '字符串' | '数值' | '日期' | '枚举' | '文本' | '布尔'

export interface OntologyAttribute {
  id: string
  name: string
  description?: string
  type: OntologyAttrType
  isPrimaryKey: boolean
}

export interface OntologyObjectDef {
  id: string
  knowledgeBaseId: string
  name: string
  description: string
  attributes: OntologyAttribute[]
  requirement: string
  status: OntologyDefStatus
}

export type OntologyRelationType = '一对一' | '一对多' | '多对一' | '多对多' | '自定义'

export interface OntologyRelationDef {
  id: string
  knowledgeBaseId: string
  sourceObject: string
  name: string
  targetObject: string
  description: string
  relationType: OntologyRelationType
  status: OntologyDefStatus
}

export type CompileScope = 'single' | 'whole'
export type CompileTrigger = 'upload' | 'update'

export const compileScopeTextMap: Record<CompileScope, string> = {
  single: 'ontology.singleDoc',
  whole: 'ontology.wholeKb',
}
export const compileTriggerTextMap: Record<CompileTrigger, string> = {
  upload: 'ontology.triggerOnUpload',
  update: 'ontology.triggerOnUpdate',
}

export interface CompileStep {
  id: string
  knowledgeBaseId: string
  order: number
  name: string
  prompt: string
  skill: string
  scope: CompileScope
  trigger: CompileTrigger
  template: string
}

export interface EngineSetting {
  knowledgeBaseId: string
  semanticModel: string
}

export type SaveOntologyObjectPayload = Omit<OntologyObjectDef, 'id' | 'knowledgeBaseId'>
export type SaveOntologyRelationPayload = Omit<OntologyRelationDef, 'id' | 'knowledgeBaseId'>
export type SaveCompileStepPayload = Omit<CompileStep, 'id' | 'knowledgeBaseId'>



export type ConstraintTargetType = 'entity' | 'attribute' | 'relation'

export const constraintTargetTypeTextMap: Record<ConstraintTargetType, string> = {
  entity: 'ontology.entity',
  attribute: 'ontology.attribute',
  relation: 'ontology.relation',
}

export type ConstraintTypeCode = 'mutually_exclusive' | 'value_range' | 'unique' | 'required' | 'custom'

export const constraintTypeTextMap: Record<ConstraintTypeCode, string> = {
  mutually_exclusive: 'ontology.constraintMutuallyExclusive',
  value_range: 'ontology.constraintValueRange',
  unique: 'ontology.constraintUnique',
  required: 'ontology.constraintRequired',
  custom: 'ontology.custom',
}

export function normalizeConstraintType(value?: string | null): ConstraintTypeCode {
  const aliases: Record<string, ConstraintTypeCode> = {
    mutually_exclusive: 'mutually_exclusive',
    '互斥': 'mutually_exclusive',
    value_range: 'value_range',
    '值域要求': 'value_range',
    unique: 'unique',
    '唯一': 'unique',
    required: 'required',
    '必填': 'required',
    custom: 'custom',
    '自定义': 'custom',
  }
  return aliases[value || ''] || 'custom'
}


export interface CompiledSchemaConstraint {
  name: string
  target_type: ConstraintTargetType
  target_code: string
  target_label?: string | null
  constraint_type: ConstraintTypeCode
  expression?: string
  suggestion?: string
}


export interface OntologyConstraint {
  id: string
  name: string
  targetType: ConstraintTargetType
  targetCode: string
  targetLabel?: string
  constraintType: ConstraintTypeCode
  expression?: string
  suggestion?: string
}

export type SaveOntologyConstraintPayload = Omit<OntologyConstraint, 'id'>



export interface SynonymGroup {
  id: string
  knowledgeBaseId: string
  terms: string[]
  canonical?: string | null
  createdAt?: string | null
  updatedAt?: string | null
}

export interface SynonymListResult {
  items: SynonymGroup[]
  total: number
  page: number
  pageSize: number
}

export interface SynonymImportResult {
  created: number
  skipped: number
  failed: { index: number; reason: string }[]
}
