import { redirect } from 'react-router-dom'
import loadableComponent from '@/utils/loadable'

const BasicLayout = loadableComponent(() => import('@/components/BasicLayout'))
const HostedLayout = loadableComponent(() => import('@/components/HostedLayout'))
const KnowledgeSearch = loadableComponent(() => import('@/pages/KnowledgeSearch'))
const DomainSpace = loadableComponent(() => import('@/pages/DomainSpace'))
const DomainSpacePermission = loadableComponent(() => import('@/pages/DomainSpacePermission'))
const DomainKnowledge = loadableComponent(() => import('@/pages/DomainKnowledge'))
const DomainKnowledgeDetail = loadableComponent(() => import('@/pages/DomainKnowledgeDetail'))
const DomainKnowledgeDatasourceManual = loadableComponent(() => import('@/pages/DomainKnowledgeDatasourceManual'))
const DomainKnowledgeDatasourceStorage = loadableComponent(() => import('@/pages/DomainKnowledgeDatasourceStorage'))
const DomainKnowledgeDatasourceSync = loadableComponent(() => import('@/pages/DomainKnowledgeDatasourceSync'))
const DomainKnowledgeSourceData = loadableComponent(() => import('@/pages/DomainKnowledgeSourceData'))
const DomainKnowledgeCompileResults = loadableComponent(() => import('@/pages/DomainKnowledgeCompileResults'))
const DomainKnowledgeDataSource = loadableComponent(() => import('@/pages/DomainKnowledgeDataSource'))
const DomainKnowledgeParser = loadableComponent(() => import('@/pages/DomainKnowledgeParser'))
const DomainKnowledgeEngine = loadableComponent(() => import('@/pages/DomainKnowledgeEngine'))
const DomainKnowledgeGraph = loadableComponent(() => import('@/pages/DomainKnowledgeGraph'))
const DomainKnowledgeInstanceDetail = loadableComponent(() => import('@/pages/DomainKnowledgeInstanceDetail'))
const DomainKnowledgeRelationDetail = loadableComponent(() => import('@/pages/DomainKnowledgeRelationDetail'))
const DomainManagement = loadableComponent(() => import('@/pages/DomainManagement'))
const DomainManagementServices = loadableComponent(() => import('@/pages/DomainManagementServices'))
const DomainManagementSearch = loadableComponent(() => import('@/pages/DomainManagementSearch'))
const NotFound = loadableComponent(() => import('@/pages/NotFound'))

export function getRoutes(mode: 'standalone' | 'hosted' = 'standalone') {
  const Layout = mode === 'hosted' ? HostedLayout : BasicLayout

  return [
    {
      path: '/',
      loader: () => redirect('/knowledge-search'),
    },
    {
      path: 'home',
      loader: () => redirect('/knowledge-search'),
    },
    {
      path: '',
      element: Layout,
      children: [
        { path: 'knowledge-search', element: KnowledgeSearch, title: '领域知识检索' },
        { path: 'domain-space', element: DomainSpace, title: '领域空间管理' },
        { path: 'domain-space/permissions', element: DomainSpacePermission, title: '权限管理' },
        { path: 'domain-knowledge', element: DomainKnowledge, title: '领域知识管理' },
        { path: 'domain-knowledge/:id', element: DomainKnowledgeDetail, title: '知识库详情' },
        { path: 'domain-knowledge/:id/datasource/manual', element: DomainKnowledgeDatasourceManual, title: '手动上传数据源' },
        { path: 'domain-knowledge/:id/datasource/storage', element: DomainKnowledgeDatasourceStorage, title: '文件存储直连' },
        { path: 'domain-knowledge/:id/datasource/sync', element: DomainKnowledgeDatasourceSync, title: 'API同步数据源' },
        { path: 'domain-knowledge/:id/source-data', element: DomainKnowledgeSourceData, title: '源数据查看' },
        { path: 'domain-knowledge/:id/compile-results', element: DomainKnowledgeCompileResults, title: '编译结果' },
        { path: 'domain-knowledge/:id/data-source', element: DomainKnowledgeDataSource, title: '数据源配置' },
        { path: 'domain-knowledge/:id/parser', element: DomainKnowledgeParser, title: '解析配置' },
        { path: 'domain-knowledge/:id/engine', element: DomainKnowledgeEngine, title: '引擎配置' },
        { path: 'domain-knowledge/:id/graph', element: DomainKnowledgeGraph, title: '知识图谱' },
        { path: 'domain-knowledge/:id/graph/instances/:instanceId', element: DomainKnowledgeInstanceDetail, title: '实体实例详情' },
        { path: 'domain-knowledge/:id/graph/relations/:relationId', element: DomainKnowledgeRelationDetail, title: '关系详情' },
        { path: 'domain-management', element: DomainManagement, title: '领域服务管理' },
        { path: 'domain-management/services', element: DomainManagementServices, title: '服务管理' },
        { path: 'domain-management/search', element: DomainManagementSearch, title: '知识检索' },
      ],
    },
    { path: '*', element: NotFound, title: '404' },
  ]
}

export default getRoutes('standalone')
