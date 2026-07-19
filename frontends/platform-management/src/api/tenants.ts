import apiClient from './client'
import i18n from '@/locales/i18n'

interface ApiEnvelope<T> {
  success: boolean
  code?: number
  message?: string
  data?: T
}

export interface TenantListResponse {
  items: TenantItem[]
  total: number
}

export interface TenantItem {
  id: string
  name: string
  description: string | null
  status: number
  plan_type: string
  expire_time: string | null
  created_at: string | null
  updated_at: string | null
}

export interface TenantCreatePayload {
  id: string
  name: string
  description?: string
  plan_type?: string
}

export interface TenantUpdatePayload {
  name?: string
  description?: string
  plan_type?: string
  status?: number
}

function unwrapEnvelope<T>(payload: ApiEnvelope<T>): T {
  if (!payload?.success) throw new Error(payload?.message || i18n.t('common.loadFailed'))
  return payload.data as T
}

export async function listTenants(page = 1, pageSize = 100): Promise<TenantListResponse> {
  const resp = await apiClient.get<ApiEnvelope<TenantListResponse>>('/api/v1/platform/tenants', { params: { page, page_size: pageSize } })
  return unwrapEnvelope(resp.data)
}

export async function createTenant(data: TenantCreatePayload): Promise<TenantItem> {
  const resp = await apiClient.post<ApiEnvelope<TenantItem>>('/api/v1/platform/tenants', data)
  return unwrapEnvelope(resp.data)
}

export async function updateTenant(id: string, data: TenantUpdatePayload): Promise<TenantItem> {
  const resp = await apiClient.patch<ApiEnvelope<TenantItem>>(`/api/v1/platform/tenants/${id}`, data)
  return unwrapEnvelope(resp.data)
}

export async function deleteTenant(id: string): Promise<void> {
  await apiClient.delete<ApiEnvelope<null>>(`/api/v1/platform/tenants/${id}`)
}

export async function getTenantUserCounts(): Promise<Record<string, number>> {
  const r = await apiClient.get<ApiEnvelope<Record<string, number>>>('/api/v1/platform/tenants/user-counts')
  return unwrapEnvelope(r.data) as Record<string, number>
}

export function getPlanTypeLabel(plan: string): string {
  const labels: Record<string, string> = { free: 'tenantManagement.free', pro: 'tenantManagement.pro', enterprise: 'tenantManagement.enterprise' }
  return labels[plan] || plan
}

export function getStatusLabel(status: number): { label: string; color: string } {
  return status === 1 ? { label: 'status.enabled', color: 'success' } : { label: 'status.disabled', color: 'warning' }
}