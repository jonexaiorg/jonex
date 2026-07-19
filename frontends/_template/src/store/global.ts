import { makeAutoObservable } from 'mobx'
import { getItem, setItem } from '@/utils/storage'
import { LANGUAGE_STORAGE_KEY } from '@jonex/shell-sdk'

class GlobalStore {
  locale: string = getItem<string>(LANGUAGE_STORAGE_KEY) || 'en'
  userInfo: Record<string, unknown> | null = getItem<Record<string, unknown>>('userInfo') || null

  constructor() {
    makeAutoObservable(this)
  }

  setLocale = (lang: string) => {
    this.locale = lang
    setItem(LANGUAGE_STORAGE_KEY, lang)
  }

  setUserInfo = (data: Record<string, unknown> | null) => {
    this.userInfo = data
    setItem('userInfo', data)
  }
}

export default new GlobalStore()
