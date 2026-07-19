import { useCallback, useEffect, useState } from 'react'
import type { SynonymGroup } from '@/types/domainKnowledge'
import { listSynonyms } from '@/api/ontologySynonym'
import i18next from '@/locales/i18n'

export interface UseSynonymsResult {
  data: SynonymGroup[]
  total: number
  page: number
  pageSize: number
  loading: boolean
  error: string | null
  refresh: () => void
  setPage: (page: number) => void
}


export function useSynonyms(kbId: string, pageSize = 20): UseSynonymsResult {
  const [data, setData] = useState<SynonymGroup[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    if (!kbId) return
    setLoading(true)
    setError(null)
    listSynonyms(kbId, page, pageSize)
      .then((res) => {
        setData(res.items)
        setTotal(res.total)
      })
      .catch((e: any) => setError(e?.message || i18next.t('common.loadFailed')))
      .finally(() => setLoading(false))
  }, [kbId, page, pageSize])

  useEffect(() => {
    load()
  }, [load])

  return { data, total, page, pageSize, loading, error, refresh: load, setPage }
}
