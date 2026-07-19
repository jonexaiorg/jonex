import apiClient from './client'
import i18n from '@/locales/i18n'

interface ApiEnvelope<T> {
  success: boolean; code?: number; message?: string; data?: T
}

export interface UserItem {
  id: number; tenant_id: string; username: string; display_name: string | null
  email: string | null; role: string; status: number
  last_login_at: string | null; created_at: string | null; updated_at: string | null
}

export interface UserListResponse { items: UserItem[]; total: number }

export interface UserCreatePayload { username: string; password: string; display_name?: string; email?: string; role?: string }
export interface UserUpdatePayload { display_name?: string; email?: string; role?: string; status?: number }

function unwrap<T>(p: ApiEnvelope<T>): T {
  if (!p?.success) throw new Error(p?.message || i18n.t('common.loadFailed'))
  return p.data as T
}

export async function listAllUsers(): Promise<UserListResponse> {
  const r = await apiClient.get<ApiEnvelope<UserListResponse>>('/api/v1/platform/users/all')
  return unwrap(r.data)
}

export async function listUsers(page = 1, pageSize = 100): Promise<UserListResponse> {
  const r = await apiClient.get<ApiEnvelope<UserListResponse>>('/api/v1/platform/users', { params: { page, page_size: pageSize } })
  return unwrap(r.data)
}

export async function createUser(data: UserCreatePayload): Promise<UserItem> {
  const r = await apiClient.post<ApiEnvelope<UserItem>>('/api/v1/platform/users', data)
  return unwrap(r.data)
}

export async function updateUser(id: number, data: UserUpdatePayload): Promise<UserItem> {
  const r = await apiClient.patch<ApiEnvelope<UserItem>>(`/api/v1/platform/users/${id}`, data)
  return unwrap(r.data)
}

export async function deleteUser(id: number): Promise<void> {
  await apiClient.delete(`/api/v1/platform/users/${id}`)
}

export function getRoleLabel(role: string): string {
  const m: Record<string, string> = { admin: 'userManagement.admin', user: 'userManagement.user' }
  return m[role] || role
}

export function getUserStatus(s: number): { label: string; color: string } {
  return s === 1 ? { label: 'status.enabled', color: 'success' } : { label: 'status.disabled', color: 'error' }
}