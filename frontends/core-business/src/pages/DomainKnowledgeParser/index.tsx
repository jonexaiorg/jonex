import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  AudioFilled,
  CloseOutlined,
  DownOutlined,
  ExclamationCircleFilled,
  FileExcelFilled,
  FileImageFilled,
  FilePdfFilled,
  FilePptFilled,
  FileTextOutlined,
  FileWordFilled,
  FilterFilled,
  PlusOutlined,
  SaveFilled,
  VideoCameraFilled,
} from '@ant-design/icons'
import {
  createParserSetting,
  deleteParserSetting,
  getParserConfigs,
  getParserSettings,
  listPromptTemplates,
  updateParserSetting,
  type ParserConfigItem,
  type ParserSettingItem,
  type ParserSettingPayload,
  type PromptTemplateListItem,
} from '@/api/domainKnowledge'
import { useTranslation } from 'react-i18next'
import './index.css'

interface ParserConfigRow {
  id: string
  fileType: string
  type: string
  parserConfigId: string
  parserName: string
  preprocessing: string[]
  postprocessing: string[]
  prompt: string
  promptTemplateId?: string | null
  promptTemplateVersion?: string | null
  summaryPrompt: string
  summaryTemplateId?: string | null
  summaryTemplateVersion?: string | null
  tagPrompt: string
  tagTemplateId?: string | null
  tagTemplateVersion?: string | null
}

interface ParserFormState {
  type: string
  parserConfigId: string
  prompt: string
  promptTemplateId?: string | null
  promptTemplateVersion?: string | null
  preprocessing: string[]
  postSummary: boolean
  postTag: boolean
  summaryPrompt: string
  summaryTemplateId?: string | null
  summaryTemplateVersion?: string | null
  tagPrompt: string
  tagTemplateId?: string | null
  tagTemplateVersion?: string | null
}

interface FileTypeOption {
  fileType: string
  label: string
  extensions: string[]
}

type TemplateTarget = 'prompt' | 'summaryPrompt' | 'tagPrompt'

interface ParserConfigContentProps {
  kbId?: string
}

const fileTypeOptions: FileTypeOption[] = [
  { fileType: 'pdf', label: 'PDF', extensions: ['PDF'] },
  { fileType: 'doc', label: 'DOCX / DOC', extensions: ['DOCX', 'DOC'] },
  { fileType: 'xlsx', label: 'XLSX', extensions: ['XLSX'] },
  { fileType: 'pptx', label: 'PPTX', extensions: ['PPTX', 'PPT'] },
  { fileType: 'image', label: 'JPG / PNG / GIF', extensions: ['JPG', 'JPEG', 'PNG', 'GIF'] },
  { fileType: 'audio', label: 'MP3 / WAV / AAC', extensions: ['MP3', 'WAV', 'AAC'] },
  { fileType: 'video', label: 'MP4 / AVI / MOV', extensions: ['MP4', 'AVI', 'MOV'] },
  { fileType: 'txt', label: 'TXT', extensions: ['TXT'] },
  { fileType: 'md', label: 'MD', extensions: ['MD'] },
  { fileType: 'html', label: 'HTML / XML', extensions: ['HTML', 'HTM', 'XML'] },
  { fileType: 'cad', label: 'DWG / DXF', extensions: ['DWG', 'DXF'] },
]

const visibleParserTypeOrder = ['video', 'audio', 'image', 'document', 'web', 'cad']
const visibleParserTypes = new Set(visibleParserTypeOrder)
const preferredParserTypeByFileType: Record<string, string> = {
  pdf: 'document',
  doc: 'document',
  xlsx: 'document',
  pptx: 'document',
  txt: 'document',
  md: 'document',
  html: 'document',
  image: 'image',
  audio: 'audio',
  video: 'video',
  cad: 'cad',
}

