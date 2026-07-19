import React, { useState, useMemo, useEffect, useCallback } from 'react'
import {
  Button, Input, Select, Modal, message, Spin, Empty, Pagination, Tooltip,
} from 'antd'
import {
  PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined,
  ExclamationCircleOutlined, ReloadOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import type { TemplateDomain } from '../../api/templateDomains'
import { fetchDomains, createDomain, updateDomain, deleteDomain } from '../../api/templateDomains'
import { colors } from '@jonex/platform-theme/tokens'
import './index.css'

const PAGE_SIZE = 12

const STATUS_OPTIONS = [
  { label: 'templateDomain.allStatus', value: '' },
  { label: 'templateDomain.enabled', value: 'active' },
  { label: 'templateDomain.disabled', value: 'inactive' },
]

const STATUS_MAP: Record<string, { label: string; cls: string }> = {
  active: { label: 'templateDomain.enabled', cls: 'active' },
  inactive: { label: 'templateDomain.disabled', cls: 'inactive' },
  archived: { label: 'templateDomain.archived', cls: 'inactive' },
}


const DOMAIN_ICONS: Array<{ icon: string; bg: string; color: string }> = [
  { icon: '💰', bg: '#eff6ff', color: '#3b82f6' },
  { icon: '🏥', bg: '#f0fdf4', color: '#10b981' },
  { icon: '⚖️', bg: '#fff7ed', color: '#f97316' },
  { icon: '🏭', bg: '#fef2f2', color: '#ef4444' },
  { icon: '📱', bg: '#f5f3ff', color: '#8b5cf6' },
  { icon: '🛒', bg: '#fdf2f8', color: '#ec4899' },
  { icon: '🎓', bg: '#ecfeff', color: '#06b6d4' },
  { icon: '🚚', bg: '#fffbeb', color: '#d97706' },
  { icon: '🏗️', bg: '#f1f5f9', color: '#475569' },
  { icon: '📊', bg: '#f0f9ff', color: '#0284c7' },
]

function getDomainIcon(index: number) {
  return DOMAIN_ICONS[index % DOMAIN_ICONS.length]
}

export default function TemplateDomains() {
  const { t } = useTranslation('business')
  const navigate = useNavigate()
  const [domains, setDomains] = useState<TemplateDomain[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [modalOpen, setModalOpen] = useState(false)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [editingDomain, setEditingDomain] = useState<TemplateDomain | null>(null)
  const [deletingDomain, setDeletingDomain] = useState<TemplateDomain | null>(null)
  const [formName, setFormName] = useState('')
  const [formDesc, setFormDesc] = useState('')
  const [formStatus, setFormStatus] = useState('active')
  const [saving, setSaving] = useState(false)

  const loadDomains = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const offset = (page - 1) * PAGE_SIZE
      const result = await fetchDomains(offset, PAGE_SIZE)
      setDomains(result.items || [])
      setTotal(result.total || 0)
    } catch {
      setError(t('templateDomain.loadFailed'))
    } finally {
      setLoading(false)
    }
  }, [page, t])

  useEffect(() => {
    loadDomains()
  }, [loadDomains])

  const filtered = useMemo(() => {
    return domains.filter((d) => {
      if (search && !d.name.includes(search)) return false
      if (statusFilter && d.status !== statusFilter) return false
      return true
    })
  }, [domains, search, statusFilter])

  const openCreate = () => {
    setEditingDomain(null)
    setFormName('')
    setFormDesc('')
    setFormStatus('active')
    setModalOpen(true)
  }

  const openEdit = (domain: TemplateDomain) => {
    setEditingDomain(domain)
    setFormName(domain.name)
    setFormDesc(domain.description || '')
    setFormStatus(domain.status)
    setModalOpen(true)
  }

  const handleSave = async () => {
    if (!formName.trim()) {
      message.warning(t('templateDomain.nameRequired'))
      return
    }
    setSaving(true)
    try {
      if (editingDomain) {
        await updateDomain(editingDomain.id, {
          name: formName.trim(),
          description: formDesc.trim() || undefined,
          status: formStatus,
        })
        message.success(t('templateDomain.updateSuccess'))
      } else {
        await createDomain({
          name: formName.trim(),
          description: formDesc.trim() || undefined,
          status: formStatus,
        })
        message.success(t('templateDomain.createSuccess'))
      }
      setModalOpen(false)
      await loadDomains()
    } catch {
      message.error(t('common.operationFailed'))
    } finally {
      setSaving(false)
    }
  }

  const openDeleteModal = (domain: TemplateDomain) => {
    setDeletingDomain(domain)
    setDeleteModalOpen(true)
  }

  const handleDelete = async () => {
    if (!deletingDomain) return
    try {
      await deleteDomain(deletingDomain.id)
      message.success(t('templateDomain.deleteSuccess'))
      setDeleteModalOpen(false)
      setDeletingDomain(null)
      await loadDomains()
    } catch {
      message.error(t('common.deleteFailed'))
    }
  }

  const handleCardClick = (domain: TemplateDomain) => {
    navigate(`/template-scenarios?domain_id=${domain.id}`)
  }

  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return '-'
    return dateStr.replace('T', ' ').substring(0, 16)
  }

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('templateDomain.title')}</h1>
        <p className="yx-page-subtitle">{t('templateDomain.subtitle')}</p>
      </div>

      <div className="yx-toolbar">
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <Input
            placeholder={t('templateDomain.searchPlaceholder')}
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            allowClear
            style={{ width: 260 }}
          />
          <Select
            placeholder={t('templateDomain.allStatus')}
            value={statusFilter || undefined}
            onChange={(v) => { setStatusFilter(v || ''); setPage(1) }}
            allowClear
            style={{ width: 130 }}
            options={STATUS_OPTIONS.filter((o) => o.value !== '').map((o) => ({ ...o, label: t(o.label) }))}
          />
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button icon={<ReloadOutlined />} onClick={loadDomains}>{t('common.refresh')}</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            {t('templateDomain.create')}
          </Button>
        </div>
      </div>

      { }
      {loading && (
        <div style={{ textAlign: 'center', padding: 80 }}>
          <Spin size="large" />
        </div>
      )}
      {error && !loading && (
        <div style={{ textAlign: 'center', padding: 80 }}>
          <Empty description={error}>
            <Button type="primary" onClick={loadDomains}>{t('common.retry')}</Button>
          </Empty>
        </div>
      )}
      {!loading && !error && filtered.length === 0 && (
        <div style={{ textAlign: 'center', padding: 80 }}>
          <Empty description={t('templateDomain.noData')}>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
              {t('templateDomain.createFirst')}
            </Button>
          </Empty>
        </div>
      )}

      { }
      {!loading && !error && filtered.length > 0 && (
        <>
          <div className="domain-grid">
            {filtered.map((domain, index) => {
              const iconDef = getDomainIcon(index)
              const meta = STATUS_MAP[domain.status]
              return (
                <div
                  key={domain.id}
                  className="domain-card"
                  onClick={() => handleCardClick(domain)}
                >
                  <div
                    className="card-icon"
                    style={{ background: iconDef.bg, color: iconDef.color }}
                  >
                    {iconDef.icon}
                  </div>
                  <div className="card-body">
                    <Tooltip title={domain.name}>
                      <div className="card-title">{domain.name}</div>
                    </Tooltip>
                    {domain.description ? (
                      <Tooltip title={domain.description}>
                        <div className="card-desc">{domain.description}</div>
                      </Tooltip>
                    ) : (
                      <div className="card-desc" style={{ color: '#cbd5e1' }}>{t('common.noDescription')}</div>
                    )}
                  </div>
                  <div className="card-meta">
                    <span className="card-time">{formatDate(domain.created_at)}</span>
                    <span className={`card-status ${meta?.cls || domain.status}`}>
                      {meta ? t(meta.label) : domain.status}
                    </span>
                  </div>
                  <div className="card-footer">
                    <span className="card-scenario-count">
                      {t('templateDomain.scenarioCountText', { count: domain.scenario_count ?? 0 })}
                    </span>
                    <div className="card-actions">
                      <Button
                        type="text"
                        size="small"
                        icon={<EditOutlined />}
                        onClick={(e) => { e.stopPropagation(); openEdit(domain) }}
                      />
                      <Button
                        type="text"
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={(e) => { e.stopPropagation(); openDeleteModal(domain) }}
                      />
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          { }
          {total > PAGE_SIZE && (
            <div style={{ textAlign: 'center', marginTop: 24 }}>
              <Pagination
                current={page}
                pageSize={PAGE_SIZE}
                total={total}
                onChange={(p) => setPage(p)}
                showSizeChanger={false}
              />
            </div>
          )}
        </>
      )}

      { }
      <Modal
        title={editingDomain ? t('templateDomain.edit') : t('templateDomain.create')}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleSave}
        okText={t('common.save')}
        cancelText={t('common.cancel')}
        confirmLoading={saving}
        width={520}
      >
        <div className="yx-form-row">
          <label>
            {t('templateDomain.name')} <span style={{ color: '#dc2626' }}>*</span>
          </label>
          <Input
            placeholder={t('templateDomain.namePlaceholder')}
            value={formName}
            onChange={(e) => setFormName(e.target.value)}
          />
        </div>
        <div className="yx-form-row">
          <label>{t('templateDomain.description')}</label>
          <Input.TextArea
            placeholder={t('templateDomain.descPlaceholder')}
            value={formDesc}
            onChange={(e) => setFormDesc(e.target.value)}
            rows={3}
          />
        </div>
        <div className="yx-form-row">
          <label>{t('templateDomain.status')}</label>
          <Select
            value={formStatus}
            onChange={(v) => setFormStatus(v)}
            style={{ width: '100%' }}
            options={[
              { label: t('templateDomain.enabled'), value: 'active' },
              { label: t('templateDomain.disabled'), value: 'inactive' },
            ]}
          />
        </div>
      </Modal>

      { }
      <Modal
        title={null}
        open={deleteModalOpen}
        onCancel={() => setDeleteModalOpen(false)}
        onOk={handleDelete}
        okText={t('common.confirmDelete')}
        cancelText={t('common.cancel')}
        okButtonProps={{ danger: true }}
        width={400}
      >
        <div style={{ textAlign: 'center', padding: '12px 0' }}>
          <div
            style={{
              width: 48, height: 48, borderRadius: 12,
              background: '#fef2f2', color: '#dc2626',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 22, margin: '0 auto 12px',
            }}
          >
            <ExclamationCircleOutlined />
          </div>
          <div>
            <strong style={{ fontSize: 16 }}>{deletingDomain?.name}</strong>
            <p style={{ fontSize: 14, color: colors.textSecondary, margin: '4px 0 0' }}>
              {t('templateDomain.confirmDelete')}
            </p>
          </div>
        </div>
      </Modal>
    </div>
  )
}
