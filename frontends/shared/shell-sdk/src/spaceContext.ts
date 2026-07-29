/**
 * 领域空间全局上下文协议（shell-sdk 唯一来源）
 *
 * 契约：localStorage key + window event name + URL query param
 * Shell 与 core-business 都从这里引入，杜绝双份常量漂移。
 */

export const SPACE_STORAGE_KEY = 'jonex:core-business:selected-space-id';
export const SPACE_CHANGED_EVENT = 'jonex:core-business:space-changed';
export const SPACE_URL_PARAM = 'space_id';

export interface SpaceChangedDetail {
  spaceId: string | null;
}

/** 仅写持久化（回落失效空间时也用它更新 localStorage） */
export function persistSpaceId(spaceId: string | null): void {
  if (spaceId) {
    localStorage.setItem(SPACE_STORAGE_KEY, spaceId);
  } else {
    localStorage.removeItem(SPACE_STORAGE_KEY);
  }
}

/** 仅派发 window 事件 */
export function emitSpaceChanged(spaceId: string | null): void {
  window.dispatchEvent(
    new CustomEvent<SpaceChangedDetail>(SPACE_CHANGED_EVENT, {
      detail: { spaceId },
    }),
  );
}

/** 持久化 + 派发（用户主动切换时的便捷组合） */
export function broadcastSpaceChange(spaceId: string | null): void {
  persistSpaceId(spaceId);
  emitSpaceChanged(spaceId);
}

/** 读持久化的空间 id */
export function readPersistedSpaceId(): string | null {
  return localStorage.getItem(SPACE_STORAGE_KEY);
}

/**
 * 订阅「当前空间变化」，返回取消订阅函数。
 * 双通道覆盖所有部署形态：
 * - window CustomEvent：同窗口（standalone 本窗口内、未来生产 MF hosted）。
 * - storage 事件：跨窗口同源（当前 dev 的 iframe hosted、跨标签页）。
 */
export function onSpaceChanged(handler: (spaceId: string | null) => void): () => void {
  const onCustom = (e: Event) => handler((e as CustomEvent<SpaceChangedDetail>).detail?.spaceId ?? null);
  const onStorage = (e: StorageEvent) => {
    if (e.key === SPACE_STORAGE_KEY) handler(e.newValue);
  };
  window.addEventListener(SPACE_CHANGED_EVENT, onCustom);
  window.addEventListener('storage', onStorage);
  return () => {
    window.removeEventListener(SPACE_CHANGED_EVENT, onCustom);
    window.removeEventListener('storage', onStorage);
  };
}

// —— 空间列表失效：domain-space 管理页增删空间后广播 ——
export const SPACES_INVALIDATED_EVENT = 'jonex:core-business:spaces-invalidated';
const SPACES_INVALIDATED_KEY = 'jonex:core-business:spaces-invalidated-at';

/** 广播「空间列表已变更，请重拉」（同窗口 CustomEvent + 跨窗口 storage 信号） */
export function emitSpacesInvalidated(): void {
  try {
    localStorage.setItem(SPACES_INVALIDATED_KEY, String(Date.now()));
  } catch {
    /* ignore */
  }
  window.dispatchEvent(new CustomEvent(SPACES_INVALIDATED_EVENT));
}

/** 订阅空间列表失效，返回取消订阅函数（同 onSpaceChanged 的双通道） */
export function onSpacesInvalidated(handler: () => void): () => void {
  const onCustom = () => handler();
  const onStorage = (e: StorageEvent) => {
    if (e.key === SPACES_INVALIDATED_KEY) handler();
  };
  window.addEventListener(SPACES_INVALIDATED_EVENT, onCustom);
  window.addEventListener('storage', onStorage);
  return () => {
    window.removeEventListener(SPACES_INVALIDATED_EVENT, onCustom);
    window.removeEventListener('storage', onStorage);
  };
}
