import { request, getData } from './request'
import type {
  DomainServiceItem,
  DomainServiceListResult,
  DomainServiceFormData,
  ServiceApiKeyItem,
} from '../types/domainService'


export async function listServices(
  space_id?: string,
  offset = 0,
  limit = 100,
): Promise<DomainServiceListResult> {
  const params: Record<string, string | number> = { offset, limit }
  if (space_id) params.space_id = space_id
  return getData<DomainServiceListResult>(
    request.get('/knowledge-base/services', { params }),
  )
}


export async function createService(data: DomainServiceFormData): Promise<DomainServiceItem> {
  return getData<DomainServiceItem>(request.post('/knowledge-base/services', data))
}


export async function getService(serviceId: string): Promise<DomainServiceItem> {
  return getData<DomainServiceItem>(request.get(`/knowledge-base/services/${serviceId}`))
}


export async function updateService(
  serviceId: string,
  data: Partial<DomainServiceFormData>,
): Promise<DomainServiceItem> {
  return getData<DomainServiceItem>(
    request.patch(`/knowledge-base/services/${serviceId}`, data),
  )
}


export async function deleteService(serviceId: string): Promise<boolean> {
  await getData(request.delete(`/knowledge-base/services/${serviceId}`))
  return true
}


export async function listServiceApiKeys(
  serviceId: string,
): Promise<{ items: ServiceApiKeyItem[]; total: number }> {
  return getData(request.get(`/knowledge-base/services/${serviceId}/api-keys`))
}


export async function createServiceApiKey(
  serviceId: string,
  data?: { key_prefix?: string; expires_in_days?: number },
): Promise<ServiceApiKeyItem> {
  return getData(request.post(`/knowledge-base/services/${serviceId}/api-keys`, data || {}))
}


export async function deleteServiceApiKey(serviceId: string, keyId: string): Promise<boolean> {
  return getData(request.delete(`/knowledge-base/services/${serviceId}/api-keys/${keyId}`))
}


export async function rotateApiKey(serviceId: string): Promise<{ api_key: string }> {
  return getData(request.post(`/knowledge-base/services/${serviceId}/rotate-api-key`))
}


export async function getServicePermissions(
  serviceId: string,
): Promise<{ permissions: Array<{ id?: string; user_id: string; role: string }> }> {
  return getData(request.get(`/knowledge-base/services/${serviceId}/permissions`))
}


export async function setServicePermissions(
  serviceId: string,
  permissions: Array<{ user_id: string; role: string }>,
): Promise<boolean> {
  return getData(
    request.put(`/knowledge-base/services/${serviceId}/permissions`, { permissions }),
  )
}