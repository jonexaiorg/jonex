import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { Input, Button, message } from 'antd'
import { PlusCircleOutlined } from '@ant-design/icons'
import { emitSpacesInvalidated } from '@jonex/shell-sdk'
import { createSpace } from '../../api/domainSpace'
import type { DomainSpaceFormData } from '../../types/domainSpace'
import { useStore } from '../../store'

export default function DomainSpaceCreate() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { global } = useStore()
  const [form, setForm] = useState<DomainSpaceFormData>({ name: '', description: '' })
  const [submitting, setSubmitting] = useState(false)

  const handleCreate = async () => {
    if (!form.name.trim()) {
      message.warning(t('domainSpace.nameRequired'))
      return
    }
    setSubmitting(true)
    try {
      const saved = await createSpace({ ...form, name: form.name.trim() })
      message.success(t('domainSpace.createSuccess'))
      await global.refreshSpaces()
      if (saved?.id) {
        global.setCurrentSpaceId(saved.id, { persist: true, broadcast: true })
        emitSpacesInvalidated()

        navigate(`/domain-space/${saved.id}/settings`, { replace: true })
        return
      }
      emitSpacesInvalidated()
      navigate('/domain-space', { replace: true })
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('domainKnowledge.createFailed'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="yx-domain-space-page">
      <div className="yx-page-header">
        <h1 className="yx-page-title" style={{ margin: 0 }}>{t('domainSpace.create')}</h1>
      </div>

      <div className="yx-card" style={{ padding: '28px 32px', maxWidth: 640 }}>
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 13, color: '#64748b', marginBottom: 6 }}>
            <span style={{ color: '#ef4444', marginRight: 4 }}>*</span>{t('domainSpace.nameRequired')}
          </div>
          <Input
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            placeholder={t('domainSpace.create')}
            maxLength={128}
            onPressEnter={handleCreate}
          />
        </div>
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 13, color: '#64748b', marginBottom: 6 }}>{t('domainService.description')}</div>
          <Input.TextArea
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            placeholder={t('domainService.description')}
            rows={4}
          />
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
          <Button onClick={() => navigate('/domain-space')}>{t('dataSource.cancel')}</Button>
          <Button type="primary" icon={<PlusCircleOutlined />} loading={submitting} onClick={handleCreate}>
            {t('domainSpace.create')}
          </Button>
        </div>
      </div>
    </div>
  )
}
