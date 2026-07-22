import { makeAutoObservable } from 'mobx'
import { getItem, setItem } from '@/utils/storage'

class GlobalStore {
  locale: string = getItem<string>('locale') || 'zh'
  userInfo: Record<string, unknown> | null = getItem<Record<string, unknown>>('userInfo') || null

  constructor() {
    makeAutoObservable(this)
  }

  setLocale = (lang: string) => {
    this.locale = lang
    setItem('locale', lang)
  }

  setUserInfo = (data: Record<string, unknown> | null) => {
    this.userInfo = data
    setItem('userInfo', data)
  }
}

export default new GlobalStore()
