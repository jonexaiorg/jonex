import {
  SearchOutlined,
  VideoCameraOutlined, AudioOutlined, FileImageOutlined,
  FileTextOutlined, GlobalOutlined, PartitionOutlined,
} from '@ant-design/icons'
import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { listParsers, type ParserItem } from '@/api/parsers'
import './index.css'

interface DisplayField {
  label: string
  value: string
}

interface PrototypeDisplayField {
  labelKey: string
  valueKey?: string
  value?: string
}

interface PrototypeParserView {
  descKey: string
  color: string
  icon: React.ReactNode
  fields: PrototypeDisplayField[]
  order: number
}

const PROTOTYPE_PARSERS: Record<string, PrototypeParserView> = {
  video: {
    descKey: 'parserManagement.prototype.videoDesc',
    color: '#ef4444',
    icon: <VideoCameraOutlined />,
    fields: [
      { labelKey: 'parserManagement.fields.keyFrameExtraction', valueKey: 'parserManagement.values.smartMode' },
      { labelKey: 'parserManagement.fields.resolutionLimit', value: '1080p' },
    ],
    order: 0,
  },
  audio: {
    descKey: 'parserManagement.prototype.audioDesc',
    color: '#8b5cf6',
    icon: <AudioOutlined />,
    fields: [
      { labelKey: 'parserManagement.fields.transcriptionModel', valueKey: 'parserManagement.values.generalTranscriptionModel' },
      { labelKey: 'parserManagement.fields.outputFormat', value: 'SRT' },
    ],
    order: 1,
  },
  image: {
    descKey: 'parserManagement.prototype.imageDesc',
    color: '#f59e0b',
    icon: <FileImageOutlined />,
    fields: [
      { labelKey: 'parserManagement.fields.ocrEngine', valueKey: 'parserManagement.values.builtInOcr' },
      { labelKey: 'parserManagement.fields.imageCompression', valueKey: 'parserManagement.values.highQuality' },
    ],
    order: 2,
  },
  document: {
    descKey: 'parserManagement.prototype.documentDesc',
    color: '#3b82f6',
    icon: <FileTextOutlined />,
    fields: [
      { labelKey: 'parserManagement.fields.layoutRetention', valueKey: 'parserManagement.values.enabled' },
      { labelKey: 'parserManagement.fields.tableExtraction', valueKey: 'parserManagement.values.smartExtraction' },
    ],
    order: 3,
  },
  web: {
    descKey: 'parserManagement.prototype.webDesc',
    color: '#94a3b8',
    icon: <GlobalOutlined />,
    fields: [
      { labelKey: 'parserManagement.fields.renderingMode', valueKey: 'parserManagement.values.staticRendering' },
      { labelKey: 'parserManagement.fields.crawlDepth', value: '--' },
    ],
    order: 4,
  },
  cad: {
    descKey: 'parserManagement.prototype.cadDesc',
    color: '#94a3b8',
    icon: <PartitionOutlined />,
    fields: [
      { labelKey: 'parserManagement.fields.accuracyLevel', valueKey: 'parserManagement.values.standard' },
      { labelKey: 'parserManagement.fields.layerExtraction', valueKey: 'parserManagement.values.all' },
    ],
    order: 5,
  },
}

function iconForType(type: string): React.ReactNode {
  return PROTOTYPE_PARSERS[type]?.icon || <FileTextOutlined />
}

function colorForType(type: string, active: boolean): string {
  if (!active) return '#94a3b8'
  return PROTOTYPE_PARSERS[type]?.color || '#3b82f6'
}

function parserDesc(parser: ParserItem, t: TFunction): string {
  const prototype = PROTOTYPE_PARSERS[parser.parser_type]
  if (prototype) return t(prototype.descKey)
  return t('parserManagement.genericDescription', {
    formats: (parser.file_types || []).join('/'),
    name: parser.name,
  })
}

function formatProcessCount(value: unknown, active: boolean): string {
  if (!active) return '--'
  if (typeof value === 'number') return value.toLocaleString()
  if (typeof value === 'string' && value) return value
  return '--'
}

