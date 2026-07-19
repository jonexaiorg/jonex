import { redirect } from 'react-router-dom'
import { isEmbedded } from '@jonex/shell-sdk'
import loadableComponent from '@/utils/loadable'

const BasicLayout = loadableComponent(() => import('@/components/BasicLayout'))
const HostedLayout = loadableComponent(() => import('@/components/HostedLayout'))
const KnowledgeSearch = loadableComponent(() => import('@/pages/KnowledgeSearch'))
const DomainSpace = loadableComponent(() => import('@/pages/DomainSpace'))
const DomainSpaceCreate = loadableComponent(() => import('@/pages/DomainSpaceCreate'))
const DomainSpaceSettings = loadableComponent(() => import('@/pages/DomainSpaceSettings'))
const DomainSpacePermission = loadableComponent(() => import('@/pages/DomainSpacePermission'))
const DomainKnowledge = loadableComponent(() => import('@/pages/DomainKnowledge'))
const DomainKnowledgeDetail = loadableComponent(() => import('@/pages/DomainKnowledgeDetail'))
const DomainKnowledgeDatasourceManual = loadableComponent(() => import('@/pages/DomainKnowledgeDatasourceManual'))
const DomainKnowledgeDatasourceStorage = loadableComponent(() => import('@/pages/DomainKnowledgeDatasourceStorage'))
const DomainKnowledgeDatasourceSync = loadableComponent(() => import('@/pages/DomainKnowledgeDatasourceSync'))
const DomainKnowledgeDatasourceApiPush = loadableComponent(() => import('@/pages/DomainKnowledgeDatasourceApiPush'))
const DomainKnowledgeSourceData = loadableComponent(() => import('@/pages/DomainKnowledgeSourceData'))
const DomainKnowledgeCompileResults = loadableComponent(() => import('@/pages/DomainKnowledgeCompileResults'))
const DomainKnowledgeDataSource = loadableComponent(() => import('@/pages/DomainKnowledgeDataSource'))
const DomainKnowledgeParser = loadableComponent(() => import('@/pages/DomainKnowledgeParser'))
const DomainKnowledgeEngine = loadableComponent(() => import('@/pages/DomainKnowledgeEngine'))
const DomainKnowledgeGraph = loadableComponent(() => import('@/pages/DomainKnowledgeGraph'))
const DomainKnowledgeInstanceDetail = loadableComponent(() => import('@/pages/DomainKnowledgeInstanceDetail'))
const DomainKnowledgeRelationDetail = loadableComponent(() => import('@/pages/DomainKnowledgeRelationDetail'))
const DomainKnowledgeInstanceList = loadableComponent(() => import('@/pages/DomainKnowledgeInstanceList'))
const KnowledgeTracking = loadableComponent(() => import('@/pages/KnowledgeTracking'))
const DomainKnowledgeRelationList = loadableComponent(() => import('@/pages/DomainKnowledgeRelationList'))
const DomainManagement = loadableComponent(() => import('@/pages/DomainManagement'))
const DomainManagementServices = loadableComponent(() => import('@/pages/DomainManagementServices'))
const DomainManagementSearch = loadableComponent(() => import('@/pages/DomainManagementSearch'))
const NotFound = loadableComponent(() => import('@/pages/NotFound'))

export function getRoutes(mode: 'standalone' | 'hosted' = 'standalone') {


  const Layout = mode === 'hosted' || isEmbedded() ? HostedLayout : BasicLayout

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
        { path: 'knowledge-search', element: KnowledgeSearch, title: 'knowledgeSearch.title' },
        { path: 'domain-space', element: DomainSpace, title: 'domainSpace.title' },
        { path: 'domain-space/new', element: DomainSpaceCreate, title: 'domainSpace.create' },
        { path: 'domain-space/:id/settings', element: DomainSpaceSettings, title: 'domainSpace.settings' },
        { path: 'domain-space/permissions', element: DomainSpacePermission, title: 'domainSpace.permission' },
        { path: 'domain-knowledge', element: DomainKnowledge, title: 'domainKnowledge.title' },
        { path: 'domain-knowledge/:id', element: DomainKnowledgeDetail, title: 'domainKnowledge.detail' },
        { path: 'domain-knowledge/:id/datasource/manual', element: DomainKnowledgeDatasourceManual, title: 'dataSource.manualUpload' },
        { path: 'domain-knowledge/:id/datasource/storage/:dsId', element: DomainKnowledgeDatasourceStorage, title: 'dataSource.storageDirect' },
        { path: 'domain-knowledge/:id/datasource/sync/:dsId', element: DomainKnowledgeDatasourceSync, title: 'dataSource.apiSync' },
        { path: 'domain-knowledge/:id/datasource/api-push/:dsId', element: DomainKnowledgeDatasourceApiPush, title: 'dataSource.apiPush' },
        { path: 'domain-knowledge/:id/source-data', element: DomainKnowledgeSourceData, title: 'knowledgeSearch.sourceData' },
        { path: 'domain-knowledge/:id/compile-results', element: DomainKnowledgeCompileResults, title: 'knowledgeSearch.compileResults' },
        { path: 'domain-knowledge/:id/data-source', element: DomainKnowledgeDataSource, title: 'knowledgeSearch.dataSourceConfig' },
        { path: 'domain-knowledge/:id/parser', element: DomainKnowledgeParser, title: 'knowledgeSearch.parserConfig' },
        { path: 'domain-knowledge/:id/engine', element: DomainKnowledgeEngine, title: 'knowledgeSearch.engineConfig' },
        { path: 'domain-knowledge/:id/graph', element: DomainKnowledgeGraph, title: 'knowledgeSearch.knowledgeGraph' },
        { path: 'domain-knowledge/:id/graph/instances/:instanceId', element: DomainKnowledgeInstanceDetail, title: 'knowledgeSearch.entityInstance' },
        { path: 'domain-knowledge/:id/graph/relations/:relationId', element: DomainKnowledgeRelationDetail, title: 'knowledgeSearch.relationDetail' },
        { path: 'domain-knowledge/:id/result/instances/:entityType', element: DomainKnowledgeInstanceList, title: 'knowledgeSearch.entityList' },
        { path: 'domain-knowledge/:id/tracking', element: KnowledgeTracking, title: 'knowledgeSearch.knowledgeTracking' },
        { path: 'domain-knowledge/:id/result/relations/:relationName', element: DomainKnowledgeRelationList, title: 'knowledgeSearch.relationList' },
        { path: 'domain-management', element: DomainManagement, title: 'domainService.title' },
        { path: 'domain-management/services', element: DomainManagementServices, title: 'domainService.serviceList' },
        { path: 'domain-management/search', element: DomainManagementSearch, title: 'knowledgeSearch.title' },
      ],
    },
    { path: '*', element: NotFound, title: '404' },
  ]
}

export default getRoutes('standalone')
