import { request, getData } from './request'


export interface PlatformUser {
  id: number
  tenant_id: string
  username: string
  display_name: string | null
  email: string | null
  role: string
  status: number
  last_login_at: string | null
  created_at: string | null
  updated_at: string | null
}

export interface PlatformUserListResult {
  total: number
  items: PlatformUser[]
}


export async function listUsers(
  page = 1,
  pageSize = 100,
): Promise<PlatformUserListResult> {
  return getData<PlatformUserListResult>(
    request.get('/platform/users', { params: { page, page_size: pageSize } }),
  )
}
