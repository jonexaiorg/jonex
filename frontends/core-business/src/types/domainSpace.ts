export interface DomainSpace {
  id: string
  name: string
  description: string | null
  owner_id: string | null
  status: 'active' | 'inactive' | 'disabled'
  knowledge_base_count: number
  service_count: number
  created_at: string | null
  updated_at: string | null
}


export interface SpacePermission {
  id: string
  user_id: string
  role: 'viewer' | 'manager'
  created_at: string | null
}


export interface SpaceMember {
  id: string
  name: string
  avatar: string
  department: string
  avatarColor: string
  role: 'viewer' | 'manager'
}

export interface DomainSpaceListParams {
  offset?: number
  limit?: number
  keyword?: string
}

export interface DomainSpaceListResult {
  items: DomainSpace[]
  total: number
  offset: number
  limit: number
}

export interface DomainSpaceFormData {
  name: string
  description?: string
  owner_id?: string
  status?: 'active' | 'inactive' | 'disabled'
}

export const SPACE_STATUS_MAP: Record<string, { tKey: string; color: string }> = {
  active: { tKey: 'status.active', color: 'green' },
  inactive: { tKey: 'status.maintenance', color: 'orange' },
  disabled: { tKey: 'status.disabled', color: 'red' },
}
