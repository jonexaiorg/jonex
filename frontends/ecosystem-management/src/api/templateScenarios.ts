import i18next from '@/locales/i18n'
import apiClient from './client'

interface ApiEnvelope<T> {
  success: boolean
  code?: number
  message?: string
  data?: T
}

export interface TemplateListResponse<T> {
  items: T[]
  total: number
  offset?: number
  limit?: number
}

export interface TemplateDomain {
  id: string
  name: string
  description?: string | null
  status: 'active' | 'inactive' | 'archived' | string
  scenario_count?: number
  created_at?: string | null
  updated_at?: string | null
}

export interface TemplateScenario {
  id: string
  domain_id: string
  name: string
  description?: string | null
  config_json?: Record<string, unknown>
  created_at?: string | null
  updated_at?: string | null
}

export interface TemplateAttribute {
  id: string
  template_object_id?: string
  attr_name: string
  description?: string | null
  attr_type: string
  is_primary_key: number | boolean
  sort_order?: number
}

export interface TemplateObject {
  id: string
  domain_id: string
  scenario_id: string
  name: string
  description?: string | null
  status?: string
  created_at?: string | null
  updated_at?: string | null
  attributes: TemplateAttribute[]
}

export interface TemplateRelation {
  id: string
  domain_id: string
  scenario_id: string
  name: string
  description?: string | null
  source_object_id: string
  target_object_id: string
  source_object_name?: string | null
  target_object_name?: string | null
  relation_type: string
  status?: string
  created_at?: string | null
  updated_at?: string | null
}

export interface SaveTemplateScenarioPayload {
  name: string
  description?: string
  domain_id: string
}

export interface SaveTemplateObjectPayload {
  name: string
  description?: string
  attributes: Array<{
    attr_name: string
    description?: string
    attr_type: string
    is_primary_key: boolean
    sort_order?: number
  }>
}

export interface SaveTemplateRelationPayload {
  source_object_id: string
  target_object_id: string
  name: string
  description?: string
  relation_type: string
}

function unwrapEnvelope<T>(payload: ApiEnvelope<T>): T {
  if (!payload?.success) {
    throw new Error(payload?.message || i18next.t('common.loadFailed'))
  }
  return payload.data as T
}

export async function fetchTemplateDomains(
  offset = 0,
  limit = 20,
): Promise<TemplateListResponse<TemplateDomain>> {
  const resp = await apiClient.get<ApiEnvelope<TemplateListResponse<TemplateDomain>>>(
    '/api/v1/ecosystem/templates/domains',
    { params: { offset, limit } },
  )
  return unwrapEnvelope(resp.data)
}

export async function fetchTemplateScenarios(domainId?: string): Promise<TemplateListResponse<TemplateScenario>> {
  const resp = await apiClient.get<ApiEnvelope<TemplateListResponse<TemplateScenario>>>(
    '/api/v1/ecosystem/templates/scenarios',
    { params: { domain_id: domainId || undefined, limit: 100 } },
  )
  return unwrapEnvelope(resp.data)
}

export async function createTemplateScenario(data: SaveTemplateScenarioPayload): Promise<TemplateScenario> {
  const resp = await apiClient.post<ApiEnvelope<TemplateScenario>>('/api/v1/ecosystem/templates/scenarios', data)
  return unwrapEnvelope(resp.data)
}

export async function updateTemplateScenario(
  scenarioId: string,
  data: Partial<SaveTemplateScenarioPayload>,
): Promise<TemplateScenario> {
  const resp = await apiClient.patch<ApiEnvelope<TemplateScenario>>(
    `/api/v1/ecosystem/templates/scenarios/${scenarioId}`,
    data,
  )
  return unwrapEnvelope(resp.data)
}

export async function deleteTemplateScenario(scenarioId: string): Promise<void> {
  const resp = await apiClient.delete<ApiEnvelope<void>>(`/api/v1/ecosystem/templates/scenarios/${scenarioId}`)
  unwrapEnvelope(resp.data)
}

export async function fetchTemplateObjects(scenarioId: string): Promise<TemplateListResponse<TemplateObject>> {
  const resp = await apiClient.get<ApiEnvelope<TemplateListResponse<TemplateObject>>>(
    `/api/v1/ecosystem/templates/scenarios/${scenarioId}/objects`,
    { params: { limit: 100 } },
  )
  return unwrapEnvelope(resp.data)
}

