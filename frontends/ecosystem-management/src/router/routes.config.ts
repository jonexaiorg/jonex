import { redirect } from 'react-router-dom';
import { isEmbedded } from '@jonex/shell-sdk';
import loadableComponent from '@/utils/loadable';

const BasicLayout = loadableComponent(() => import('@/components/BasicLayout'));
const HostedLayout = loadableComponent(() => import('@/components/HostedLayout'));
const Home = loadableComponent(() => import('@/pages/Home'));
const AdapterManagement = loadableComponent(() => import('@/pages/AdapterManagement'));
const BusinessMarketplace = loadableComponent(() => import('@/pages/BusinessMarketplace'));
const Skills = loadableComponent(() => import('@/pages/Skills'));
const TemplateDomains = loadableComponent(() => import('@/pages/TemplateDomains'));
const TemplateScenarios = loadableComponent(() => import('@/pages/TemplateScenarios'));
const TemplateObjects = loadableComponent(() => import('@/pages/TemplateObjects'));
const TemplateRelations = loadableComponent(() => import('@/pages/TemplateRelations'));
const PromptTemplates = loadableComponent(() => import('@/pages/PromptTemplates'));
const NotFound = loadableComponent(() => import('@/pages/NotFound'));

export function getRoutes(mode: 'standalone' | 'hosted' = 'standalone') {
  const inIframe = typeof window !== 'undefined' && window.parent !== window;
  const Layout = mode === 'hosted' || (isEmbedded() && inIframe) ? HostedLayout : BasicLayout;
  return [
    { path: '/', loader: () => redirect('/adapter-management') },
    {
      path: '',
      element: Layout,
      children: [
        { path: 'home', element: Home, title: 'navigation.ecosystemManagement' },
        { path: 'adapter-management', element: AdapterManagement, title: 'navigation.adapterManagement' },
        { path: 'business-marketplace', element: BusinessMarketplace, title: 'navigation.businessMarketplace' },
        { path: 'skills', element: Skills, title: 'navigation.skills' },
        { path: 'template-domains', element: TemplateDomains, title: 'navigation.templateDomains' },
        { path: 'template-scenarios', element: TemplateScenarios, title: 'navigation.templateScenarios' },
        { path: 'template-objects', element: TemplateObjects, title: 'navigation.templateObjects' },
        { path: 'template-relations', element: TemplateRelations, title: 'navigation.templateRelations' },
        { path: 'prompt-templates', element: PromptTemplates, title: 'navigation.promptTemplates' },
      ],
    },
    { path: '*', element: NotFound, title: '404' },
  ];
}
export default getRoutes('standalone');
