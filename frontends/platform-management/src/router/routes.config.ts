import { redirect } from 'react-router-dom'
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
  const Layout = mode === 'hosted' ? HostedLayout : BasicLayout
  return [
    { path: '/', loader: () => redirect('/model-adapter') },
    { path: '', element: Layout, children: [
      { path: 'home', element: Home, title: '平台管理' },
      { path: 'model-adapter', element: ModelAdapter, title: '模型适配' },
      { path: 'tenant-management', element: TenantManagement, title: '租户管理' },
      { path: 'user-management', element: UserManagement, title: '用户管理' },
      { path: 'role-permission', element: RolePermission, title: '角色权限' },
      { path: 'task-schedule', element: TaskSchedule, title: '任务调度' },
      { path: 'system-config', element: SystemConfig, title: '系统配置' },
      { path: 'operation-log', element: OperationLog, title: '操作日志' },
      { path: 'data-access', element: DataAccess, title: '数据接入方式' },
      { path: 'parser-management', element: ParserManagement, title: '解析器管理' },
      { path: 'knowledge-compile', element: KnowledgeCompile, title: '知识编译' },
      { path: 'knowledge-compile/search', element: KnowledgeCompileSearch, title: '编译检索' },
      { path: 'knowledge-compile/graph', element: KnowledgeCompileGraph, title: '知识图谱' },
      { path: 'knowledge-compile/vector', element: KnowledgeCompileVector, title: '向量检索' },
      { path: 'knowledge-compile/compile', element: KnowledgeCompileCompile, title: '编译管理' },
    ]},
    { path: '*', element: NotFound, title: '404' },
  ]
}
export default getRoutes('standalone')
