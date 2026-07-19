import apiClient from './client'
import i18n from '@/locales/i18n'

interface ApiEnvelope<T> { success: boolean; code?: number; message?: string; data?: T }

export interface AuditLogItem {
  id: number; tenant_id: string; user_id: number | null; username: string | null
  ip: string | null; action: string; resource: string | null; resource_id: string | null
  status_code: number | null; duration_ms: number | null
  detail: string | null; trace_id: string | null
  created_at: string | null
}

export interface AuditLogListResponse { total: number; items: AuditLogItem[] }

function unwrap<T>(p: ApiEnvelope<T>): T { if (!p?.success) throw new Error(p?.message || i18n.t('common.loadFailed')); return p.data as T }

export async function listAuditLogs(params: {
  page?: number; page_size?: number; user_id?: number; action?: string
  start_time?: string; end_time?: string
} = {}): Promise<AuditLogListResponse> {
  const r = await apiClient.get<ApiEnvelope<AuditLogListResponse>>('/api/v1/platform/audit-logs', { params })
  return unwrap(r.data)
}

export async function getAuditLog(id: number): Promise<AuditLogItem> {
  const r = await apiClient.get<ApiEnvelope<AuditLogItem>>(`/api/v1/platform/audit-logs/${id}`)
  return unwrap(r.data)
}

export function getActionLabel(action: string): string {
  const m: Record<string, string> = {
    create: 'operationLog.create', update: 'operationLog.update', delete: 'operationLog.delete',
    login: 'operationLog.login', logout: 'operationLog.logout', search: 'operationLog.search', upload: 'operationLog.upload',
    connect: 'operationLog.connect', disconnect: 'operationLog.disconnect',
  }
  return m[action] || action
}