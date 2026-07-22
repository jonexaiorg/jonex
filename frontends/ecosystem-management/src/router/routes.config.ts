import { redirect } from 'react-router-dom'
import loadableComponent from '@/utils/loadable'

const BasicLayout = loadableComponent(() => import('@/components/BasicLayout'))
const HostedLayout = loadableComponent(() => import('@/components/HostedLayout'))
const Home = loadableComponent(() => import('@/pages/Home'))
const AdapterManagement = loadableComponent(() => import('@/pages/AdapterManagement'))
const BusinessMarketplace = loadableComponent(() => import('@/pages/BusinessMarketplace'))
const Skills = loadableComponent(() => import('@/pages/Skills'))
const TemplateDomains = loadableComponent(() => import('@/pages/TemplateDomains'))
const TemplateScenarios = loadableComponent(() => import('@/pages/TemplateScenarios'))
const TemplateObjects = loadableComponent(() => import('@/pages/TemplateObjects'))
const TemplateRelations = loadableComponent(() => import('@/pages/TemplateRelations'))
const NotFound = loadableComponent(() => import('@/pages/NotFound'))

export function getRoutes(mode: 'standalone' | 'hosted' = 'standalone') {
  const Layout = mode === 'hosted' ? HostedLayout : BasicLayout
  return [
    { path: '/', loader: () => redirect('/adapter-management') },
    { path: '', element: Layout, children: [
      { path: 'home', element: Home, title: '生态管理' },
      { path: 'adapter-management', element: AdapterManagement, title: '适配器管理' },
      { path: 'business-marketplace', element: BusinessMarketplace, title: '业务领域商场' },
      { path: 'skills', element: Skills, title: '技能管理' },
      { path: 'template-domains', element: TemplateDomains, title: '模板领域' },
      { path: 'template-scenarios', element: TemplateScenarios, title: '模板领域场景' },
      { path: 'template-objects', element: TemplateObjects, title: '模板对象管理' },
      { path: 'template-relations', element: TemplateRelations, title: '模板关系管理' },
    ]},
    { path: '*', element: NotFound, title: '404' },
  ]
}
export default getRoutes('standalone')