const preprocessOptions = [
  { code: 'large_document_preprocess', labelKey: 'parserConfig.largeDocumentPreprocess', legacy: '大文档预处理' },
  { code: 'long_document_preprocess', labelKey: 'parserConfig.longDocumentPreprocess', legacy: '长文档预处理' },
  { code: 'excel_multi_sheet', labelKey: 'parserConfig.excelMultiSheet', legacy: 'Excel多Sheet处理' },
  { code: 'html_base64_media', labelKey: 'parserConfig.htmlBase64Media', legacy: 'HTML Base64媒体处理' },
  { code: 'video_quality_check', labelKey: 'parserConfig.videoQualityCheck', legacy: '视频质量检测' },
  { code: 'video_frame_reduction', labelKey: 'parserConfig.videoFrameReduction', legacy: '视频缩帧处理' },
  { code: 'long_video_segmentation', labelKey: 'parserConfig.longVideoSegmentation', legacy: '长视频分段处理' },
] as const

const postprocessOptions = [
  { code: 'auto_summary', labelKey: 'parserConfig.autoSummary', legacy: '自动摘要' },
  { code: 'auto_tag', labelKey: 'parserConfig.autoTag', legacy: '自动标签' },
] as const

const processingOptions = [...preprocessOptions, ...postprocessOptions]
const legacyProcessingCode = new Map<string, string>(
  processingOptions.map((option) => [option.legacy, option.code]),
)
const processingLabelKey = new Map<string, string>(
  processingOptions.map((option) => [option.code, option.labelKey]),
)

function normalizeProcessingList(value: unknown): string[] {
  return Array.isArray(value)
    ? value.map(String).map((item) => legacyProcessingCode.get(item) || item)
    : []
}

function getProcessingLabel(item: string, t: (key: string, options?: { defaultValue?: string }) => string): string {
  const labelKey = processingLabelKey.get(item)
  return labelKey ? t(labelKey, { defaultValue: item }) : item
}

const emptyForm: ParserFormState = {
  type: '',
  parserConfigId: '',
  prompt: '',
  promptTemplateId: null,
  promptTemplateVersion: null,
  preprocessing: [],
  postSummary: false,
  postTag: false,
  summaryPrompt: '',
  summaryTemplateId: null,
  summaryTemplateVersion: null,
  tagPrompt: '',
  tagTemplateId: null,
  tagTemplateVersion: null,
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  return 'Request failed. Please try again later'
}

function renderFileIcon(type: string): React.ReactNode {
  if (type.includes('PDF')) return <FilePdfFilled />
  if (type.includes('DOC')) return <FileWordFilled />
  if (type.includes('XLS')) return <FileExcelFilled />
  if (type.includes('PPT')) return <FilePptFilled />
  if (type.includes('JPG') || type.includes('PNG') || type.includes('GIF')) return <FileImageFilled />
  if (type.includes('MP3') || type.includes('WAV') || type.includes('AAC')) return <AudioFilled />
  if (type.includes('MP4') || type.includes('AVI') || type.includes('MOV')) return <VideoCameraFilled />
  return <FileTextOutlined />
}

function getIconClass(type: string): string {
  if (type.includes('PDF')) return 'pdf'
  if (type.includes('DOC')) return 'word'
  if (type.includes('XLS')) return 'excel'
  if (type.includes('PPT')) return 'ppt'
  if (type.includes('JPG') || type.includes('PNG') || type.includes('GIF')) return 'image'
  if (type.includes('MP3') || type.includes('WAV') || type.includes('AAC')) return 'audio'
  if (type.includes('MP4') || type.includes('AVI') || type.includes('MOV')) return 'video'
  if (type.includes('DWG') || type.includes('DXF')) return 'cad'
  return 'text'
}

function normalizeFileType(value: string): string {
  const byLabel = fileTypeOptions.find((item) => item.label === value)
  if (byLabel) return byLabel.fileType
  const byKey = fileTypeOptions.find((item) => item.fileType === value)
  if (byKey) return byKey.fileType
  return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '')
}

function labelForFileType(fileType: string, fallback: string): string {
  return fileTypeOptions.find((item) => item.fileType === fileType)?.label || fallback || fileType.toUpperCase()
}

function buildPostprocessing(form: ParserFormState): string[] {
  const postprocessing: string[] = []
  if (form.postSummary) postprocessing.push('auto_summary')
  if (form.postTag) postprocessing.push('auto_tag')
  return postprocessing
}

function toList(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String) : []
}

