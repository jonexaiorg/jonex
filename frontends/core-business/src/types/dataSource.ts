export type AccessType = 'api' | 'api_push' | 'storage' | 'file'


export interface AccessMethodItem {
  id: string
  name: string
  accessType: AccessType
  description?: string
  status: string
}


export interface DataSourceInstance {
  id: string
  knowledgeBaseId: string
  accessMethodId?: string
  accessType: AccessType
  name: string
  configJson: Record<string, any>
  syncMode: 'manual' | 'scheduled'
  status: 'active' | 'paused' | 'error'
  lastSyncAt?: string | null
  lastSyncStatus?: string | null
  lastSyncMessage?: string | null
  documentCount: number
  createdAt?: string | null
  updatedAt?: string | null

  ingestKey?: string
  ingestUrl?: string
}

export interface CreateDataSourcePayload {
  knowledge_base_id: string
  access_method_id?: string
  access_type: AccessType
  name: string
  config_json: Record<string, any>
  sync_mode?: 'manual' | 'scheduled'
}

export interface TestResult {
  ok: boolean
  message: string
  sample_count?: number
}

export interface SyncResult {
  created: number
  failed: number
  message?: string | null
}

export interface DataSourceDoc {
  id: string
  name: string
  type: string
  size: string
  uploadTime: string
  status: string
}
