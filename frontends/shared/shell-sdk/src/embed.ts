/**
 * 嵌入模式（embed）协议
 *
 * 当 Shell 用 iframe 内嵌子应用的 standalone 版本时（本地开发 fallback），
 * 会在 iframe URL 上带 `?embed=1`。子应用据此渲染「无壳布局」（不显示自己的
 * 侧边栏/顶栏），避免与 Shell 的外壳重复，从而无需再用 CSS 事后隐藏菜单。
 *
 * 这是 Shell 与子应用之间的浏览器级约定，常量放在 shell-sdk 做唯一来源，
 * 避免两侧参数名漂移。
 */
export const EMBED_QUERY_PARAM = 'embed';

/**
 * 当前页面是否处于 Shell iframe 嵌入模式（URL 带 `?embed=1`）。
 * 仅在浏览器环境有意义；非浏览器环境返回 false。
 */
export function isEmbedded(): boolean {
  if (typeof window === 'undefined') return false;
  try {
    return new URLSearchParams(window.location.search).get(EMBED_QUERY_PARAM) === '1';
  } catch {
    return false;
  }
}
