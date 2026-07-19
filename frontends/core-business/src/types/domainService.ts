

export interface DomainServiceItem {
  id: string
  name: string
  description: string | null
  space_id: string

  space_name?: string
  domain_type: string | null
  status: string
  api_key_encrypted: string | null

  kb_ids: string[]

  kb_names?: string[]
  created_at: string | null
  updated_at: string | null
}

export interface DomainServiceListResult {
  items: DomainServiceItem[]
  total: number
  offset: number
  limit: number
}

export interface DomainServiceFormData {
  name: string
  space_id: string
  description?: string

  kb_ids?: string[]
  status?: string
}

export interface DomainServiceStatusOption {
  value: string
  label: string
  color: string
}

export const SERVICE_STATUS_MAP: Record<string, DomainServiceStatusOption> = {
  active: { value: 'active', label: 'status.active', color: '#059669' },
  inactive: { value: 'inactive', label: 'status.inactive', color: '#dc2626' },
  testing: { value: 'testing', label: 'status.testing', color: '#d97706' },
}


export interface KnowledgeBaseOption {
  id: string
  name: string
}


export interface PermMember {

  id: string

  name: string

  department: string
  avatar: string
  avatarColor: string
  role: 'viewer' | 'manager'
}


export function userNameToColor(name: string): string {
  const colors = ['#3b82f6', '#10b981', '#8b5cf6', '#f97316', '#ec4899', '#06b6d4', '#84cc16', '#f43f5e']
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  return colors[Math.abs(hash) % colors.length]
}


export function userToPermMember(
  user: { id: number | string; username: string; display_name?: string | null; role?: string },
  permRole: 'viewer' | 'manager' = 'viewer',
): PermMember {
  const name = (user.display_name || user.username || String(user.id)).trim()
  return {
    id: String(user.id),
    name,
    department: user.role || '',
    avatar: name.charAt(0).toUpperCase(),
    avatarColor: userNameToColor(name),
    role: permRole,
  }
}


export interface ServiceApiKeyItem {
  id: string
  service_id: string
  key_prefix: string
  key_encrypted: string
  expires_at: string | null
  is_active: boolean
  created_at: string | null
}


export const MOCK_KNOWLEDGE_BASES: KnowledgeBaseOption[] = [
  { id: 'kb-finance', name: '金融产品知识库' },
  { id: 'kb-medical', name: '医学文献知识库' },
  { id: 'kb-manufacturing', name: '设备故障知识库' },
  { id: 'kb-education', name: '课程资源知识库' },
  { id: 'kb-legal', name: '法律法规知识库' },
  { id: 'kb-customer', name: '客户服务知识库' },
  { id: 'kb-compliance', name: '合规文书知识库' },
  { id: 'kb-quality', name: '质量检测知识库' },
]
