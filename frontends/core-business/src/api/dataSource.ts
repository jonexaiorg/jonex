import { request, getData } from './request'
import type {
  AccessMethodItem,
  CreateDataSourcePayload,
  DataSourceInstance,
  SyncResult,
  TestResult,
} from '@/types/dataSource'
import type { ManualDocItem } from '@/types/domainKnowledge'

interface BackendDataSource {
  id: string
  tenant_id: string
  knowledge_base_id: string
  access_method_id?: string | null
  access_type: string
  name: string
  config_json: Record<string, any>
  sync_mode: string
  status: string
  last_sync_at?: string | null
  last_sync_status?: string | null
  last_sync_message?: string | null
  document_count: number
  created_at?: string | null
  updated_at?: string | null
  ingest_key?: string
  ingest_url?: string
}

function mapDataSource(b: BackendDataSource): DataSourceInstance {
  return {
    id: b.id,
    knowledgeBaseId: b.knowledge_base_id,
    accessMethodId: b.access_method_id || undefined,
    accessType: b.access_type as DataSourceInstance['accessType'],
    name: b.name,
    configJson: b.config_json || {},
    syncMode: (b.sync_mode as DataSourceInstance['syncMode']) || 'manual',
    status: (b.status as DataSourceInstance['status']) || 'active',
    lastSyncAt: b.last_sync_at,
    lastSyncStatus: b.last_sync_status,
    lastSyncMessage: b.last_sync_message,
    documentCount: b.document_count || 0,
    createdAt: b.created_at,
    updatedAt: b.updated_at,
    ingestKey: b.ingest_key,
    ingestUrl: b.ingest_url,
  }
}


export async function listAccessMethods(): Promise<AccessMethodItem[]> {
  const res = await getData<{ items: any[] }>(
    request.get('/ecosystem/data-access-methods', { params: { offset: 0, limit: 100 } }),
  )
  return (res.items || [])
    .filter((i) => i.status === 'active')
    .map((i) => ({
      id: i.id,
      name: i.name,
      accessType: i.access_type,
      description: i.description,
      status: i.status,
    }))
}


export async function listDataSources(kbId: string): Promise<DataSourceInstance[]> {
  const res = await getData<{ items: BackendDataSource[]; total: number }>(
    request.get('/knowledge-base/data-sources', { params: { knowledge_base_id: kbId } }),
  )
  return (res.items || []).map(mapDataSource)
}

export async function getDataSource(dsId: string): Promise<DataSourceInstance> {
  return mapDataSource(await getData<BackendDataSource>(request.get(`/knowledge-base/data-sources/${dsId}`)))
}

export async function createDataSource(payload: CreateDataSourcePayload): Promise<DataSourceInstance> {
  return mapDataSource(await getData<BackendDataSource>(request.post('/knowledge-base/data-sources', payload)))
}

export async function updateDataSource(
  dsId: string,
  payload: Partial<CreateDataSourcePayload> & { status?: string },
): Promise<DataSourceInstance> {
  return mapDataSource(await getData<BackendDataSource>(request.patch(`/knowledge-base/data-sources/${dsId}`, payload)))
}

export async function deleteDataSource(dsId: string): Promise<void> {
  await getData(request.delete(`/knowledge-base/data-sources/${dsId}`))
}

export async function testDataSource(dsId: string): Promise<TestResult> {
  return getData<TestResult>(request.post(`/knowledge-base/data-sources/${dsId}/test`))
}

export async function syncDataSource(dsId: string): Promise<SyncResult> {
  return getData<SyncResult>(request.post(`/knowledge-base/data-sources/${dsId}/sync`))
}

export async function resetIngestKey(dsId: string): Promise<DataSourceInstance> {
  return mapDataSource(
    await getData<BackendDataSource>(request.post(`/knowledge-base/data-sources/${dsId}/reset-ingest-key`)),
  )
}



export async function listDataSourceDocuments(kbId: string, dsId: string): Promise<ManualDocItem[]> {
  const res = await getData<{ items: any[] }>(
    request.get('/knowledge-base/documents', { params: { knowledge_base_id: kbId, page: 1, page_size: 100 } }),
  )
  const fmtSize = (b?: number) =>
    typeof b === 'number' ? (b >= 1048576 ? `${(b / 1048576).toFixed(1)} MB` : `${Math.round(b / 1024)} KB`) : '-'
  const statusText = (s: string) =>
    s === 'ready' ? '入库·解析·编译' : s === 'parsing' ? '入库·解析中' : s === 'pending' ? '入库' : s
  return (res.items || [])
    .filter((d) => (d.metadata || {}).data_source_id === dsId)
    .map((d) => {
      const meta = d.metadata || {}
      return {
        id: d.id,
        name: d.file_name,
        type: ((d.file_name || '').split('.').pop() || '').toUpperCase(),
        size: fmtSize(d.file_size),
        uploader: (meta.uploader as string) || 'system',
        uploadTime: (d.created_at || '').replace('T', ' ').slice(0, 19),
        status: statusText(d.status),
        knowledgeBaseId: kbId,
      }
    })
}
