export interface DomainSpace {
  id: string;
  name: string;
  description: string | null;
  owner_id: string | null;
  status: 'active' | 'inactive' | 'disabled';
  knowledge_base_count: number;
  service_count: number;
  created_at: string | null;
  updated_at: string | null;
}

/** 空间权限记录（对应后端 space_permissions 表） */
export interface SpacePermission {
  id: string;
  user_id: string;
  role: 'viewer' | 'manager';
  created_at: string | null;
}

/** 空间成员 UI 展示模型 */
export interface SpaceMember {
  id: string;
  name: string;
  avatar: string;
  department: string;
  avatarColor: string;
  role: 'viewer' | 'manager';
}

export interface DomainSpaceListParams {
  offset?: number;
  limit?: number;
  keyword?: string;
}

export interface DomainSpaceListResult {
  items: DomainSpace[];
  total: number;
  offset: number;
  limit: number;
}

export interface DomainSpaceFormData {
  name: string;
  description?: string;
  owner_id?: string;
  status?: 'active' | 'inactive' | 'disabled';
}

export function getSpaceStatusMap(t: (key: string) => string): Record<string, { label: string; color: string }> {
  return {
    active: { label: t('status.active'), color: 'green' },
    inactive: { label: t('domainSpace.maintenanceStatus'), color: 'orange' },
    disabled: { label: t('status.disabled'), color: 'red' },
  };
}