function mapSettingToRow(item: ParserSettingItem): ParserConfigRow {
  const postprocessing = normalizeProcessingList(item.postprocessing_json)
  return {
    id: item.id,
    fileType: item.file_type,
    type: labelForFileType(item.file_type, item.file_type_label),
    parserConfigId: item.parser_config_id || '',
    parserName: item.parser_name || '',
    preprocessing: normalizeProcessingList(item.preprocessing_json),
    postprocessing,
    prompt: item.prompt_text || '',
    promptTemplateId: item.prompt_template_id,
    promptTemplateVersion: item.prompt_template_version,
    summaryPrompt: item.summary_prompt_text || '',
    summaryTemplateId: item.summary_template_id,
    summaryTemplateVersion: item.summary_template_version,
    tagPrompt: item.tag_prompt_text || '',
    tagTemplateId: item.tag_template_id,
    tagTemplateVersion: item.tag_template_version,
  }
}

function rowToForm(row: ParserConfigRow): ParserFormState {
  return {
    type: row.type,
    parserConfigId: row.parserConfigId,
    prompt: row.prompt,
    promptTemplateId: row.promptTemplateId,
    promptTemplateVersion: row.promptTemplateVersion,
    preprocessing: row.preprocessing,
    postSummary: row.postprocessing.includes('auto_summary'),
    postTag: row.postprocessing.includes('auto_tag'),
    summaryPrompt: row.summaryPrompt,
    summaryTemplateId: row.summaryTemplateId,
    summaryTemplateVersion: row.summaryTemplateVersion,
    tagPrompt: row.tagPrompt,
    tagTemplateId: row.tagTemplateId,
    tagTemplateVersion: row.tagTemplateVersion,
  }
}

function renderTags(
  items: string[],
  type: 'pre' | 'post',
  t: (key: string, options?: { defaultValue?: string }) => string,
) {
  if (items.length === 0) {
    return <span className="parser-config-muted">Not configured</span>
  }

  return (
    <div className="parser-config-tags">
      {items.map((item) => (
        <span key={item} className={`parser-config-tag ${type}`}>
          {getProcessingLabel(item, t)}
        </span>
      ))}
    </div>
  )
}

function parserMatchesFileType(parser: ParserConfigItem, label: string): boolean {
  const option = fileTypeOptions.find((item) => item.label === label)
  const wanted = new Set((option?.extensions || []).map((item) => item.toUpperCase()))
  if (!wanted.size) return false
  return (parser.file_types || []).some((item) => wanted.has(String(item).toUpperCase()))
}

function templateContent(template: PromptTemplateListItem): string {
  const versions = template.versions_json || []
  return (
    versions.find((item) => item.version === template.current_version)?.content ||
    versions[0]?.content ||
    ''
  )
}

function templateDesc(template: PromptTemplateListItem): string {
  return template.description || `${template.category} · ${template.scope === 'system' ? 'System Template' : 'Domain Template'}`
}