export async function createTemplateObject(
  scenarioId: string,
  data: SaveTemplateObjectPayload,
): Promise<TemplateObject> {
  const resp = await apiClient.post<ApiEnvelope<TemplateObject>>(
    `/api/v1/ecosystem/templates/scenarios/${scenarioId}/objects`,
    data,
  )
  return unwrapEnvelope(resp.data)
}

export async function updateTemplateObject(
  objectId: string,
  data: Partial<SaveTemplateObjectPayload>,
): Promise<TemplateObject> {
  const resp = await apiClient.patch<ApiEnvelope<TemplateObject>>(
    `/api/v1/ecosystem/templates/objects/${objectId}`,
    data,
  )
  return unwrapEnvelope(resp.data)
}

export async function deleteTemplateObject(objectId: string): Promise<void> {
  const resp = await apiClient.delete<ApiEnvelope<void>>(`/api/v1/ecosystem/templates/objects/${objectId}`)
  unwrapEnvelope(resp.data)
}

export async function fetchTemplateRelations(scenarioId: string): Promise<TemplateListResponse<TemplateRelation>> {
  const resp = await apiClient.get<ApiEnvelope<TemplateListResponse<TemplateRelation>>>(
    `/api/v1/ecosystem/templates/scenarios/${scenarioId}/relations`,
    { params: { limit: 100 } },
  )
  return unwrapEnvelope(resp.data)
}

export async function createTemplateRelation(
  scenarioId: string,
  data: SaveTemplateRelationPayload,
): Promise<TemplateRelation> {
  const resp = await apiClient.post<ApiEnvelope<TemplateRelation>>(
    `/api/v1/ecosystem/templates/scenarios/${scenarioId}/relations`,
    data,
  )
  return unwrapEnvelope(resp.data)
}

export async function updateTemplateRelation(
  relationId: string,
  data: Partial<SaveTemplateRelationPayload>,
): Promise<TemplateRelation> {
  const resp = await apiClient.patch<ApiEnvelope<TemplateRelation>>(
    `/api/v1/ecosystem/templates/relations/${relationId}`,
    data,
  )
  return unwrapEnvelope(resp.data)
}

export async function deleteTemplateRelation(relationId: string): Promise<void> {
  const resp = await apiClient.delete<ApiEnvelope<void>>(`/api/v1/ecosystem/templates/relations/${relationId}`)
  unwrapEnvelope(resp.data)
}



export interface TemplateConstraint {
  id: string
  scenario_id: string
  name: string
  target_type: 'object' | 'attribute' | 'relation'
  target_id: string
  target_label: string
  constraint_type: 'unique' | 'exists' | 'conditional' | 'range'
  expression?: string | null
  suggestion?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface SaveTemplateConstraintPayload {
  name: string
  target_type: string
  target_id: string
  constraint_type: string
  expression?: string
  suggestion?: string
}

export async function fetchTemplateConstraints(
  scenarioId: string,
): Promise<TemplateListResponse<TemplateConstraint>> {
  const resp = await apiClient.get<ApiEnvelope<TemplateListResponse<TemplateConstraint>>>(
    `/api/v1/ecosystem/templates/scenarios/${scenarioId}/constraints`,
    { params: { limit: 100 } },
  )
  return unwrapEnvelope(resp.data)
}

export async function createTemplateConstraint(
  scenarioId: string,
  data: SaveTemplateConstraintPayload,
): Promise<TemplateConstraint> {
  const resp = await apiClient.post<ApiEnvelope<TemplateConstraint>>(
    `/api/v1/ecosystem/templates/scenarios/${scenarioId}/constraints`,
    data,
  )
  return unwrapEnvelope(resp.data)
}

export async function updateTemplateConstraint(
  constraintId: string,
  data: Partial<SaveTemplateConstraintPayload>,
): Promise<TemplateConstraint> {
  const resp = await apiClient.patch<ApiEnvelope<TemplateConstraint>>(
    `/api/v1/ecosystem/templates/constraints/${constraintId}`,
    data,
  )
  return unwrapEnvelope(resp.data)
}

export async function deleteTemplateConstraint(constraintId: string): Promise<void> {
  const resp = await apiClient.delete<ApiEnvelope<void>>(
    `/api/v1/ecosystem/templates/constraints/${constraintId}`,
  )
  unwrapEnvelope(resp.data)
}
