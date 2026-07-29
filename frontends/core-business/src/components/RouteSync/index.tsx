import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * 将子应用的内部路由同步到浏览器地址栏。
 * 嵌入模式（iframe）下以父窗口 /apps/ 路径为准。
 */
export default function RouteSync() {
  const location = useLocation();

  useEffect(() => {
    const path = location.pathname + location.search + location.hash;
    if (path === '/' || path === '/home') return;

    const inIframe = window.parent !== window;
    const win = (inIframe ? window.parent : window) as any;
    const shellCtx = win.__SHELL_CONTEXT__;

    // 确定 basename
    let basePath;
    if (inIframe) {
      basePath = '/apps/core-business';
    } else if (shellCtx?.basePath) {
      basePath = shellCtx.basePath;
    } else if (shellCtx) {
      basePath = '/apps/core-business';
    } else {
      basePath = '/core-business';
    }

    // 移除末尾斜杠
    if (basePath.endsWith('/')) basePath = basePath.slice(0, -1);

    win.history.replaceState({}, '', `${basePath}${path}`);
  }, [location]);

  return null;
}
