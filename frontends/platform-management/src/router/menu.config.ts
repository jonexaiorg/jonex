import type { ComponentType } from 'react';
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
} from '@ant-design/icons';

export interface MenuItem {
  key: string;
  path?: string;
  icon?: string;
  label: string;
  roles?: string[];
  children?: MenuItem[];
}
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
};
export const menuConfig: MenuItem[] = [
  { key: 'home', path: '/home', icon: 'HomeOutlined', label: 'navigation.home', roles: ['admin'] },
  {
    key: 'model-adapter',
    path: '/model-adapter',
    icon: 'ApiOutlined',
    label: 'navigation.modelAdapter',
    roles: ['admin'],
  },
  {
    key: 'tenant-management',
    path: '/tenant-management',
    icon: 'TeamOutlined',
    label: 'navigation.tenantManagement',
    roles: ['admin'],
  },
  {
    key: 'user-management',
    path: '/user-management',
    icon: 'UserOutlined',
    label: 'navigation.userManagement',
    roles: ['admin'],
  },
  {
    key: 'role-permission',
    path: '/role-permission',
    icon: 'SafetyOutlined',
    label: 'navigation.rolePermission',
    roles: ['admin'],
  },
  {
    key: 'task-schedule',
    path: '/task-schedule',
    icon: 'ScheduleOutlined',
    label: 'navigation.taskSchedule',
    roles: ['admin'],
  },
  {
    key: 'system-config',
    path: '/system-config',
    icon: 'SettingOutlined',
    label: 'navigation.systemConfig',
    roles: ['admin'],
  },
  {
    key: 'operation-log',
    path: '/operation-log',
    icon: 'FileTextOutlined',
    label: 'navigation.operationLog',
    roles: ['admin'],
  },
  {
    key: 'data-access',
    path: '/data-access',
    icon: 'CloudServerOutlined',
    label: 'navigation.dataAccessMethods',
    roles: ['admin'],
  },
  {
    key: 'parser-management',
    path: '/parser-management',
    icon: 'CodeOutlined',
    label: 'navigation.parserManagement',
    roles: ['admin'],
  },
];
