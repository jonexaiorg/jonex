import apiClient from './client';

interface ApiEnvelope<T> {
  success: boolean;
  code?: number;
  message?: string;
  data?: T;
}

export interface AuditLogItem {
  id: number;
  tenant_id: string;
  user_id: number | null;
  username: string | null;
  ip: string | null;
  action: string;
  resource: string | null;
  resource_label: string | null;
  resource_id: string | null;
  status_code: number | null;
  duration_ms: number | null;
  detail: string | null;
  trace_id: string | null;
  created_at: string | null;
}

export interface AuditLogListResponse {
  total: number;
  items: AuditLogItem[];
}

export interface AuditActionOption {
  action: string;
  label_zh: string;
  label_en: string;
}

function unwrap<T>(p: ApiEnvelope<T>): T {
  if (!p?.success) throw new Error(p?.message || 'Request failed');
  return p.data as T;
}

export async function listAuditLogs(
  params: {
    page?: number;
    page_size?: number;
    user_id?: number;
    action?: string;
    resource?: string;
    keyword?: string;
    start_time?: string;
    end_time?: string;
  } = {},
): Promise<AuditLogListResponse> {
  const r = await apiClient.get<ApiEnvelope<AuditLogListResponse>>('/api/v1/platform/audit-logs', { params });
  return unwrap(r.data);
}

export async function getAuditLog(id: number): Promise<AuditLogItem> {
  const r = await apiClient.get<ApiEnvelope<AuditLogItem>>(`/api/v1/platform/audit-logs/${id}`);
  return unwrap(r.data);
}

export async function listAuditActions(): Promise<AuditActionOption[]> {
  const r = await apiClient.get<ApiEnvelope<{ actions: AuditActionOption[] }>>('/api/v1/platform/audit-logs/actions');
  const data = unwrap(r.data);
  return data?.actions ?? [];
}

export interface AuditResourceType {
  resource: string;
  label_zh: string;
  label_en: string;
}

export async function listAuditResourceTypes(): Promise<AuditResourceType[]> {
  const r = await apiClient.get<ApiEnvelope<{ resources: AuditResourceType[] }>>(
    '/api/v1/platform/audit-logs/resource-types',
  );
  const data = unwrap(r.data);
  return data?.resources ?? [];
}

/** 根据当前 locale 获取操作类型显示名 */
export function getActionLabelByLocale(action: string, labelZh: string, labelEn: string, locale: string): string {
  return locale?.startsWith('zh') ? labelZh : labelEn;
}
