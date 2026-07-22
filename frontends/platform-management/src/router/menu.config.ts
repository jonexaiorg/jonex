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
  { key: 'home', path: '/home', icon: 'HomeOutlined', label: '平台管理概览', roles: ['admin'] },
  { key: 'model-adapter', path: '/model-adapter', icon: 'ApiOutlined', label: '模型适配', roles: ['admin'] },
  { key: 'tenant-management', path: '/tenant-management', icon: 'TeamOutlined', label: '租户管理', roles: ['admin'] },
  { key: 'user-management', path: '/user-management', icon: 'UserOutlined', label: '用户管理', roles: ['admin'] },
  { key: 'role-permission', path: '/role-permission', icon: 'SafetyOutlined', label: '角色权限', roles: ['admin'] },
  { key: 'task-schedule', path: '/task-schedule', icon: 'ScheduleOutlined', label: '任务调度', roles: ['admin'] },
  { key: 'system-config', path: '/system-config', icon: 'SettingOutlined', label: '系统配置', roles: ['admin'] },
  { key: 'operation-log', path: '/operation-log', icon: 'FileTextOutlined', label: '操作日志', roles: ['admin'] },
  { key: 'data-access', path: '/data-access', icon: 'CloudServerOutlined', label: '数据接入方式', roles: ['admin'] },
  { key: 'parser-management', path: '/parser-management', icon: 'CodeOutlined', label: '解析器管理', roles: ['admin'] },
]
