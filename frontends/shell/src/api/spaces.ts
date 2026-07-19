import { apiClient } from './auth'

interface ApiEnvelope<T> {
  success: boolean
  code: number
  message: string
  data: T
}

export interface ShellSpaceItem {
  id: string
  name: string
}

export async function fetchSpaces(): Promise<ShellSpaceItem[]> {
  const resp = await apiClient.get<
    ApiEnvelope<{ items: ShellSpaceItem[]; total: number }>
  >('/api/v1/knowledge-base/spaces', { params: { limit: 100 } })

  const envelope = resp.data
  if (!envelope.success) {
    throw new Error(envelope.message || '获取空间列表失败')
  }
  return envelope.data.items || []
}
