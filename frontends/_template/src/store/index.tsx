import { useGlobalStore } from './global';

/** 兼容旧用法：const { global } = useStore(); global.xxx 仍可响应式工作 */
export function useStore() {
  return { global: useGlobalStore() };
}

export { useGlobalStore } from './global';

export default useGlobalStore;
