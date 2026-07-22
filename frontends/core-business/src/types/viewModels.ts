export interface DomainSpace {
  id: string
  name: string
  description: string
  status: 'active' | 'inactive'
  docCount: number
  knowledgeCount: number
  createdAt: string
  icon?: string
}

export interface DomainPermission {
  id: string
  username: string
  displayName: string
  role: 'admin' | 'editor' | 'viewer'
  avatar?: string
}

export interface GraphInstance {
  id: string
  name: string
  type: string
  properties: { key: string; value: string }[]
  relations: { id: string; name: string; target: string }[]
  sourceDocs: string[]
}

export interface GraphRelation {
  id: string
  name: string
  sourceEntity: string
  targetEntity: string
  type: string
  properties: { key: string; value: string }[]
  sourceSnippets: string[]
}