function displayFields(parser: ParserItem, t: TFunction): DisplayField[] {
  const prototype = PROTOTYPE_PARSERS[parser.parser_type]
  if (prototype) {
    return prototype.fields.map((field) => ({
      label: t(field.labelKey),
      value: field.valueKey ? t(field.valueKey) : field.value || '--',
    }))
  }

  const raw = parser.config_json?.display_fields
  if (Array.isArray(raw)) {
    return raw.map((item) => ({
      label: String((item as any).label || ''),
      value: String((item as any).value || '--'),
    })).filter((item) => item.label)
  }
  return [
    { label: t('parserManagement.fields.supportedFormats'), value: (parser.file_types || []).slice(0, 4).join(' / ') || '--' },
    { label: t('parserManagement.fields.parserType'), value: parser.parser_type || '--' },
  ]
}

function getErrorMessage(error: unknown, t: TFunction): string {
  if (error instanceof Error) return error.message
  return t('parserManagement.requestFailed')
}

export default function ParserManagement() {
  const { t } = useTranslation('business')
  const [search, setSearch] = useState('')
  const [parsers, setParsers] = useState<ParserItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const loadParsers = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const resp = await listParsers(0, 100)
      setParsers(resp.items || [])
    } catch (err) {
      setError(getErrorMessage(err, t))
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => {
    void loadParsers()
  }, [loadParsers])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    const visibleParsers = parsers
      .filter((parser) => Boolean(PROTOTYPE_PARSERS[parser.parser_type]))
      .sort((a, b) => PROTOTYPE_PARSERS[a.parser_type].order - PROTOTYPE_PARSERS[b.parser_type].order)

    if (!q) return visibleParsers
    return visibleParsers.filter((parser) => {
      const fileTypes = (parser.file_types || []).join(' ').toLowerCase()
      return (
        parser.name.toLowerCase().includes(q) ||
        parser.parser_type.toLowerCase().includes(q) ||
        fileTypes.includes(q)
      )
    })
  }, [parsers, search])

  return (
    <div>
      <div className="yx-page-title">
        <h1 style={{ fontSize: 22, fontWeight: 700, color: '#0b2b5c', margin: 0 }}>
          {t('parserManagement.title')}
        </h1>
      </div>
      <div style={{ marginBottom: 20, marginTop: 8 }}>
        <div className="yx-search-box" style={{ width: 240 }}>
          <SearchOutlined style={{ color: '#94a3b8' }} />
          <input
            type="text"
            placeholder={t('parserManagement.searchPlaceholder')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {error && (
        <div className="parser-page-error">
          <span>{error}</span>
          <button type="button" onClick={() => void loadParsers()}>
            {t('common.retry')}
          </button>
        </div>
      )}

      <div className="parser-grid">
        {loading ? (
          <div className="parser-state">{t('parserManagement.loading')}</div>
        ) : filtered.length === 0 ? (
          <div className="parser-state">{t('parserManagement.noParsers')}</div>
        ) : (
          filtered.map((parser) => {
            const isActive = parser.status === 'active'
            const version = String(parser.config_json?.version || '--')
            const processCount = formatProcessCount(parser.config_json?.process_count, isActive)

            return (
              <div key={parser.id} className={`parser-card${isActive ? '' : ' grey'}`}>
                <div className="parser-icon" style={{ color: colorForType(parser.parser_type, isActive) }}>
                  {iconForType(parser.parser_type)}
                </div>
                {!isActive && <div className="future-tag">{t('parserManagement.comingSoon')}</div>}
                <h3>
                  {parser.name}{' '}
                  {isActive && (
                    <>
                      <span className="status-dot green" />
                      <span style={{ fontSize: 12, color: '#22c55e', fontWeight: 400 }}>{t('status.running')}</span>
                    </>
                  )}
                </h3>
                <div className="parser-desc">{parserDesc(parser, t)}</div>
                <div className="parser-meta">
                  <span>{t('parserManagement.version')} {version}</span>
                  <span>{t('parserManagement.processCount')} {processCount}</span>
                </div>
                {displayFields(parser, t).map((row) => (
                  <div key={row.label} className="form-row">
                    <label>{row.label}</label>
                    <div style={{ fontSize: 13, color: '#334155', padding: '2px 0' }}>{row.value}</div>
                  </div>
                ))}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
