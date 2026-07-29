import type { ComponentType } from 'react';
import { SearchOutlined, BlockOutlined, DatabaseOutlined, ClusterOutlined } from '@ant-design/icons';

export interface MenuItem {
  key: string;
  path?: string;
  icon?: string;
  label: string;
  roles?: string[];
  children?: MenuItem[];
}

export const IconMap: Record<string, ComponentType> = {
  SearchOutlined,
  BlockOutlined,
  DatabaseOutlined,
  ClusterOutlined,
};

export function getMenuConfig(t: (key: string) => string): MenuItem[] {
  return [
    {
      key: 'knowledge-search',
      path: '/knowledge-search',
      icon: 'SearchOutlined',
      label: t('navigation.knowledgeSearch'),
      roles: ['admin', 'user'],
    },
    {
      key: 'domain-space',
      path: '/domain-space',
      icon: 'BlockOutlined',
      label: t('navigation.domainSpace'),
      roles: ['admin', 'user'],
    },
    {
      key: 'domain-knowledge',
      path: '/domain-knowledge',
      icon: 'DatabaseOutlined',
      label: t('navigation.domainKnowledge'),
      roles: ['admin', 'user'],
    },
    {
      key: 'domain-management',
      path: '/domain-management',
      icon: 'ClusterOutlined',
      label: t('navigation.domainManagement'),
      roles: ['admin'],
    },
  ];
}
