import apiClient from './client'
import i18n from '@/locales/i18n'

interface ApiEnvelope<T> { success: boolean; code?: number; message?: string; data?: T }

export interface SystemConfigItem {
  id: number; config_group: string; config_key: string
  config_value: string | null; value_type: string; description: string | null
}

function unwrap<T>(p: ApiEnvelope<T>): T { if (!p?.success) throw new Error(p?.message || i18n.t('common.loadFailed')); return p.data as T }

export async function listSystemConfigs(): Promise<{ items: SystemConfigItem[] }> {
  const r = await apiClient.get<ApiEnvelope<{ items: SystemConfigItem[] }>>('/api/v1/platform/system-configs')
  return unwrap(r.data)
}

export async function updateSystemConfig(key: string, value: string): Promise<SystemConfigItem> {
  const r = await apiClient.put<ApiEnvelope<SystemConfigItem>>(`/api/v1/platform/system-configs/${key}`, { config_value: value })
  return unwrap(r.data)
}