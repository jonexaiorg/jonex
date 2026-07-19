import { redirect } from 'react-router-dom'
import { isEmbedded } from '@jonex/shell-sdk'
import loadableComponent from '@/utils/loadable'

const BasicLayout = loadableComponent(() => import('@/components/BasicLayout'))
const HostedLayout = loadableComponent(() => import('@/components/HostedLayout'))
const Home = loadableComponent(() => import('@/pages/Home'))
const ModelAdapter = loadableComponent(() => import('@/pages/ModelAdapter'))
const TenantManagement = loadableComponent(() => import('@/pages/TenantManagement'))
const UserManagement = loadableComponent(() => import('@/pages/UserManagement'))
const RolePermission = loadableComponent(() => import('@/pages/RolePermission'))
const TaskSchedule = loadableComponent(() => import('@/pages/TaskSchedule'))
const SystemConfig = loadableComponent(() => import('@/pages/SystemConfig'))
const OperationLog = loadableComponent(() => import('@/pages/OperationLog'))
const DataAccess = loadableComponent(() => import('@/pages/DataAccess'))
const ParserManagement = loadableComponent(() => import('@/pages/ParserManagement'))
const KnowledgeCompile = loadableComponent(() => import('@/pages/KnowledgeCompile'))
const KnowledgeCompileSearch = loadableComponent(() => import('@/pages/KnowledgeCompileSearch'))
const KnowledgeCompileGraph = loadableComponent(() => import('@/pages/KnowledgeCompileGraph'))
const KnowledgeCompileVector = loadableComponent(() => import('@/pages/KnowledgeCompileVector'))
const KnowledgeCompileCompile = loadableComponent(() => import('@/pages/KnowledgeCompileCompile'))
const NotFound = loadableComponent(() => import('@/pages/NotFound'))

export function getRoutes(mode: 'standalone' | 'hosted' = 'standalone') {
  const Layout = mode === 'hosted' || isEmbedded() ? HostedLayout : BasicLayout
  return [
    { path: '/', loader: () => redirect('/model-adapter') },
    { path: '', element: Layout, children: [
      { path: 'home', element: Home, title: 'home.title' },
      { path: 'model-adapter', element: ModelAdapter, title: 'modelAdapter.title' },
      { path: 'tenant-management', element: TenantManagement, title: 'tenantManagement.title' },
      { path: 'user-management', element: UserManagement, title: 'userManagement.title' },
      { path: 'role-permission', element: RolePermission, title: 'rolePermission.title' },
      { path: 'task-schedule', element: TaskSchedule, title: 'taskSchedule.title' },
      { path: 'system-config', element: SystemConfig, title: 'systemConfig.title' },
      { path: 'operation-log', element: OperationLog, title: 'operationLog.title' },
      { path: 'data-access', element: DataAccess, title: 'dataAccess.title' },
      { path: 'parser-management', element: ParserManagement, title: 'parserManagement.title' },
      { path: 'knowledge-compile', element: KnowledgeCompile, title: 'knowledgeCompile.title' },
      { path: 'knowledge-compile/search', element: KnowledgeCompileSearch, title: 'knowledgeCompile.search' },
      { path: 'knowledge-compile/graph', element: KnowledgeCompileGraph, title: 'knowledgeCompile.graph' },
      { path: 'knowledge-compile/vector', element: KnowledgeCompileVector, title: 'knowledgeCompile.vector' },
      { path: 'knowledge-compile/compile', element: KnowledgeCompileCompile, title: 'knowledgeCompile.compile' },
    ]},
    { path: '*', element: NotFound, title: '404' },
  ]
}
export default getRoutes('standalone')
