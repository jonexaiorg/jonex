import { createRoot } from 'react-dom/client';
import App from './App';
import mount from './remote/RemoteApp';
import { bootstrapStandaloneAuth, createStandaloneShellContext } from '@jonex/shell-sdk';
import './locales/i18n';
import './styles/index.scss';
import '@jonex/platform-theme/theme.css';
import '@jonex/platform-theme/layout.css';

// Module Federation 远程模式下，Shell 会调用 mount 函数挂载子应用，
// 不走 main.tsx 的 standalone 初始化路径。
const isFederatedRemote = typeof window !== 'undefined' && !!(window as any).__federation_shared__;

const root = document.getElementById('root');
const shellContext = (window as any).__SHELL_CONTEXT__;

if (shellContext && root) {
  mount(root, shellContext);
} else if (!isFederatedRemote) {
  // 非 Module Federation 远程模式时启动独立应用
  startStandalone();
}

async function startStandalone() {
  const appId = (import.meta as any).env?.VITE_APP_ID || 'core-business';
  const loginUrl = (import.meta as any).env?.VITE_LOGIN || '/login';
  const authMeUrl = (import.meta as any).env?.VITE_AUTH_ME || '/api/v1/auth/me';
  const exchangeTicketUrl = (import.meta as any).env?.VITE_AUTH_EXCHANGE_TICKET;
  const basePath = (import.meta as any).env?.VITE_STANDALONE_BASE || '/';

  const result = await bootstrapStandaloneAuth({
    appId,
    loginUrl,
    authMeUrl,
    exchangeTicketUrl,
  });

  if (!result.authenticated) return;

  const ctx = createStandaloneShellContext({
    appId,
    basePath,
    token: result.token,
    user: result.user,
    loginUrl,
  });

  (window as any).__SHELL_CONTEXT__ = ctx;
  createRoot(root!).render(<App />);
}
