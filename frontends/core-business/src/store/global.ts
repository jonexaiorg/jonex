import { makeAutoObservable, runInAction } from 'mobx'
import { getItem, setItem } from '@/utils/storage'
import { listSpaces } from '@/api/domainSpace'
import type { DomainSpace } from '@/types/domainSpace'
import {
  LANGUAGE_STORAGE_KEY,
  persistSpaceId,
  readPersistedSpaceId,
} from '@jonex/shell-sdk'

interface SetCurrentSpaceIdOpts {
  persist?: boolean
  broadcast?: boolean
}

class GlobalStore {
  locale: string = getItem<string>(LANGUAGE_STORAGE_KEY) || 'en'
  userInfo: Record<string, unknown> | null =
    getItem<Record<string, unknown>>('userInfo') || null


  spaces: DomainSpace[] = []
  spacesLoaded = false
  spacesLoading = false
  currentSpaceId: string | null = null

  constructor() {
    makeAutoObservable(this)
  }


  get currentSpace(): DomainSpace | undefined {
    if (!this.currentSpaceId) return undefined
    return this.spaces.find((s) => s.id === this.currentSpaceId)
  }



  setLocale = (lang: string) => {
    this.locale = lang
    setItem(LANGUAGE_STORAGE_KEY, lang)
  }

  setUserInfo = (data: Record<string, unknown> | null) => {
    this.userInfo = data
    setItem('userInfo', data)
  }








  setCurrentSpaceId = (
    id: string | null,
    opts: SetCurrentSpaceIdOpts = {},
  ) => {
    const { persist = true, broadcast = false } = opts
    this.currentSpaceId = id
    if (persist) {
      persistSpaceId(id)
    }
    if (broadcast) {

      import('@jonex/shell-sdk').then(({ emitSpaceChanged }) =>
        emitSpaceChanged(id),
      )
    }
  }


  setSpaces = (list: DomainSpace[]) => {
    this.spaces = list

    if (
      this.currentSpaceId &&
      !list.find((s) => s.id === this.currentSpaceId)
    ) {
      const fallbackId = list[0]?.id ?? null
      this.setCurrentSpaceId(fallbackId, {
        persist: true,
        broadcast: false,
      })
    }
    this.spacesLoaded = true
  }


  loadSpaces = async () => {
    if (this.spacesLoading || this.spacesLoaded) return
    this.spacesLoading = true
    try {
      const result = await listSpaces(0, 100)
      const data = result.items
      runInAction(() => {

        if (!this.currentSpaceId) {
          const persisted = readPersistedSpaceId()
          const valid =
            persisted && data.find((s) => s.id === persisted)
          this.currentSpaceId = valid
            ? persisted
            : data[0]?.id ?? null
          persistSpaceId(this.currentSpaceId)
        }
        this.setSpaces(data)
      })
    } finally {
      runInAction(() => {
        this.spacesLoading = false
      })
    }
  }


  refreshSpaces = async () => {
    this.spacesLoading = true
    try {
      const result = await listSpaces(0, 100)
      const data = result.items
      runInAction(() => {
        this.setSpaces(data)
      })
    } finally {
      runInAction(() => {
        this.spacesLoading = false
        this.spacesLoaded = true
      })
    }
  }
}

export default new GlobalStore()
