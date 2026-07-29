import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

export default function RouteSync() {
  const location = useLocation();

  useEffect(() => {
    const path = location.pathname + location.search + location.hash;
    if (path === '/' || path === '/home') return;

    const inIframe = window.parent !== window;
    const win = (inIframe ? window.parent : window) as any;
    const shellCtx = win.__SHELL_CONTEXT__;

    let basePath;
    if (inIframe) {
      basePath = '/apps/ecosystem-management';
    } else if (shellCtx?.basePath) {
      basePath = shellCtx.basePath;
    } else if (shellCtx) {
      basePath = '/apps/ecosystem-management';
    } else {
      basePath = '/ecosystem-management';
    }

    if (basePath.endsWith('/')) basePath = basePath.slice(0, -1);

    win.history.replaceState({}, '', `${basePath}${path}`);
  }, [location]);

  return null;
}
