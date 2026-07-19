import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Button, Input, Select } from 'antd'
import { SettingOutlined, SaveOutlined } from '@ant-design/icons'
import type { EngineSetting } from '@/types/domainKnowledge'
import { ENGINE_MODEL_OPTIONS, DEFAULT_ENGINE_MODEL } from './constants'

const cardStyle: React.CSSProperties = {
  background: '#fff', borderRadius: 14, border: '1px solid #eef2f6', padding: 24, marginBottom: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
}
const h3Style: React.CSSProperties = { margin: 0, fontSize: 15, fontWeight: 600, color: '#0b2b5c', display: 'flex', alignItems: 'center', gap: 8 }

interface Props {
  engine: EngineSetting | null
  loading: boolean
  onSave: (model: string) => void
}

export default function EngineBasicSection({ engine, loading, onSave }: Props) {
  const { t } = useTranslation()
  const [model, setModel] = useState<string>(DEFAULT_ENGINE_MODEL)
  useEffect(() => { if (engine) setModel(engine.semanticModel) }, [engine])

  return (
    <div className="config-section" style={cardStyle}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <h3 style={h3Style}><SettingOutlined style={{ color: '#3b82f6' }} /> {t('compile.engineSettings')}</h3>
      </div>
      <p style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16 }}>Configure the model and engine parameters used for ontology construction.</p>
      <div style={{ padding: 20, maxWidth: 560, border: '1px solid #eef2f6', borderRadius: 10 }}>
        <div className="yx-form-row">
          <label>Ontology Construction Model <span style={{ color: '#dc2626' }}>*</span></label>
          <Select value={model} onChange={setModel} style={{ width: '100%' }} loading={loading} options={ENGINE_MODEL_OPTIONS} />
        </div>
        <div className="yx-form-row" style={{ marginTop: 16 }}>
          <label>Ontology Construction Prompt</label>
          <Input.TextArea
            rows={4}
            disabled
            placeholder={t('ontology.notImplemented')}
          />
          <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 6 }}>
            Prompt persistence is planned and is not available in this release.
          </div>
        </div>
        <div style={{ marginTop: 16, display: 'flex', gap: 10 }}>
          <Button type="primary" icon={<SaveOutlined />} onClick={() => onSave(model)}>{t('common.save')}</Button>
          <Button onClick={() => setModel(DEFAULT_ENGINE_MODEL)}>Restore Default</Button>
        </div>
      </div>
    </div>
  )
}