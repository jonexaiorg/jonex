export interface Scenario {
  id: string
  name: string
  industry: string
  description: string
  useCases: string[]
  maturity: 'production' | 'pilot' | 'planning'
  adapterCount: number
}

export interface Skill {
  id: string
  name: string
  category: string
  description: string
  status: 'enabled' | 'disabled' | 'draft'
  version: string
  updatedAt: string
}

export interface TemplateDomain {
  id: string
  name: string
  industry: string
  description: string
  usageCount: number
  status: 'published' | 'draft'
  updatedAt: string
}

export interface TemplateScenario {
  id: string
  domainId: string
  domainName: string
  name: string
  description: string
  objectCount: number
  relationCount: number
  status: 'published' | 'draft'
}

export interface TemplateObject {
  id: string
  name: string
  domainId: string
  domainName: string
  fields: { name: string; type: string; required: boolean }[]
  status: 'active' | 'draft'
}

export interface TemplateRelation {
  id: string
  name: string
  sourceObject: string
  targetObject: string
  relationType: string
  constraints: string
}
