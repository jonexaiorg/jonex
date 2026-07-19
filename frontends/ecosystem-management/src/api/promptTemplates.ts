import i18next from '@/locales/i18n'
import apiClient from './client'



export interface VersionItem {
  version: string
  content: string
  updated_by?: string
  updated_at?: string
  remark?: string
}

export interface PromptTemplateItem {
  id: string
  tenant_id: string | null
  name: string
  category: string
  scope: 'system' | 'domain'
  description?: string
  status: string
  current_version: string
  versions_json: VersionItem[]
  created_by?: string
  created_at: string | null
  updated_at: string | null
}

export interface PromptTemplateDetail extends PromptTemplateItem {
  versions: VersionItem[]
  current_content?: string
}

export interface PromptTemplateListResponse {
  items: PromptTemplateItem[]
  total: number
  offset: number
  limit: number
}

export interface VersionListResponse {
  items: VersionItem[]
  current_version: string
}

export interface CreatePromptTemplatePayload {
  name: string
  category: string
  description?: string
  content: string
  status?: string
}

export interface UpdatePromptTemplatePayload {
  name?: string
  category?: string
  description?: string
  content?: string
  status?: string
  version_remark?: string
  target_version?: string
}



export const PROMPT_CATEGORIES = [
  'promptTemplate.categories.general', 'promptTemplate.categories.document', 'promptTemplate.categories.finance',
  'promptTemplate.categories.contract', 'promptTemplate.categories.data', 'promptTemplate.categories.other',
] as const

export const CATEGORY_ICON_MAP: Record<string, { icon: string; bg: string }> = {
  'promptTemplate.categories.general': { icon: '💬', bg: 'linear-gradient(135deg, #3b82f6, #1d4ed8)' },
  'promptTemplate.categories.document': { icon: '📄', bg: 'linear-gradient(135deg, #f97316, #ea580c)' },
  'promptTemplate.categories.finance': { icon: '📈', bg: 'linear-gradient(135deg, #10b981, #059669)' },
  'promptTemplate.categories.contract': { icon: '⚖️', bg: 'linear-gradient(135deg, #8b5cf6, #7c3aed)' },
  'promptTemplate.categories.data': { icon: '🗄️', bg: 'linear-gradient(135deg, #06b6d4, #0891b2)' },
  'promptTemplate.categories.other': { icon: '📋', bg: 'linear-gradient(135deg, #64748b, #475569)' },
}



interface ApiEnvelope<T> {
  success: boolean
  code?: number
  message?: string
  data?: T
}

function unwrap<T>(payload: ApiEnvelope<T>): T {
  if (!payload?.success) {
    throw new Error(payload?.message || i18next.t('common.loadFailed'))
  }
  return payload.data as T
}



export async function listPromptTemplates(params: {
  scope?: string
  category?: string
  keyword?: string
  offset?: number
  limit?: number
}): Promise<PromptTemplateListResponse> {
  const resp = await apiClient.get<ApiEnvelope<PromptTemplateListResponse>>(
    '/api/v1/ecosystem/prompt-templates',
    { params },
  )
  return unwrap(resp.data)
}

export async function getPromptTemplate(id: string): Promise<PromptTemplateDetail> {
  const resp = await apiClient.get<ApiEnvelope<PromptTemplateDetail>>(
    `/api/v1/ecosystem/prompt-templates/${id}`,
  )
  return unwrap(resp.data)
}

export async function createPromptTemplate(
  data: CreatePromptTemplatePayload,
): Promise<PromptTemplateItem> {
  const resp = await apiClient.post<ApiEnvelope<PromptTemplateItem>>(
    '/api/v1/ecosystem/prompt-templates',
    data,
  )
  return unwrap(resp.data)
}

export async function updatePromptTemplate(
  id: string,
  data: UpdatePromptTemplatePayload,
): Promise<PromptTemplateItem> {
  const resp = await apiClient.patch<ApiEnvelope<PromptTemplateItem>>(
    `/api/v1/ecosystem/prompt-templates/${id}`,
    data,
  )
  return unwrap(resp.data)
}

export async function deletePromptTemplate(id: string): Promise<void> {
  const resp = await apiClient.delete<ApiEnvelope<null>>(
    `/api/v1/ecosystem/prompt-templates/${id}`,
  )
  unwrap(resp.data)
}

export async function copyPromptTemplate(id: string): Promise<PromptTemplateItem> {
  const resp = await apiClient.post<ApiEnvelope<PromptTemplateItem>>(
    `/api/v1/ecosystem/prompt-templates/${id}/copy`,
  )
  return unwrap(resp.data)
}

export async function listVersions(id: string): Promise<VersionListResponse> {
  const resp = await apiClient.get<ApiEnvelope<VersionListResponse>>(
    `/api/v1/ecosystem/prompt-templates/${id}/versions`,
  )
  return unwrap(resp.data)
}

export async function rollbackVersion(
  id: string,
  targetVersion: string,
): Promise<PromptTemplateItem> {
  const resp = await apiClient.post<ApiEnvelope<PromptTemplateItem>>(
    `/api/v1/ecosystem/prompt-templates/${id}/versions/rollback`,
    { target_version: targetVersion },
  )
  return unwrap(resp.data)
}
