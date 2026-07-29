export type AccessType = 'api' | 'api_push' | 'storage' | 'file' | 'mqtt';

/** 接入目录项（来自 /ecosystem/data-access-methods） */
export interface AccessMethodItem {
  id: string;
  name: string;
  accessType: AccessType;
  description?: string;
  status: string;
}

/** 数据源实例（后端 snake → 前端 camel） */
export interface DataSourceInstance {
  id: string;
  knowledgeBaseId: string;
  accessMethodId?: string;
  accessType: AccessType;
  name: string;
  configJson: Record<string, any>;
  syncMode: 'manual' | 'scheduled';
  status: 'active' | 'paused' | 'error';
  lastSyncAt?: string | null;
  lastSyncStatus?: string | null;
  lastSyncMessage?: string | null;
  documentCount: number;
  createdAt?: string | null;
  updatedAt?: string | null;
  // 仅创建 api_push / 重置 key 时一次性返回
  ingestKey?: string;
  ingestUrl?: string;
}

export interface CreateDataSourcePayload {
  knowledge_base_id: string;
  access_method_id?: string;
  access_type: AccessType;
  name: string;
  config_json: Record<string, any>;
  sync_mode?: 'manual' | 'scheduled';
}

export interface TestResult {
  ok: boolean;
  message: string;
  sample_count?: number;
}

export interface SyncResult {
  created: number;
  failed: number;
  message?: string | null;
}

export interface DataSourceDoc {
  id: string;
  name: string;
  type: string;
  size: string;
  uploadTime: string;
  status: string;
}
