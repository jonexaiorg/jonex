import type { KnowledgeSearchHistoryItem } from '../types/knowledgeSearch'

const seedHistory: KnowledgeSearchHistoryItem[] = []

const STORAGE_KEY = 'jonex_core_business_knowledge_search_history_v1'
const MAX_ITEMS = 20

function load(): KnowledgeSearchHistoryItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed) && parsed.length > 0) return parsed
    }
  } catch {

  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(seedHistory))
  return seedHistory
}

function persist(items: KnowledgeSearchHistoryItem[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
}

export function listMockKnowledgeSearchHistory(): KnowledgeSearchHistoryItem[] {
  return load()
}

export function saveMockKnowledgeSearchHistory(
  item: Omit<KnowledgeSearchHistoryItem, 'id' | 'searchedAt'>,
): KnowledgeSearchHistoryItem[] {
  const items = load()
  const keyA = item.domainId ?? 'all'
  const existingIdx = items.findIndex(
    (h) => h.query === item.query && (h.domainId ?? 'all') === keyA,
  )

  const newItem: KnowledgeSearchHistoryItem = {
    ...item,
    id: `history-${Date.now()}`,
    searchedAt: new Date().toISOString(),
  }

  const updated: KnowledgeSearchHistoryItem[] =
    existingIdx >= 0
      ? [newItem, ...items.filter((_, i) => i !== existingIdx)]
      : [newItem, ...items].slice(0, MAX_ITEMS)

  persist(updated)
  return updated
}

export function deleteMockKnowledgeSearchHistory(id: string): KnowledgeSearchHistoryItem[] {
  const updated = load().filter((h) => h.id !== id)
  persist(updated)
  return updated
}

export function clearMockKnowledgeSearchHistory(): KnowledgeSearchHistoryItem[] {
  persist([])
  return []
}
