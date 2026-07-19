import type { ComponentType } from 'react'
import { BlockOutlined, ShopOutlined, ThunderboltOutlined, CopyOutlined, AppstoreAddOutlined, FileTextOutlined } from '@ant-design/icons'

export interface MenuItem { key: string; path?: string; icon?: string; label: string; roles?: string[]; children?: MenuItem[] }
export const IconMap: Record<string, ComponentType> = { BlockOutlined, ShopOutlined, ThunderboltOutlined, CopyOutlined, AppstoreAddOutlined, FileTextOutlined }
export const menuConfig: MenuItem[] = [
  { key: 'adapter-management', path: '/adapter-management', icon: 'BlockOutlined', label: 'adapter.title', roles: ['admin', 'user'] },
  { key: 'business-marketplace', path: '/business-marketplace', icon: 'ShopOutlined', label: 'businessMarketplace.title', roles: ['admin', 'user'] },
  { key: 'skills', path: '/skills', icon: 'ThunderboltOutlined', label: 'skill.title', roles: ['admin', 'user'] },
  { key: 'prompt-templates', path: '/prompt-templates', icon: 'FileTextOutlined', label: 'promptTemplate.title', roles: ['admin', 'user'] },
  { key: 'template-domains', path: '/template-domains', icon: 'CopyOutlined', label: 'templateDomain.title', roles: ['admin', 'user'] },
]
