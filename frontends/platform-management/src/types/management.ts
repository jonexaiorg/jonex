export interface DataAccessMethod {
  id: string
  name: string
  type: 'file' | 'api' | 'storage' | 'database'
  description: string
  enabled: boolean
  configUrl?: string
}

export interface ParserInfo {
  id: string
  name: string
  version: string
  fileTypes: string[]
  status: 'active' | 'inactive' | 'error'
  description: string
}

export interface CompileTask {
  id: string
  name: string
  type: string
  status: 'running' | 'completed' | 'failed' | 'pending'
  entityCount: number
  relationCount: number
  chunkCount: number
  updatedAt: string
}
