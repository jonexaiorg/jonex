import type { ComponentType } from 'react'
import { HomeOutlined } from '@ant-design/icons'

export interface MenuItem {
  key: string
  path?: string
  icon?: string
  label: string
  roles?: string[]
  children?: MenuItem[]
}

export const IconMap: Record<string, ComponentType> = {
  HomeOutlined,
}

export const menuConfig: MenuItem[] = [
  {
    key: 'home',
    path: '/home',
    icon: 'HomeOutlined',
    label: 'navigation.home',
    roles: ['admin', 'user'],
  },
]
