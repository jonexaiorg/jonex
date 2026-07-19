import i18next from '@/locales/i18n'
import apiClient from './client'

interface ApiEnvelope<T> {
  success: boolean
  code?: number
  message?: string
  data?: T
}

export interface SkillListResponse {
  items: SkillItem[]
  total: number
  offset?: number
  limit?: number
}

export interface SkillItem {
  id: string
  name: string
  description: string | null
  category: string
  icon?: string | null
  status: 'published' | 'disabled'
  enabled: boolean
  tenant_status: 'enabled' | 'disabled'
  tool_name: string
  instruction: string
  input_schema: Record<string, unknown>
  output_schema: Record<string, unknown>
  tags: string[]
  capability?: Record<string, unknown>
}

export interface FetchSkillsParams {
  offset?: number
  limit?: number
  category?: string
  keyword?: string
}

export interface SkillToggleResponse {
  id: string
  skill_id: string
  tenant_status: 'enabled' | 'disabled'
  enabled: boolean
}

function unwrapEnvelope<T>(payload: ApiEnvelope<T>): T {
  if (!payload?.success) {
    throw new Error(payload?.message || i18next.t('common.loadFailed'))
  }
  return payload.data as T
}

export async function fetchSkills(
  params: FetchSkillsParams = {},
): Promise<SkillListResponse> {
  const resp = await apiClient.get<ApiEnvelope<SkillListResponse>>(
    '/api/v1/ecosystem/skills',
    {
      params: {
        offset: params.offset ?? 0,
        limit: params.limit ?? 20,
        category: params.category,
        keyword: params.keyword,
      },
    },
  )
  return unwrapEnvelope(resp.data)
}

export async function fetchSkill(skillId: string): Promise<SkillItem> {
  const resp = await apiClient.get<ApiEnvelope<SkillItem>>(
    `/api/v1/ecosystem/skills/${skillId}`,
  )
  return unwrapEnvelope(resp.data)
}

export async function enableSkill(
  skillId: string,
): Promise<SkillToggleResponse> {
  const resp = await apiClient.post<ApiEnvelope<SkillToggleResponse>>(
    `/api/v1/ecosystem/skills/${skillId}/enable`,
  )
  return unwrapEnvelope(resp.data)
}

export async function disableSkill(
  skillId: string,
): Promise<SkillToggleResponse> {
  const resp = await apiClient.post<ApiEnvelope<SkillToggleResponse>>(
    `/api/v1/ecosystem/skills/${skillId}/disable`,
  )
  return unwrapEnvelope(resp.data)
}