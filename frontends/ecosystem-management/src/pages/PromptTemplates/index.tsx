import React, { useState, useEffect, useCallback } from 'react'
import { Button, Input, Select, Spin, Result, message, Modal } from 'antd'
import { PlusOutlined, SearchOutlined, GlobalOutlined, AppstoreOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { colors } from '@jonex/platform-theme/tokens'
import {
  listPromptTemplates,
  createPromptTemplate,
  updatePromptTemplate,
  deletePromptTemplate,
  copyPromptTemplate,
  PROMPT_CATEGORIES,
  type PromptTemplateItem,
  type CreatePromptTemplatePayload,
  type UpdatePromptTemplatePayload,
} from '../../api/promptTemplates'
import PromptCard from './PromptCard'
import CreateEditModal from './CreateEditModal'
import VersionModal from './VersionModal'
import './index.css'

type ModalMode = 'create' | 'edit' | 'view'

export default function PromptTemplates() {
  const { t } = useTranslation()

  const [templates, setTemplates] = useState<PromptTemplateItem[]>([])
  const [counts, setCounts] = useState({ system: 0, domain: 0 })
  const [listTotal, setListTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)


  const [scope, setScope] = useState<'system' | 'domain'>('system')
  const [keywordInput, setKeywordInput] = useState('')
  const [keyword, setKeyword] = useState('')
  const [category, setCategory] = useState<string>('')


  const [modalOpen, setModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<ModalMode>('create')
  const [editingTemplate, setEditingTemplate] = useState<PromptTemplateItem | null>(null)


  const [versionModalOpen, setVersionModalOpen] = useState(false)
  const [versionTemplate, setVersionTemplate] = useState<PromptTemplateItem | null>(null)


  const [deletingId, setDeletingId] = useState<string | null>(null)


  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const filters = {
        category: category || undefined,
        keyword: keyword.trim() || undefined,
      }
      const [result, systemResult, domainResult] = await Promise.all([
        listPromptTemplates({
          ...filters,
          scope,
          offset: 0,
          limit: 100,
        }),
        listPromptTemplates({
          ...filters,
          scope: 'system',
          offset: 0,
          limit: 1,
        }),
        listPromptTemplates({
          ...filters,
          scope: 'domain',
          offset: 0,
          limit: 1,
        }),
      ])
      setTemplates(result.items)
      setListTotal(result.total)
      setCounts({ system: systemResult.total, domain: domainResult.total })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('common.loadFailed'))
    } finally {
      setLoading(false)
    }
  }, [scope, category, keyword, t])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const nextKeyword = keywordInput.trim()
      setKeyword(prev => (prev === nextKeyword ? prev : nextKeyword))
    }, 400)

    return () => window.clearTimeout(timer)
  }, [keywordInput])

  useEffect(() => { loadData() }, [loadData])


  const handleCreate = () => {
    setEditingTemplate(null)
    setModalMode('create')
    setModalOpen(true)
  }

  const handleEdit = (id: string) => {
    const tpl = templates.find(t => t.id === id) || null
    setEditingTemplate(tpl)
    setModalMode('edit')
    setModalOpen(true)
  }

  const handleView = (id: string) => {
    const tpl = templates.find(t => t.id === id) || null
    setEditingTemplate(tpl)
    setModalMode('view')
    setModalOpen(true)
  }

  const handleVersion = (id: string) => {
    const tpl = templates.find(t => t.id === id) || null
    setVersionTemplate(tpl)
    setVersionModalOpen(true)
  }

  const handleCopy = async (id: string) => {
    try {
      await copyPromptTemplate(id)
      message.success(t('promptTemplate.copyToTenantSuccess'))
      await loadData()
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('common.operationFailed'))
    }
  }

  const handleDeleteClick = (id: string) => {
    setDeletingId(id)
  }

  const handleDeleteConfirm = async () => {
    if (!deletingId) return
    try {
      await deletePromptTemplate(deletingId)
      message.success(t('promptTemplate.deleteSuccess'))
      setDeletingId(null)
      await loadData()
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('common.deleteFailed'))
    }
  }

  const handleSubmit = async (data: CreatePromptTemplatePayload | UpdatePromptTemplatePayload) => {
    if (modalMode === 'create') {
      await createPromptTemplate(data as CreatePromptTemplatePayload)
      message.success(t('promptTemplate.createSuccess'))
    } else if (editingTemplate) {
      await updatePromptTemplate(editingTemplate.id, data as UpdatePromptTemplatePayload)
      message.success(t('promptTemplate.updateSuccess'))
    }
    await loadData()
  }


  const systemCount = counts.system
  const domainCount = counts.domain



  if (loading && templates.length === 0) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
      <Spin size="large" />
    </div>
  }

  if (error && templates.length === 0) {
    return <Result
      status="error" title={t('common.loadFailed')} subTitle={error}
      extra={<Button type="primary" onClick={loadData}>{t('common.retry')}</Button>}
    />
  }

  return (
    <div className="pt-page">
      { }
      <div className="pt-header">
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: colors.brandDark, margin: 0 }}>
            📋 {t('promptTemplate.title')}
          </h1>
          <div style={{ fontSize: 14, color: '#94a3b8', marginTop: 4 }}>
            {t('promptTemplate.description')}
          </div>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          {t('promptTemplate.create')}
        </Button>
      </div>

      { }
      <div className="pt-toolbar-card">
        <div className="pt-scope-tabs">
          <button
            className={`pt-scope-tab ${scope === 'system' ? 'active' : ''}`}
            onClick={() => setScope('system')}
          >
            <GlobalOutlined /> {t('promptTemplate.systemScope')}
            <span className="pt-tab-count">{systemCount}</span>
          </button>
          <button
            className={`pt-scope-tab ${scope === 'domain' ? 'active' : ''}`}
            onClick={() => setScope('domain')}
          >
            <AppstoreOutlined /> {t('promptTemplate.domainScope')}
            <span className="pt-tab-count">{domainCount}</span>
          </button>
        </div>
      </div>

      { }
      <div className="pt-toolbar-card">
        <div className="pt-search-bar">
          <Input
            prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
            placeholder={t('promptTemplate.searchPlaceholder')}
            value={keywordInput}
            onChange={e => setKeywordInput(e.target.value)}
            allowClear
            style={{ width: 320 }}
          />
          <Select
            value={category || 'all'}
            onChange={(v: string) => setCategory(v === 'all' ? '' : v)}
            style={{ width: 150 }}
          >
            <Select.Option value="all">{t('promptTemplate.allCategories')}</Select.Option>
            {PROMPT_CATEGORIES.map(cat => (
              <Select.Option key={cat} value={cat}>{t(cat)}</Select.Option>
            ))}
          </Select>
          <div style={{ flex: 1 }} />
          <span style={{ fontSize: 13, color: '#94a3b8' }}>
            {t('promptTemplate.countText', { count: listTotal })}
          </span>
        </div>
      </div>

      { }
      {templates.length === 0 ? (
        <div className="pt-empty">
          <div style={{ fontSize: 40, marginBottom: 12, opacity: 0.4 }}>📂</div>
          <div style={{ color: '#94a3b8' }}>
            {scope === 'system' ? t('promptTemplate.noSystemTemplates') : t('promptTemplate.noDomainTemplates')}
          </div>
        </div>
      ) : (
        <div className="pt-grid">
          {templates.map(tpl => (
            <PromptCard
              key={tpl.id}
              template={tpl}
              onEdit={handleEdit}
              onView={handleView}
              onDelete={handleDeleteClick}
              onVersion={handleVersion}
              onCopy={handleCopy}
            />
          ))}
        </div>
      )}

      { }
      <CreateEditModal
        open={modalOpen}
        mode={modalMode}
        template={editingTemplate}
        onClose={() => setModalOpen(false)}
        onSubmit={handleSubmit}
      />

      { }
      <VersionModal
        open={versionModalOpen}
        template={versionTemplate}
        onClose={() => setVersionModalOpen(false)}
        onRollback={loadData}
      />

      { }
      <Modal
        title={t('promptTemplate.delete')}
        open={!!deletingId}
        onOk={handleDeleteConfirm}
        onCancel={() => setDeletingId(null)}
        okText={t('common.confirmDelete')}
        cancelText={t('common.cancel')}
        okButtonProps={{ danger: true }}
      >
        <div style={{ textAlign: 'center', padding: '12px 0' }}>
          <div style={{
            width: 48, height: 48, borderRadius: 12, background: '#fef2f2', color: '#dc2626',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 22, margin: '0 auto 12px',
          }}>
            🗑️
          </div>
          <strong>{t('promptTemplate.deleteConfirm')}</strong>
          <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 13 }}>
            {t('promptTemplate.deleteConfirmDesc')}
          </p>
        </div>
      </Modal>
    </div>
  )
}
