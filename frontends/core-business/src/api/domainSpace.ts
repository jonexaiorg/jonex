import { request, getData } from './request'
import type {
  DomainSpace,
  DomainSpaceFormData,
  DomainSpaceListResult,
  SpacePermission,
} from '../types/domainSpace'


export async function listSpaces(
  offset = 0,
  limit = 50,
): Promise<DomainSpaceListResult> {
  return getData<DomainSpaceListResult>(
    request.get('/knowledge-base/spaces', { params: { offset, limit } }),
  )
}


export async function getSpace(spaceId: string): Promise<DomainSpace> {
  return getData<DomainSpace>(request.get(`/knowledge-base/spaces/${spaceId}`))
}


export async function createSpace(data: DomainSpaceFormData): Promise<DomainSpace> {
  return getData<DomainSpace>(request.post('/knowledge-base/spaces', data))
}


export async function updateSpace(
  spaceId: string,
  data: Partial<DomainSpaceFormData>,
): Promise<DomainSpace> {
  return getData<DomainSpace>(
    request.patch(`/knowledge-base/spaces/${spaceId}`, data),
  )
}


export async function deleteSpace(spaceId: string): Promise<void> {
  await getData(request.delete(`/knowledge-base/spaces/${spaceId}`))
}


export async function getSpacePermissions(
  spaceId: string,
): Promise<SpacePermission[]> {
  const result = await getData<{ permissions: SpacePermission[] }>(
    request.get(`/knowledge-base/spaces/${spaceId}/permissions`),
  )
  return result.permissions ?? []
}


export async function updateSpacePermissions(
  spaceId: string,
  permissions: { user_id: string; role: string }[],
): Promise<void> {
  await getData(
    request.put(`/knowledge-base/spaces/${spaceId}/permissions`, { permissions }),
  )
}