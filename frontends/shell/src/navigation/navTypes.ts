import type { ComponentType } from 'react';

export interface PrototypeNavItem {
  key: string;
  label: string;
  appId?: string;
  internalPath?: string;
  icon?: ComponentType;
  tag?: '设计中' | '未来';
  hidden?: boolean;
  children?: PrototypeNavItem[];
  /** 额外匹配路径，当这些路径匹配时该导航项也视为高亮 */
  matchPaths?: { appId: string; internalPath: string }[];
}

export interface NavSection {
  key: string;
  label: string;
  icon: ComponentType;
  items: PrototypeNavItem[];
}

export interface BreadcrumbEntry {
  title: string;
  path: string;
}
