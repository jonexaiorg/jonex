import type { ComponentType } from 'react'
import {
  SearchOutlined,
  BlockOutlined,
  DatabaseOutlined,
  ClusterOutlined,
} from '@ant-design/icons'

export interface MenuItem {
  key: string
  path?: string
  icon?: string
  label: string
  roles?: string[]
  children?: MenuItem[]
}

export const IconMap: Record<string, ComponentType> = {
  SearchOutlined,
  BlockOutlined,
  DatabaseOutlined,
  ClusterOutlined,
}

export const menuConfig: MenuItem[] = [
  {
    key: 'knowledge-search',
    path: '/knowledge-search',
    icon: 'SearchOutlined',
    label: 'knowledgeSearch.title',
    roles: ['admin', 'user'],
  },
  {
    key: 'domain-space',
    path: '/domain-space',
    icon: 'BlockOutlined',
    label: 'domainSpace.title',
    roles: ['admin', 'user'],
  },
  {
    key: 'domain-knowledge',
    path: '/domain-knowledge',
    icon: 'DatabaseOutlined',
    label: 'domainKnowledge.title',
    roles: ['admin', 'user'],
  },
  {
    key: 'domain-management',
    path: '/domain-management',
    icon: 'ClusterOutlined',
    label: 'domainService.title',
    roles: ['admin'],
  },
]
