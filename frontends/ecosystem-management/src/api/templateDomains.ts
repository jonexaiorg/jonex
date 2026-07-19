import apiClient from './client'

export interface TemplateDomain {
  id: string
  name: string
  description?: string
  status: 'active' | 'inactive' | 'archived'
  scenario_count?: number
  created_at: string
  updated_at?: string
}

export async function fetchDomains(
  offset = 0,
  limit = 20,
): Promise<{ items: TemplateDomain[]; total: number; offset: number; limit: number }> {
  const resp = await apiClient.get('/api/v1/ecosystem/templates/domains', {
    params: { offset, limit },
  })
  return resp.data.data
}

export async function createDomain(
  data: { name: string; description?: string; status: string },
): Promise<TemplateDomain> {
  const resp = await apiClient.post('/api/v1/ecosystem/templates/domains', data)
  return resp.data.data
}

export async function updateDomain(
  domainId: string,
  data: { name?: string; description?: string; status?: string },
): Promise<TemplateDomain> {
  const resp = await apiClient.patch(`/api/v1/ecosystem/templates/domains/${domainId}`, data)
  return resp.data.data
}

export async function deleteDomain(domainId: string): Promise<void> {
  await apiClient.delete(`/api/v1/ecosystem/templates/domains/${domainId}`)
}
