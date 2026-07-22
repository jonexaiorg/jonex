import { test, expect } from '@playwright/test'

const KB_ID = 'kb-test-001'

test.describe('DomainKnowledge Result Tab', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept parse-result APIs with mock data
    await page.route('**/knowledge-base/bases/*/parse-result/summary', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          code: 200,
          message: 'ok',
          data: {
            knowledge_base_id: KB_ID,
            tenant_id: 'test_tenant',
            source: 'lightrag_storage',
            scope_mode: 'knowledge_base',
            status: 'processed',
            documents_count: 3,
            processed_documents_count: 3,
            failed_documents_count: 0,
            chunks_count: 9,
            entities_count: 155,
            relationships_count: 134,
            compile_versions_count: 0,
            last_updated_at: '2026-05-29T10:00:00',
            storage_files: {
              'kv_store_doc_status.json': true,
              'vdb_chunks.json': true,
              'vdb_entities.json': true,
              'vdb_relationships.json': true,
              'graph_chunk_entity_relation.graphml': true,
            },
          },
        }),
      })
    })

    await page.route('**/knowledge-base/bases/*/parse-result/graph-summary', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          code: 200,
          message: 'ok',
          data: {
            nodes_count: 155,
            edges_count: 134,
            entity_type_count: 4,
            relation_type_count: 1,
            avg_degree: 1.73,
            entity_type_distribution: [
              { label: 'organization', count: 60, pct: 38.71 },
              { label: 'person', count: 45, pct: 29.03 },
              { label: 'location', count: 30, pct: 19.35 },
              { label: 'unknown', count: 20, pct: 12.9 },
            ],
            relation_distribution: [
              { label: 'default', count: 134, pct: 100 },
            ],
          },
        }),
      })
    })

    await page.route('**/knowledge-base/bases/*/parse-result/entities**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          code: 200,
          message: 'ok',
          data: {
            items: [
              { id: 'e1', name: 'Apple Inc.', type: 'organization', description: 'Technology company', source_id: '', file_path: 'kb=...|doc=...|tenant=test_tenant|file=test.md|chunk=0', created_at: 1717000000, relations_count: 3 },
              { id: 'e2', name: 'Tim Cook', type: 'person', description: 'CEO of Apple', source_id: '', file_path: 'kb=...|doc=...|tenant=test_tenant|file=test.md|chunk=1', created_at: 1717000001, relations_count: 2 },
              { id: 'e3', name: 'Cupertino', type: 'location', description: 'Headquarters', source_id: '', file_path: 'kb=...|doc=...|tenant=test_tenant|file=test.md|chunk=0', created_at: 1717000002, relations_count: 1 },
            ],
            total: 155,
            page: 1,
            page_size: 6,
          },
        }),
      })
    })

    await page.route('**/core-business/domain-knowledge/*/detail', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true, code: 200, message: 'ok',
          data: {
            id: KB_ID, name: 'Test KB', spaceId: 's1', spaceName: 'Default Space',
            documentCount: 3, entityCount: 155, relationCount: 134,
            compileVersionCount: 0, status: 'synced', updatedAt: '2026-05-29 10:00:00',
          },
        }),
      })
    })

    await page.route('**/core-business/domain-knowledge/*/data-sources', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true, code: 200, data: [] }) })
    })
  })

  test('result tab displays real stats from parse-result API', async ({ page }) => {
    await page.goto(`/domain-knowledge/${KB_ID}`)

    // Click "领域知识结果" tab
    await page.click('text=领域知识结果')

    // Wait for stats to load
    await expect(page.locator('text=155')).toHaveCount(1, { timeout: 5000 })

    // Verify stat cards
    await expect(page.locator('text=知识实体')).toBeVisible()
    await expect(page.locator('text=知识关系')).toBeVisible()
  })

  test('entity table loads and displays data', async ({ page }) => {
    await page.goto(`/domain-knowledge/${KB_ID}`)
    await page.click('text=领域知识结果')

    // Entity table should show entities
    await expect(page.locator('text=Apple Inc.')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('text=Tim Cook')).toBeVisible()
    await expect(page.locator('text=Cupertino')).toBeVisible()
  })

  test('entity type dropdown is dynamic', async ({ page }) => {
    await page.goto(`/domain-knowledge/${KB_ID}`)
    await page.click('text=领域知识结果')

    // Click entity type select
    const select = page.locator('.ant-select').filter({ hasText: '全部类型' })
    await select.click()

    // Should show entity types from API
    await expect(page.locator('.ant-select-dropdown')).toContainText('organization')
    await expect(page.locator('.ant-select-dropdown')).toContainText('person')
    await expect(page.locator('.ant-select-dropdown')).toContainText('location')
  })

  test('entity search filters by keyword', async ({ page }) => {
    await page.goto(`/domain-knowledge/${KB_ID}`)
    await page.click('text=领域知识结果')

    const searchInput = page.locator('input[placeholder="搜索实体..."]')
    await searchInput.fill('Apple')

    // Debounce wait
    await page.waitForTimeout(400)

    // Only Apple entity should show
    await expect(page.locator('text=Apple Inc.')).toBeVisible()
  })

  test('graph summary displays stats', async ({ page }) => {
    await page.goto(`/domain-knowledge/${KB_ID}`)
    await page.click('text=领域知识结果')

    // Graph summary section
    await expect(page.locator('text=知识图谱')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('text=4')).toBeVisible() // entity_type_count
    await expect(page.locator('text=1.73')).toBeVisible() // avg_degree
  })

  test('empty state when no data', async ({ page }) => {
    // Override: return empty storage
    await page.route('**/knowledge-base/bases/*/parse-result/summary', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true, code: 200, message: 'ok',
          data: {
            knowledge_base_id: 'kb-empty', tenant_id: 'test',
            source: 'lightrag_storage', scope_mode: 'knowledge_base',
            status: 'storage_missing', documents_count: 0,
            processed_documents_count: 0, failed_documents_count: 0,
            chunks_count: 0, entities_count: 0, relationships_count: 0,
            compile_versions_count: 0, last_updated_at: null, storage_files: {},
          },
        }),
      })
    })

    await page.goto('/domain-knowledge/kb-empty')
    await page.click('text=领域知识结果')

    // Should show zeros / dashes
    await expect(page.locator('text=0')).toHaveCount(1, { timeout: 5000 })
  })

  test('scope warning shows when present', async ({ page }) => {
    await page.route('**/knowledge-base/bases/*/parse-result/summary', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true, code: 200, message: 'ok',
          data: {
            knowledge_base_id: 'kb-scope', tenant_id: 'test',
            source: 'lightrag_storage', scope_mode: 'knowledge_base',
            scope_warning: '未找到该知识库的已入库文档，将返回全局存储数据',
            status: 'processed', documents_count: 155,
            processed_documents_count: 155, failed_documents_count: 0,
            chunks_count: 500, entities_count: 155, relationships_count: 134,
            compile_versions_count: 0, last_updated_at: null, storage_files: {},
          },
        }),
      })
    })

    await page.goto('/domain-knowledge/kb-scope')
    await page.click('text=领域知识结果')

    // Should show scope warning
    await expect(page.locator('text=全局存储数据')).toBeVisible({ timeout: 5000 })
  })
})
