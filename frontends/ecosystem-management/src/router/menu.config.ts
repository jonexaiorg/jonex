import type { ComponentType } from 'react'
import { BlockOutlined, ShopOutlined, ThunderboltOutlined, CopyOutlined, AppstoreAddOutlined } from '@ant-design/icons'

export interface MenuItem { key: string; path?: string; icon?: string; label: string; roles?: string[]; children?: MenuItem[] }
export const IconMap: Record<string, ComponentType> = { BlockOutlined, ShopOutlined, ThunderboltOutlined, CopyOutlined, AppstoreAddOutlined }
export const menuConfig: MenuItem[] = [
  { key: 'adapter-management', path: '/adapter-management', icon: 'BlockOutlined', label: '适配器管理', roles: ['admin', 'user'] },
  { key: 'business-marketplace', path: '/business-marketplace', icon: 'ShopOutlined', label: '业务商场', roles: ['admin', 'user'] },
  { key: 'skills', path: '/skills', icon: 'ThunderboltOutlined', label: '技能管理', roles: ['admin', 'user'] },
  { key: 'template-domains', path: '/template-domains', icon: 'CopyOutlined', label: '模板领域', roles: ['admin', 'user'] },
  { key: 'template-scenarios', path: '/template-scenarios', icon: 'AppstoreAddOutlined', label: '模板领域场景', roles: ['admin', 'user'] },
]
