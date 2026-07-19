import i18next from '@/locales/i18n'
import apiClient from './client'

interface ApiEnvelope<T> {
  success: boolean
  code?: number
  message?: string
  data?: T
}

export interface AdapterListResponse {
  items: AdapterItem[]
  total: number
  offset?: number
  limit?: number
}

export interface AdapterItem {
  id: string
  tenant_id: string
  name: string
  adapter_type: string
  config_json: Record<string, unknown>
  status: string
  created_at: string | null
  updated_at: string | null
}

export interface SaveAdapterPayload {
  name: string
  adapter_type: string
  config_json?: Record<string, unknown>
}

const ADAPTER_TYPE_LABELS: Record<string, string> = {
  dingtalk: 'adapter.platforms.dingtalk',
  wechat_work: 'adapter.platforms.wechat_work',
  feishu: 'adapter.platforms.feishu',
}

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  connected: { label: 'adapter.connected', color: 'green' },
  disconnected: { label: 'adapter.disconnected', color: 'default' },
  error: { label: 'adapter.error', color: 'red' },
}

export function getAdapterTypeLabel(type: string): string {
  return ADAPTER_TYPE_LABELS[type] || type
}

export function getAdapterStatusLabel(status: string): { label: string; color: string } {
  return STATUS_LABELS[status] || { label: status, color: 'default' }
}

export const ADAPTER_TYPE_OPTIONS: string[] = ['dingtalk', 'wechat_work', 'feishu']

function unwrapEnvelope<T>(payload: ApiEnvelope<T>): T {
  if (!payload?.success) {
    throw new Error(payload?.message || i18next.t('common.loadFailed'))
  }
  return payload.data as T
}

export async function listAdapters(
  offset = 0,
  limit = 100,
): Promise<AdapterListResponse> {
  const resp = await apiClient.get<ApiEnvelope<AdapterListResponse>>(
    '/api/v1/ecosystem/adapters',
    { params: { offset, limit } },
  )
  return unwrapEnvelope(resp.data)
}

export async function createAdapter(data: SaveAdapterPayload): Promise<AdapterItem> {
  const resp = await apiClient.post<ApiEnvelope<AdapterItem>>(
    '/api/v1/ecosystem/adapters',
    data,
  )
  return unwrapEnvelope(resp.data)
}

export async function updateAdapter(
  id: string,
  data: Partial<SaveAdapterPayload & { status: string }>,
): Promise<AdapterItem> {
  const resp = await apiClient.patch<ApiEnvelope<AdapterItem>>(
    `/api/v1/ecosystem/adapters/${id}`,
    data,
  )
  return unwrapEnvelope(resp.data)
}

export async function connectAdapter(id: string): Promise<AdapterItem> {
  const resp = await apiClient.post<ApiEnvelope<AdapterItem>>(
    `/api/v1/ecosystem/adapters/${id}/connect`,
  )
  return unwrapEnvelope(resp.data)
}

export async function disconnectAdapter(id: string): Promise<AdapterItem> {
  const resp = await apiClient.post<ApiEnvelope<AdapterItem>>(
    `/api/v1/ecosystem/adapters/${id}/disconnect`,
  )
  return unwrapEnvelope(resp.data)
}