import {
  HomeOutlined,
  SettingOutlined,
  GlobalOutlined,
  SearchOutlined,
  DatabaseOutlined,
  ClusterOutlined,
  CloudServerOutlined,
  CodeOutlined,
  BlockOutlined,
  UserOutlined,
  SafetyOutlined,
  FileTextOutlined,
  ApiOutlined,
  ThunderboltOutlined,
  CopyOutlined,
  AppstoreAddOutlined,
} from '@ant-design/icons'
import type { NavSection } from './navTypes'

export const prototypeNavConfig: NavSection[] = [
  {
    key: 'core-business',
    label: '业务领域管理',
    icon: HomeOutlined,
    items: [
      {
        key: 'knowledge-search',
        label: '领域知识检索',
        appId: 'core-business',
        internalPath: 'knowledge-search',
        icon: SearchOutlined,
      },
      {
        key: 'domain-space',
        label: '领域空间管理',
        appId: 'core-business',
        internalPath: 'domain-space',
        icon: GlobalOutlined,
      },
      {
        key: 'domain-knowledge',
        label: '领域知识管理',
        appId: 'core-business',
        internalPath: 'domain-knowledge',
        icon: DatabaseOutlined,
      },
      {
        key: 'domain-management',
        label: '领域服务管理',
        appId: 'core-business',
        internalPath: 'domain-management',
        icon: ClusterOutlined,
      },
    ],
  },
  {
    key: 'platform-management',
    label: '平台管理',
    icon: SettingOutlined,
    items: [
      {
        key: 'engine-mgmt-group',
        label: '引擎管理',
        icon: ApiOutlined,
        children: [
          {
            key: 'data-access',
            label: '数据接入方式',
            appId: 'platform-management',
            internalPath: 'data-access',
          },
          {
            key: 'parser-management',
            label: '解析器管理',
            appId: 'platform-management',
            internalPath: 'parser-management',
          },
          {
            key: 'model-adapter',
            label: '模型适配',
            appId: 'platform-management',
            internalPath: 'model-adapter',
          },
        ],
      },
      {
        key: 'platform-mgmt-group',
        label: '平台管理',
        icon: SettingOutlined,
        children: [
          {
            key: 'tenant-management',
            label: '租户管理',
            appId: 'platform-management',
            internalPath: 'tenant-management',
          },
          {
            key: 'user-management',
            label: '用户管理',
            appId: 'platform-management',
            internalPath: 'user-management',
          },
          {
            key: 'role-permission',
            label: '角色权限',
            appId: 'platform-management',
            internalPath: 'role-permission',
          },
          {
            key: 'system-config',
            label: '系统配置',
            appId: 'platform-management',
            internalPath: 'system-config',
          },
          {
            key: 'operation-log',
            label: '日志管理',
            appId: 'platform-management',
            internalPath: 'operation-log',
          },
        ],
      },
    ],
  },
  {
    key: 'ecosystem-management',
    label: '生态管理',
    icon: GlobalOutlined,
    items: [
      {
        key: 'eco-adapter-group',
        label: '生态适配器',
        icon: BlockOutlined,
        children: [
          {
            key: 'adapter-management',
            label: '适配器列表',
            appId: 'ecosystem-management',
            internalPath: 'adapter-management',
          },
        ],
      },
      {
        key: 'eco-skills-group',
        label: 'Skills',
        icon: ThunderboltOutlined,
        children: [
          {
            key: 'skills',
            label: '技能管理',
            appId: 'ecosystem-management',
            internalPath: 'skills',
          },
        ],
      },
      {
        key: 'eco-template-group',
        label: '业务领域模板',
        icon: CopyOutlined,
        children: [
          {
            key: 'template-domains',
            label: '模板领域',
            appId: 'ecosystem-management',
            internalPath: 'template-domains',
          },
          {
            key: 'template-scenarios',
            label: '模板领域场景',
            appId: 'ecosystem-management',
            internalPath: 'template-scenarios',
          },
        ],
      },
    ],
  },
]
