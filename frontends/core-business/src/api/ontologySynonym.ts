import type { SynonymGroup, SynonymListResult, SynonymImportResult } from '@/types/domainKnowledge'
import { request, getData, postData } from './request'


interface BackendSynonym {
  id: string
  knowledge_base_id: string
  terms: string[]
  canonical?: string | null
  created_at?: string | null
  updated_at?: string | null
}
interface BackendSynonymList {
  items: BackendSynonym[]
  total: number
  page: number
  page_size: number
}
interface BackendSynonymImport {
  created: number
  skipped: number
  failed: { index: number; reason: string }[]
}

function mapSynonym(b: BackendSynonym): SynonymGroup {
  return {
    id: b.id,
    knowledgeBaseId: b.knowledge_base_id,
    terms: b.terms || [],
    canonical: b.canonical ?? null,
    createdAt: b.created_at ?? null,
    updatedAt: b.updated_at ?? null,
  }
}

const BASE = '/knowledge-base/ontology/synonyms'

export async function listSynonyms(
  kbId: string,
  page = 1,
  pageSize = 20,
): Promise<SynonymListResult> {
  const res = await getData<BackendSynonymList>(
    request.get(BASE, { params: { knowledge_base_id: kbId, page, page_size: pageSize } }),
  )
  return {
    items: (res.items || []).map(mapSynonym),
    total: res.total ?? 0,
    page: res.page ?? page,
    pageSize: res.page_size ?? pageSize,
  }
}

export async function createSynonym(
  kbId: string,
  terms: string[],
  canonical?: string,
): Promise<SynonymGroup> {
  const res = await postData<BackendSynonym>(BASE, {
    knowledge_base_id: kbId,
    terms,
    ...(canonical ? { canonical } : {}),
  })
  return mapSynonym(res)
}

export async function updateSynonym(
  synonymId: string,
  terms: string[],
  canonical?: string,
): Promise<SynonymGroup> {
  const res = await getData<BackendSynonym>(
    request.patch(`${BASE}/${synonymId}`, {
      terms,
      ...(canonical ? { canonical } : {}),
    }),
  )
  return mapSynonym(res)
}

export async function deleteSynonym(synonymId: string): Promise<void> {
  await getData(request.delete(`${BASE}/${synonymId}`))
}

export async function importSynonyms(
  kbId: string,
  groups: string[][],
): Promise<SynonymImportResult> {
  const res = await postData<BackendSynonymImport>(`${BASE}/import`, {
    knowledge_base_id: kbId,
    groups,
  })
  return {
    created: res.created ?? 0,
    skipped: res.skipped ?? 0,
    failed: res.failed || [],
  }
}


export async function exportAllSynonyms(kbId: string): Promise<SynonymGroup[]> {
  const pageSize = 200
  let page = 1
  const all: SynonymGroup[] = []

  while (true) {
    const res = await listSynonyms(kbId, page, pageSize)
    all.push(...res.items)
    if (all.length >= res.total || res.items.length === 0) break
    page += 1
  }
  return all
}
