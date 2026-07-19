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
} from '@ant-design/icons'
import type { NavSection } from './navTypes'

export const prototypeNavConfig: NavSection[] = [
  {
    key: 'core-features',
    label: 'navigation.coreBusiness',
    icon: HomeOutlined,
    items: [
      {
        key: 'knowledge-search',
        label: 'navigation.knowledgeSearch',
        appId: 'core-business',
        internalPath: 'knowledge-search',
        icon: SearchOutlined,
      },
      {
        key: 'domain-knowledge',
        label: 'navigation.domainKnowledge',
        appId: 'core-business',
        internalPath: 'domain-knowledge',
        icon: DatabaseOutlined,
      },
      {
        key: 'domain-management',
        label: 'navigation.domainManagement',
        appId: 'core-business',
        internalPath: 'domain-management',
        icon: ClusterOutlined,
      },
    ],
  },
  {
    key: 'platform',
    label: 'navigation.platformManagement',
    icon: SettingOutlined,
    items: [
      {
        key: 'engine-mgmt-group',
        label: 'navigation.engineManagement',
        icon: ApiOutlined,
        children: [
          {
            key: 'data-access',
            label: 'navigation.dataAccess',
            appId: 'platform-management',
            internalPath: 'data-access',
          },
          {
            key: 'parser-management',
            label: 'navigation.parserManagement',
            appId: 'platform-management',
            internalPath: 'parser-management',
          },
          {
            key: 'model-adapter',
            label: 'navigation.modelAdapter',
            appId: 'platform-management',
            internalPath: 'model-adapter',
          },
        ],
      },
      {
        key: 'prompt-templates',
        label: 'navigation.promptTemplates',
        appId: 'ecosystem-management',
        internalPath: 'prompt-templates',
        icon: FileTextOutlined,
      },
      {
        key: 'administration-group',
        label: 'navigation.administration',
        icon: SettingOutlined,
        children: [
          {
            key: 'tenant-management',
            label: 'navigation.tenantManagement',
            appId: 'platform-management',
            internalPath: 'tenant-management',
          },
          {
            key: 'user-management',
            label: 'navigation.userManagement',
            appId: 'platform-management',
            internalPath: 'user-management',
          },
          {
            key: 'role-permission',
            label: 'navigation.rolePermission',
            appId: 'platform-management',
            internalPath: 'role-permission',
          },
          {
            key: 'system-config',
            label: 'navigation.systemConfig',
            appId: 'platform-management',
            internalPath: 'system-config',
          },
          {
            key: 'operation-log',
            label: 'navigation.operationLog',
            appId: 'platform-management',
            internalPath: 'operation-log',
          },
        ],
      },
    ],
  },
  {
    key: 'integrations',
    label: 'navigation.ecosystemManagement',
    icon: GlobalOutlined,
    items: [
      {
        key: 'eco-adapter-group',
        label: 'navigation.ecoAdapter',
        icon: BlockOutlined,
        children: [
          {
            key: 'adapter-management',
            label: 'navigation.adapterList',
            appId: 'ecosystem-management',
            internalPath: 'adapter-management',
          },
        ],
      },
      {
        key: 'skill-management-group',
        label: 'navigation.skillManagement',
        icon: ThunderboltOutlined,
        children: [
          {
            key: 'skills',
            label: 'navigation.skills',
            appId: 'ecosystem-management',
            internalPath: 'skills',
          },
        ],
      },
      {
        key: 'template-domains',
        label: 'navigation.templateDomains',
        appId: 'ecosystem-management',
        internalPath: 'template-domains',
        icon: CopyOutlined,
      },
    ],
  },
]
