import React, { useState, useEffect, useCallback } from 'react'
import { Input, Button, Tag, Modal, Spin, Result, message } from 'antd'
import { useTranslation } from 'react-i18next'
import {
  SearchOutlined, PlusOutlined, PlayCircleOutlined, SettingOutlined,
  RobotOutlined, CodepenOutlined, BlockOutlined, SortDescendingOutlined,
} from '@ant-design/icons'
import {
  listProviders, createProvider, updateProvider, testProvider,
  type ModelProviderItem, type SaveProviderPayload,
} from '../../api/modelProviders'

const PROVIDER_TYPE_LABELS: Record<string, string> = {
  llm: 'LLM',
  embedding: 'Embedding',
  reranker: 'Reranker',
}

const ICON_CONFIG: { icon: React.ReactNode; color: string }[] = [
  { icon: <RobotOutlined />, color: '#10b981' },
  { icon: <CodepenOutlined />, color: '#8b5cf6' },
  { icon: <BlockOutlined />, color: '#3b82f6' },
  { icon: <SortDescendingOutlined />, color: '#f59e0b' },
]

function fmtLatency(ms: number | null): string {
  if (ms === null || ms === undefined) return '-'
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
}

function fmtCount(n: number | null): string {
  if (n === null || n === undefined) return '-'
  return n.toLocaleString()
}

export default function ModelAdapterPage() {
  const { t } = useTranslation('business')
  const [providers, setProviders] = useState<ModelProviderItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<ModelProviderItem | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState({ name: '', provider_type: 'llm', endpoint: '', model_name: '' })

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await listProviders(0, 100)
      setProviders(result.items)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('common.loadFailed'))
    } finally { setLoading(false) }
  }, [t])

  useEffect(() => { load() }, [load])

  const filtered = providers.filter((p) => {
    if (!search) return true
    const q = search.toLowerCase()
    return p.name.toLowerCase().includes(q) || (p.model_name || '').toLowerCase().includes(q)
  })

  const openCreate = () => {
    setEditing(null)
    setForm({ name: '', provider_type: 'llm', endpoint: '', model_name: '' })
    setModalOpen(true)
  }

  const openEdit = (p: ModelProviderItem) => {
    setEditing(p)
    setForm({ name: p.name, provider_type: p.provider_type, endpoint: p.endpoint || '', model_name: p.model_name || '' })
    setModalOpen(true)
  }

  const handleSave = async () => {
    if (!form.name) { message.warning(t('modelAdapter.nameRequired')); return }
    setSubmitting(true)
    try {
      const payload: SaveProviderPayload = {
        name: form.name,
        provider_type: form.provider_type,
        endpoint: form.endpoint || undefined,
        model_name: form.model_name || undefined,
      }
      if (editing) {
        await updateProvider(editing.id, payload)
        message.success(t('common.updatedSuccess'))
      } else {
        await createProvider(payload)
        message.success(t('common.createdSuccess'))
      }
      setModalOpen(false)
      await load()
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('common.saveFailed'))
    } finally { setSubmitting(false) }
  }

  const handleTest = async (id: string) => {
    try {
      const result = await testProvider(id)
      message.success(result.message || t('dataAccess.testSuccess'))
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('dataAccess.testFailed'))
    }
  }

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}><Spin size="large" /></div>
  }

  if (error) {
    return <Result status="error" title={t('common.loadFailed')} subTitle={error} extra={<Button type="primary" onClick={load}>{t('common.retry')}</Button>} />
  }

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('modelAdapter.title')}</h1>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, marginTop: 8 }}>
        <Input prefix={<SearchOutlined />} placeholder={t('modelAdapter.searchPlaceholder')} value={search} onChange={(e) => setSearch(e.target.value)} allowClear style={{ width: 240 }} />
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 13, color: '#64748b' }}>{t('common.totalPage', { total: filtered.length })}</span>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>{t('modelAdapter.addProvider')}</Button>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="yx-empty-state">
          <p>{t('modelAdapter.noProviders')}</p>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>{t('modelAdapter.addProvider')}</Button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 20 }}>
          {filtered.map((p, idx) => {
            const iconCfg = ICON_CONFIG[idx % ICON_CONFIG.length]
            return (
              <div key={p.id} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 12, padding: 24 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                  <div style={{ width: 48, height: 48, borderRadius: 12, background: iconCfg.color, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, color: '#fff' }}>{iconCfg.icon}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: 16 }}>{p.name}</div>
                    <div style={{ fontSize: 12, color: '#94a3b8' }}>{PROVIDER_TYPE_LABELS[p.provider_type] || p.provider_type} · {p.model_type || '-'}</div>
                  </div>
                  <Tag color={p.status === 'active' ? 'success' : 'default'}>{p.status === 'active' ? t('modelAdapter.enabled') : p.status}</Tag>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 16 }}>
                  <div style={{ fontSize: 13 }}><span style={{ color: '#94a3b8' }}>{t('modelAdapter.latency')}: </span>{fmtLatency(p.latency_ms)}</div>
                  <div style={{ fontSize: 13 }}>
                    <span style={{ color: '#94a3b8' }}>{p.token_limit ? t('modelAdapter.tokenLimit') + ': ' : p.vector_dimension ? t('modelAdapter.vectorDimension') + ': ' : t('modelAdapter.batchSize') + ': '}</span>
                    {p.token_limit?.toLocaleString() || p.vector_dimension || ((p.config_json as Record<string, unknown>)?.batch_size as number) || '-'}
                  </div>
                  <div style={{ fontSize: 13 }}><span style={{ color: '#94a3b8' }}>{t('modelAdapter.callCount')}: </span>{fmtCount(p.call_count)}</div>
                  <div style={{ fontSize: 13 }}><span style={{ color: '#94a3b8' }}>{t('modelAdapter.successRate')}: </span>{p.success_rate !== null ? `${p.success_rate}%` : '-'}</div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <Button type="primary" size="small" icon={<PlayCircleOutlined />} onClick={() => handleTest(p.id)}>{t('dataAccess.test')}</Button>
                  <Button size="small" icon={<SettingOutlined />} onClick={() => openEdit(p)}>{t('modelAdapter.editProvider')}</Button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <Modal
        title={editing ? t('modelAdapter.editProvider') : t('modelAdapter.addProvider')}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleSave}
        okText={t('common.save')}
        cancelText={t('common.cancel')}
        confirmLoading={submitting}
        width={480}
      >
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>{t('modelAdapter.providerName')} <span style={{ color: '#dc2626' }}>*</span></label>
          <Input placeholder={t('modelAdapter.nameRequired')} value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
        </div>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>{t('modelAdapter.modelName')}</label>
          <Input placeholder={t('modelAdapter.modelNamePlaceholder')} value={form.model_name} onChange={(e) => setForm((f) => ({ ...f, model_name: e.target.value }))} />
        </div>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>{t('modelAdapter.endpoint')}</label>
          <Input placeholder={t('modelAdapter.endpointPlaceholder')} value={form.endpoint} onChange={(e) => setForm((f) => ({ ...f, endpoint: e.target.value }))} />
        </div>
      </Modal>
    </div>
  )
}