import { makeAutoObservable, runInAction } from 'mobx';
import { getItem, setItem } from '@/utils/storage';
import { listSpaces } from '@/api/domainSpace';
import type { DomainSpace } from '@/types/domainSpace';
import { persistSpaceId, readPersistedSpaceId } from '@jonex/shell-sdk';

interface SetCurrentSpaceIdOpts {
  persist?: boolean;
  broadcast?: boolean;
}

class GlobalStore {
  userInfo: Record<string, unknown> | null = getItem<Record<string, unknown>>('userInfo') || null;

  // ── 领域空间状态 ──
  spaces: DomainSpace[] = [];
  spacesLoaded = false;
  spacesLoading = false;
  currentSpaceId: string | null = null;

  constructor() {
    makeAutoObservable(this);
  }

  /** 派生：当前空间对象 */
  get currentSpace(): DomainSpace | undefined {
    if (!this.currentSpaceId) return undefined;
    return this.spaces.find((s) => s.id === this.currentSpaceId);
  }

  // ── 全局设置 ──

  setUserInfo = (data: Record<string, unknown> | null) => {
    this.userInfo = data;
    setItem('userInfo', data);
  };

  // ── 领域空间动作 ──

  /**
   * 设置当前空间
   * @param opts.persist 写 localStorage（默认 true）
   * @param opts.broadcast 派发 window 事件（默认 false，防回环）
   */
  setCurrentSpaceId = (id: string | null, opts: SetCurrentSpaceIdOpts = {}) => {
    const { persist = true, broadcast = false } = opts;
    this.currentSpaceId = id;
    if (persist) {
      persistSpaceId(id);
    }
    if (broadcast) {
      // 动态 import 避免循环依赖（emitSpaceChanged 来自 shell-sdk）
      import('@jonex/shell-sdk').then(({ emitSpaceChanged }) => emitSpaceChanged(id));
    }
  };

  /** 替换空间列表 + 校验当前空间 */
  setSpaces = (list: DomainSpace[]) => {
    this.spaces = list;
    // 当前空间不在新列表中则回落
    if (this.currentSpaceId && !list.find((s) => s.id === this.currentSpaceId)) {
      const fallbackId = list[0]?.id ?? null;
      this.setCurrentSpaceId(fallbackId, {
        persist: true,
        broadcast: false,
      });
    }
    this.spacesLoaded = true;
  };

  /** 幂等加载空间列表（首次初始化） */
  loadSpaces = async () => {
    if (this.spacesLoading || this.spacesLoaded) return;
    this.spacesLoading = true;
    try {
      const result = await listSpaces(0, 100);
      const data = result.items;
      runInAction(() => {
        // 初始化：localStorage > 首个
        if (!this.currentSpaceId) {
          const persisted = readPersistedSpaceId();
          const valid = persisted && data.find((s) => s.id === persisted);
          this.currentSpaceId = valid ? persisted : (data[0]?.id ?? null);
          persistSpaceId(this.currentSpaceId);
        }
        this.setSpaces(data);
      });
    } finally {
      runInAction(() => {
        this.spacesLoading = false;
      });
    }
  };

  /** 强制重拉空间列表（CRUD 后或收到失效事件） */
  refreshSpaces = async () => {
    this.spacesLoading = true;
    try {
      const result = await listSpaces(0, 100);
      const data = result.items;
      runInAction(() => {
        this.setSpaces(data);
      });
    } finally {
      runInAction(() => {
        this.spacesLoading = false;
        this.spacesLoaded = true;
      });
    }
  };
}

export default new GlobalStore();
