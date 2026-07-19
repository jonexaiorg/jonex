import { redirect } from 'react-router-dom'
import { isEmbedded } from '@jonex/shell-sdk'
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
const PromptTemplates = loadableComponent(() => import('@/pages/PromptTemplates'))
const NotFound = loadableComponent(() => import('@/pages/NotFound'))

export function getRoutes(mode: 'standalone' | 'hosted' = 'standalone') {
  const Layout = mode === 'hosted' || isEmbedded() ? HostedLayout : BasicLayout
  return [
    { path: '/', loader: () => redirect('/adapter-management') },
    { path: '', element: Layout, children: [
      { path: 'home', element: Home, title: 'adapter.title' },
      { path: 'adapter-management', element: AdapterManagement, title: 'adapter.title' },
      { path: 'business-marketplace', element: BusinessMarketplace, title: 'businessMarketplace.title' },
      { path: 'skills', element: Skills, title: 'skill.title' },
      { path: 'template-domains', element: TemplateDomains, title: 'templateDomain.title' },
      { path: 'template-scenarios', element: TemplateScenarios, title: 'templateScenario.title' },
      { path: 'template-objects', element: TemplateObjects, title: 'templateObject.title' },
      { path: 'template-relations', element: TemplateRelations, title: 'templateRelation.title' },
      { path: 'prompt-templates', element: PromptTemplates, title: 'promptTemplate.title' },
    ]},
    { path: '*', element: NotFound, title: '404' },
  ]
}
export default getRoutes('standalone')