export function ParserConfigContent({ kbId }: ParserConfigContentProps) {
  const params = useParams<{ id: string }>()
  const resolvedKbId = kbId || params.id || ''

  const [rows, setRows] = useState<ParserConfigRow[]>([])
  const [parsers, setParsers] = useState<ParserConfigItem[]>([])
  const [templates, setTemplates] = useState<PromptTemplateListItem[]>([])
  const [loading, setLoading] = useState(false)
  const [templateLoading, setTemplateLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [pageError, setPageError] = useState('')
  const [templateError, setTemplateError] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [mode, setMode] = useState<'add' | 'edit'>('add')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<ParserFormState>(emptyForm)
  const [formError, setFormError] = useState('')
  const [preprocessOpen, setPreprocessOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<ParserConfigRow | null>(null)
  const [templateOpen, setTemplateOpen] = useState(false)
  const [templateTarget, setTemplateTarget] = useState<TemplateTarget>('prompt')
  const [notice, setNotice] = useState('')
  const { t } = useTranslation()

  const activeParsers = useMemo(
    () => parsers
      .filter((parser) => parser.status === 'active' && visibleParserTypes.has(parser.parser_type))
      .sort((a, b) => visibleParserTypeOrder.indexOf(a.parser_type) - visibleParserTypeOrder.indexOf(b.parser_type)),
    [parsers],
  )

  const parserNameMap = useMemo(() => {
    const map = new Map<string, string>()
    parsers.forEach((parser) => map.set(parser.id, parser.name))
    return map
  }, [parsers])

  const loadData = useCallback(async () => {
    if (!resolvedKbId) {
      setPageError('Knowledge base ID is missing. Parser settings cannot be loaded.')
      return
    }

    setLoading(true)
    setPageError('')
    try {
      const [parserResp, settingsResp] = await Promise.all([
        getParserConfigs(0, 100),
        getParserSettings(resolvedKbId),
      ])
      setParsers(parserResp.items || [])
      setRows((settingsResp.items || []).map(mapSettingToRow))
    } catch (error) {
      setPageError(getErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }, [resolvedKbId])

  const loadTemplates = useCallback(async () => {
    setTemplateLoading(true)
    setTemplateError('')
    try {
      const resp = await listPromptTemplates({ offset: 0, limit: 100 })
      setTemplates(resp.items || [])
    } catch (error) {
      setTemplateError(getErrorMessage(error))
    } finally {
      setTemplateLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadData()
  }, [loadData])

  const chooseDefaultParser = (typeLabel: string): string => {
    const fileType = normalizeFileType(typeLabel)
    const preferredType = preferredParserTypeByFileType[fileType]
    const preferredParser = activeParsers.find((parser) => parser.parser_type === preferredType)
    if (preferredParser) return preferredParser.id

    return (
      activeParsers.find((parser) => parserMatchesFileType(parser, typeLabel))?.id ||
      activeParsers[0]?.id ||
      ''
    )
  }

  const openAddModal = () => {
    setMode('add')
    setEditingId(null)
    setForm(emptyForm)
    setFormError('')
    setPreprocessOpen(false)
    setModalOpen(true)
  }

  const openEditModal = (row: ParserConfigRow) => {
    setMode('edit')
    setEditingId(row.id)
    setForm(rowToForm(row))
    setFormError('')
    setPreprocessOpen(false)
    setModalOpen(true)
  }

  const closeFormModal = () => {
    setModalOpen(false)
    setPreprocessOpen(false)
    setFormError('')
  }

  const updateForm = <K extends keyof ParserFormState>(key: K, value: ParserFormState[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }))
    setFormError('')
  }

  const updateFileType = (typeLabel: string) => {
    setForm((prev) => ({
      ...prev,
      type: typeLabel,
      parserConfigId: prev.parserConfigId || chooseDefaultParser(typeLabel),
    }))
    setFormError('')
  }

  const togglePreprocess = (value: string) => {
    setForm((prev) => {
      const exists = prev.preprocessing.includes(value)
      return {
        ...prev,
        preprocessing: exists
          ? prev.preprocessing.filter((item) => item !== value)
          : [...prev.preprocessing, value],
      }
    })
  }

  const removePreprocess = (value: string) => {
    setForm((prev) => ({
      ...prev,
      preprocessing: prev.preprocessing.filter((item) => item !== value),
    }))
  }

  const buildPayload = (): ParserSettingPayload => ({
    knowledge_base_id: resolvedKbId,
    file_type: normalizeFileType(form.type),
    file_type_label: form.type,
    parser_config_id: form.parserConfigId,
    preprocessing_json: form.preprocessing,
    postprocessing_json: buildPostprocessing(form),
    prompt_text: form.prompt,
    prompt_template_id: form.promptTemplateId || null,
    prompt_template_version: form.promptTemplateVersion || null,
    summary_prompt_text: form.summaryPrompt,
    summary_template_id: form.summaryTemplateId || null,
    summary_template_version: form.summaryTemplateVersion || null,
    tag_prompt_text: form.tagPrompt,
    tag_template_id: form.tagTemplateId || null,
    tag_template_version: form.tagTemplateVersion || null,
    status: 'active',
  })

  const saveForm = async () => {
    if (!resolvedKbId) {
      setFormError('Knowledge base ID is missing. Changes cannot be saved.')
      return
    }
    if (!form.type || !form.parserConfigId) {
      setFormError('Select a file type and linked parser.')
      return
    }

    const fileType = normalizeFileType(form.type)
    const duplicate = rows.some((row) => row.fileType === fileType && row.id !== editingId)
    if (duplicate) {
      setFormError('This file type already exists. Use Configure to modify it.')
      return
    }

    setSaving(true)
    setFormError('')
    try {
      const payload = buildPayload()
      const saved = mode === 'edit' && editingId
        ? await updateParserSetting(editingId, payload)
        : await createParserSetting(payload)
      const nextRow = mapSettingToRow(saved)

      setRows((prev) =>
        mode === 'edit'
          ? prev.map((row) => (row.id === nextRow.id ? nextRow : row))
          : [...prev, nextRow],
      )
      setNotice(mode === 'edit' ? t('common.savedSuccess') : t('common.createdSuccess'))
      closeFormModal()
    } catch (error) {
      setFormError(getErrorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  const confirmDelete = async () => {
    if (!deleteTarget) return
    setSaving(true)
    try {
      await deleteParserSetting(deleteTarget.id)
      setRows((prev) => prev.filter((row) => row.id !== deleteTarget.id))
      setNotice(t('common.deletedSuccess'))
      setDeleteTarget(null)
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  const openTemplateModal = (target: TemplateTarget) => {
    setTemplateTarget(target)
    setTemplateOpen(true)
    if (!templates.length) {
      void loadTemplates()
    }
  }

  const applyTemplate = (template: PromptTemplateListItem) => {
    const content = templateContent(template)
    setForm((prev) => {
      if (templateTarget === 'summaryPrompt') {
        return {
          ...prev,
          summaryPrompt: content,
          summaryTemplateId: template.id,
          summaryTemplateVersion: template.current_version,
        }
      }
      if (templateTarget === 'tagPrompt') {
        return {
          ...prev,
          tagPrompt: content,
          tagTemplateId: template.id,
          tagTemplateVersion: template.current_version,
        }
      }
      return {
        ...prev,
        prompt: content,
        promptTemplateId: template.id,
        promptTemplateVersion: template.current_version,
      }
    })
    setTemplateOpen(false)
  }

  return (
    <>
      <section className="parser-config-panel">
        <div className="parser-config-header">
          <div>
            <h1>
              <FilterFilled />
              {t('knowledgeSearch.parserConfig')}
            </h1>
          </div>
          <button
            type="button"
            className="parser-config-add"
            onClick={openAddModal}
            disabled={loading || !resolvedKbId}
          >
            <PlusOutlined />
            Add Parser Setting
          </button>
        </div>

        {notice && (
          <div className="parser-config-notice">
            <span>{notice}</span>
            <button type="button" onClick={() => setNotice('')} aria-label="Dismiss notification">
              <CloseOutlined />
            </button>
          </div>
        )}

        {pageError && (
          <div className="parser-config-error">
            <span>{pageError}</span>
            <button type="button" onClick={() => void loadData()}>
              {t('domainKnowledge.retry')}
            </button>
          </div>
        )}

        <div className="parser-config-table-wrap">
          <table className="parser-config-data-table">
            <colgroup>
              <col className="parser-col-type" />
              <col className="parser-col-parser" />
              <col className="parser-col-pre" />
              <col className="parser-col-post" />
              <col className="parser-col-actions" />
            </colgroup>
            <thead>
              <tr>
                <th>{t('knowledgeSearch.fileType')}</th>
                <th>Linked Parser</th>
                <th>Preprocessing</th>
                <th>Postprocessing</th>
                <th>{t('knowledgeSearch.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5}>
                    <div className="parser-config-empty">{t('dataSource.loading')}</div>
                  </td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td colSpan={5}>
                    <div className="parser-config-empty">No parser settings</div>
                  </td>
                </tr>
              ) : (
                rows.map((row) => {
                  const parserName = row.parserName || parserNameMap.get(row.parserConfigId) || 'No linked parser'
                  return (
                    <tr key={row.id}>
                      <td>
                        <div className="parser-config-filetype">
                          <span className={`parser-file-icon ${getIconClass(row.type)}`}>
                            {renderFileIcon(row.type)}
                          </span>
                          <span>{row.type}</span>
                        </div>
                      </td>
                      <td>{parserName}</td>
                      <td>{renderTags(row.preprocessing, 'pre', t)}</td>
                      <td>{renderTags(row.postprocessing, 'post', t)}</td>
                      <td>
                        <div className="parser-config-actions">
                          <button type="button" onClick={() => openEditModal(row)}>
                            Configure
                          </button>
                          <span />
                          <button type="button" className="danger" onClick={() => setDeleteTarget(row)}>
                            {t('dataSource.delete')}
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </section>

      {modalOpen && (
        <div className="parser-modal-mask">
          <div className="parser-modal" role="dialog" aria-modal="true" aria-labelledby="parser-modal-title">
            <div className="parser-modal-header">
              <h2 id="parser-modal-title">{mode === 'edit' ? 'Edit Parser Setting' : 'Add Parser Setting'}</h2>
              <button type="button" className="parser-modal-close" onClick={closeFormModal} aria-label="Close">
                <CloseOutlined />
              </button>
            </div>

            <div className="parser-modal-body">
              {formError && <div className="parser-form-error">{formError}</div>}

              <div className="parser-form-row">
                <label htmlFor="parser-file-type">
                  File Type <em>*</em>
                </label>
                <select
                  id="parser-file-type"
                  className="parser-form-control parser-select-control"
                  value={form.type}
                  onChange={(event) => updateFileType(event.target.value)}
                >
                  <option value="">Select a file type</option>
                  {fileTypeOptions.map((item) => (
                    <option key={item.fileType} value={item.label}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="parser-form-row">
                <label htmlFor="parser-engine">
                  Linked Parser <em>*</em>
                </label>
                <select
                  id="parser-engine"
                  className="parser-form-control parser-select-control"
                  value={form.parserConfigId}
                  onChange={(event) => updateForm('parserConfigId', event.target.value)}
                >
                  <option value="">Select a parser</option>
                  {activeParsers.map((parser) => (
                    <option key={parser.id} value={parser.id} title={(parser.file_types || []).join(' / ')}>
                      {parser.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="parser-form-row">
                <label htmlFor="parser-prompt">
                  Prompt
                  <button type="button" className="parser-template-button" onClick={() => openTemplateModal('prompt')}>
                    <FileTextOutlined />
                    {t('compile.importFromTemplate')}
                  </button>
                </label>
                <textarea
                  id="parser-prompt"
                  className="parser-form-control parser-textarea"
                  value={form.prompt}
                  onChange={(event) => updateForm('prompt', event.target.value)}
                  placeholder="Enter instructions for processing this file type..."
                />
              </div>

              <div className="parser-form-row">
                <label>
                  Preprocessing
                  <span>(Select one or more methods; they run in the selected order)</span>
                </label>
                <div className="parser-skill-selector">
                  {form.preprocessing.length > 0 && (
                    <div className="parser-skill-tags">
                      {form.preprocessing.map((item) => (
                        <button key={item} type="button" onClick={() => removePreprocess(item)}>
                          {getProcessingLabel(item, t)}
                          <CloseOutlined />
                        </button>
                      ))}
                    </div>
                  )}
                  <button
                    type="button"
                    className="parser-skill-input-wrap"
                    onClick={() => setPreprocessOpen((open) => !open)}
                  >
                    <span>{form.preprocessing.length ? 'Select more preprocessing methods...' : 'Select preprocessing methods...'}</span>
                    <DownOutlined />
                  </button>
                  {preprocessOpen && (
                    <div className="parser-skill-dropdown">
                      {preprocessOptions.map((item) => (
                        <button
                          key={item.code}
                          type="button"
                          className={`parser-skill-option ${form.preprocessing.includes(item.code) ? 'is-checked' : ''}`}
                          onClick={() => togglePreprocess(item.code)}
                        >
                          <span className="parser-checkbox-box" />
                          {t(item.labelKey)}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="parser-modal-divider" />

              <div className="parser-form-row parser-post-row">
                <label>
                  Postprocessing
                  <span>(Select one or more postprocessing methods)</span>
                </label>
                <button
                  type="button"
                  className={`parser-checkbox ${form.postSummary ? 'is-checked' : ''}`}
                  onClick={() => updateForm('postSummary', !form.postSummary)}
                >
                  <span className="parser-checkbox-box" />
                  {t('parserConfig.autoSummary')}
                </button>
                {form.postSummary && (
                  <div className="parser-post-field">
                    <label htmlFor="parser-summary-prompt">
                      Summary Prompt
                      <button
                        type="button"
                        className="parser-template-button"
                        onClick={() => openTemplateModal('summaryPrompt')}
                      >
                        <FileTextOutlined />
                        {t('compile.importFromTemplate')}
                      </button>
                    </label>
                    <textarea
                      id="parser-summary-prompt"
                      className="parser-form-control parser-mini-textarea"
                      value={form.summaryPrompt}
                      onChange={(event) => updateForm('summaryPrompt', event.target.value)}
                      placeholder="Enter an automatic summary prompt..."
                    />
                  </div>
                )}
                <button
                  type="button"
                  className={`parser-checkbox ${form.postTag ? 'is-checked' : ''}`}
                  onClick={() => updateForm('postTag', !form.postTag)}
                >
                  <span className="parser-checkbox-box" />
                  {t('parserConfig.autoTag')}
                </button>
                {form.postTag && (
                  <div className="parser-post-field">
                    <label htmlFor="parser-tag-prompt">
                      Tag Prompt
                      <button
                        type="button"
                        className="parser-template-button"
                        onClick={() => openTemplateModal('tagPrompt')}
                      >
                        <FileTextOutlined />
                        {t('compile.importFromTemplate')}
                      </button>
                    </label>
                    <textarea
                      id="parser-tag-prompt"
                      className="parser-form-control parser-mini-textarea"
                      value={form.tagPrompt}
                      onChange={(event) => updateForm('tagPrompt', event.target.value)}
                      placeholder="Enter an automatic tagging prompt..."
                    />
                  </div>
                )}
              </div>
            </div>

            <div className="parser-modal-footer">
              <button type="button" className="parser-modal-cancel" onClick={closeFormModal}>
                Cancel
              </button>
              <button type="button" className="parser-modal-save" onClick={() => void saveForm()} disabled={saving}>
                <SaveFilled />
                {saving ? t('dataSource.loading') : t('common.save')}
              </button>
            </div>
          </div>
        </div>
      )}

      {deleteTarget && (
        <div className="parser-modal-mask">
          <div className="parser-modal parser-delete-modal" role="dialog" aria-modal="true">
            <div className="parser-delete-body">
              <div className="parser-delete-icon">
                <ExclamationCircleFilled />
              </div>
              <strong>{deleteTarget.type}</strong>
              <p>Delete this parser setting? This action cannot be undone.</p>
            </div>
            <div className="parser-modal-footer parser-delete-footer">
              <button type="button" className="parser-modal-cancel" onClick={() => setDeleteTarget(null)}>
                Cancel
              </button>
              <button type="button" className="parser-modal-danger" onClick={() => void confirmDelete()} disabled={saving}>
                {t('validation.confirmDelete')}
              </button>
            </div>
          </div>
        </div>
      )}

      {templateOpen && (
        <div className="parser-modal-mask parser-template-mask">
          <div className="parser-modal parser-template-modal" role="dialog" aria-modal="true">
            <div className="parser-modal-header">
              <h2>{t('compile.importFromTemplate')}</h2>
              <button type="button" className="parser-modal-close" onClick={() => setTemplateOpen(false)} aria-label="Close">
                <CloseOutlined />
              </button>
            </div>
            <div className="parser-modal-body">
              {templateError && <div className="parser-form-error">{templateError}</div>}
              {templateLoading ? (
                <div className="parser-template-state">{t('dataSource.loading')}</div>
              ) : templates.length === 0 ? (
                <div className="parser-template-state">No prompt templates available</div>
              ) : (
                <div className="parser-template-list">
                  {templates.map((template) => (
                    <button key={template.id} type="button" onClick={() => applyTemplate(template)}>
                      <span className="parser-template-icon">
                        <FileTextOutlined />
                      </span>
                      <span className="parser-template-info">
                        <strong>{template.name}</strong>
                        <span>{templateDesc(template)}</span>
                      </span>
                      <em>Use</em>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default function DomainKnowledgeParser() {
  return <ParserConfigContent />
}
