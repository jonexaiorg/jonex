import type { ComponentType } from 'react'
import {
  HomeOutlined,
  ApiOutlined,
  TeamOutlined,
  UserOutlined,
  SafetyOutlined,
  ScheduleOutlined,
  SettingOutlined,
  FileTextOutlined,
  CloudServerOutlined,
  CodeOutlined,
} from '@ant-design/icons'

export interface MenuItem { key: string; path?: string; icon?: string; label: string; roles?: string[]; children?: MenuItem[] }
export const IconMap: Record<string, ComponentType> = {
  HomeOutlined,
  ApiOutlined,
  TeamOutlined,
  UserOutlined,
  SafetyOutlined,
  ScheduleOutlined,
  SettingOutlined,
  FileTextOutlined,
  CloudServerOutlined,
  CodeOutlined,
}
export const menuConfig: MenuItem[] = [
  { key: 'home', path: '/home', icon: 'HomeOutlined', label: 'home.title', roles: ['admin'] },
  { key: 'model-adapter', path: '/model-adapter', icon: 'ApiOutlined', label: 'modelAdapter.title', roles: ['admin'] },
  { key: 'tenant-management', path: '/tenant-management', icon: 'TeamOutlined', label: 'tenantManagement.title', roles: ['admin'] },
  { key: 'user-management', path: '/user-management', icon: 'UserOutlined', label: 'userManagement.title', roles: ['admin'] },
  { key: 'role-permission', path: '/role-permission', icon: 'SafetyOutlined', label: 'rolePermission.title', roles: ['admin'] },
  { key: 'task-schedule', path: '/task-schedule', icon: 'ScheduleOutlined', label: 'taskSchedule.title', roles: ['admin'] },
  { key: 'system-config', path: '/system-config', icon: 'SettingOutlined', label: 'systemConfig.title', roles: ['admin'] },
  { key: 'operation-log', path: '/operation-log', icon: 'FileTextOutlined', label: 'operationLog.title', roles: ['admin'] },
  { key: 'data-access', path: '/data-access', icon: 'CloudServerOutlined', label: 'dataAccess.title', roles: ['admin'] },
  { key: 'parser-management', path: '/parser-management', icon: 'CodeOutlined', label: 'parserManagement.title', roles: ['admin'] },
]
