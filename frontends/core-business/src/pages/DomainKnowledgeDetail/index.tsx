import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { Input, Button, Table, Tag, Space, message, Modal, Form, InputNumber, Select, Alert } from 'antd'
import {
  PlusOutlined,
  ArrowLeftOutlined,
  DatabaseOutlined,
  ApiOutlined,
  ControlOutlined,
  CodeOutlined,
  BarChartOutlined,
  ThunderboltOutlined,
  GlobalOutlined,
  FileTextOutlined,
  ShareAltOutlined,
  RightOutlined,
  CloudOutlined,
  UploadOutlined,
  FolderOpenOutlined,
  VideoCameraOutlined,
  EditOutlined,
  BellOutlined,
  PictureOutlined,
  SoundOutlined,
  TeamOutlined,
  BugOutlined,
  EyeOutlined,
  SwapOutlined,
} from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import type {
  DomainKnowledgeDetail as DomainKnowledgeDetailType,
  DataSourceConfig,
  ActionRule,
  RuleTextSegment,
  OntologyInstanceSummary,
  RelationInstanceSummary,
  OntologyStatistics,
  DomainKnowledgePermissionMember,
} from '@/types/domainKnowledge'
import { statusTextMap } from '@/types/domainKnowledge'
import {
  getDomainKnowledgeDetail,
  getDomainKnowledgeDataSources,
  getDomainKnowledgeActionRules,
  getOntologyEntityTypes,
  getOntologyRelationTypes,
  getOntologyStatistics,
  getParserConfigs,
  getDomainKnowledgePermissions,
  saveDomainKnowledgePermissions,
  type ParserConfigItem,
} from '@/api/domainKnowledge'
import CompileTab from './compile/CompileTab'
import SynonymTab from './synonym/SynonymTab'
import AddDataSourceModal from '@/components/datasource/AddDataSourceModal'
import { deleteDataSource, updateDataSource } from '@/api/dataSource'
import { ParserConfigContent } from '@/pages/DomainKnowledgeParser'

const tabs = [
  { key: 'datasource', tKey: 'domainKnowledge.dataSourceSettings', icon: ApiOutlined },
  { key: 'parse', tKey: 'domainKnowledge.parserSettings', icon: ControlOutlined },
  { key: 'compile', tKey: 'domainKnowledge.compileSettings', icon: CodeOutlined },
  { key: 'result', tKey: 'domainKnowledge.results', icon: BarChartOutlined },
  { key: 'synonym', tKey: 'domainKnowledge.synonymSettings', icon: SwapOutlined },
  { key: 'permission', tKey: 'domainKnowledge.permissionSettings', icon: TeamOutlined },
]

const dataSourceIconMap: Record<string, React.ComponentType<any>> = {
  api: CloudOutlined,
  upload: UploadOutlined,
  storage: FolderOpenOutlined,
}

const dataSourceStatusView: Record<DataSourceConfig['status'], { color: string; tKey: string }> = {
  running: { color: 'success', tKey: 'dataSource.running' },
  paused: { color: 'warning', tKey: 'dataSource.paused' },
  error: { color: 'error', tKey: 'dataSource.error' },
}

const actionIconMap: Record<string, React.ComponentType<any>> = {
  video: VideoCameraOutlined,
  bell: BellOutlined,
  picture: PictureOutlined,
  file: FileTextOutlined,
  sound: SoundOutlined,
  bug: BugOutlined,
  team: TeamOutlined,
}

function renderRuleText(segments: RuleTextSegment[]): React.ReactNode {
  return segments.map((seg, i) =>
    seg.bold ? (
      <strong key={i} style={{ color: seg.color || '#0b2b5c' }}>
        {seg.text}
      </strong>
    ) : (
      <React.Fragment key={i}>{seg.text}</React.Fragment>
    ),
  )
}

export default function DomainKnowledgeDetail() {
  const { t } = useTranslation()
  const describeDataSource = (ds: DataSourceConfig): string => {
    const config = ds.configJson || {}
    if (ds.accessType === 'api') return `${t('dataSource.endpoint')}: ${config.endpoint || '-'}`
    if (ds.accessType === 'storage') {
      return `${config.backend || ''} | ${t('dataSource.bucket')}: ${config.bucket || '-'}${config.prefix ? ` / ${config.prefix}` : ''}`
    }
    if (ds.accessType === 'api_push') {
      return `${t('dataSource.apiPush')} | ${t('dataSource.documentType')}: ${(config.allowed_ext || []).join('/') || '-'}`
    }
    return t('dataSource.fileUpload')
  }
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('datasource')


  const [detail, setDetail] = useState<DomainKnowledgeDetailType | null>(null)
  const [detailLoading, setDetailLoading] = useState(true)


  const [dataSources, setDataSources] = useState<DataSourceConfig[]>([])
  const [dataSourcesLoading, setDataSourcesLoading] = useState(false)
  const [addDsOpen, setAddDsOpen] = useState(false)


const [editingDs, setEditingDs] = useState<DataSourceConfig | null>(null)
const [editingName, setEditingName] = useState('')
const [editingExtStr, setEditingExtStr] = useState('')
const [submittingEdit, setSubmittingEdit] = useState(false)

const getEditField = (key: string): any => {
  const cfg = editingDs?.configJson || {}
  if (key in cfg) return cfg[key]
  return ''
}
const setEditField = (key: string, value: any) => {
  if (!editingDs) return
  setEditingDs({ ...editingDs, configJson: { ...(editingDs.configJson || {}), [key]: value } })
}
const buildEditConfig = (): Record<string, any> => {
  const cfg = { ...(editingDs?.configJson || {}) }
  const at = editingDs?.accessType
  if (at === 'api') {
    const auth = cfg.auth || {}

    if (!auth.token) delete auth.token
    cfg.auth = auth
  }
  if (at === 'api_push') {
    cfg.allowed_ext = (editingExtStr || '').split(',').map((s: string) => s.trim()).filter(Boolean)
    cfg.max_file_mb = cfg.max_file_mb || 50
  }
  if (at === 'storage') {

    if (!cfg.credential) delete cfg.credential
    cfg.include_ext = (editingExtStr || '').split(',').map((s: string) => s.trim()).filter(Boolean)
  }
  return cfg
}

const openEditModal = (ds: DataSourceConfig) => {
  setEditingDs(ds)
  setEditingName(ds.name)
  const extArr = ds.accessType === 'api_push'
    ? (ds.configJson?.allowed_ext || [])
    : ds.accessType === 'storage'
      ? (ds.configJson?.include_ext || [])
      : []
  setEditingExtStr(Array.isArray(extArr) ? extArr.join(',') : String(extArr || ''))
}

  const reloadDataSources = useCallback(() => {
    if (!id) return
    setDataSourcesLoading(true)
    getDomainKnowledgeDataSources(id)
      .then(setDataSources)
      .catch((err: any) => message.error(err?.message || t('common.loadFailed')))
      .finally(() => setDataSourcesLoading(false))
  }, [id])


  const [ontologySummaries, setOntologySummaries] = useState<OntologyInstanceSummary[]>([])
  const [relationSummaries, setRelationSummaries] = useState<RelationInstanceSummary[]>([])
  const [resultStats, setResultStats] = useState<OntologyStatistics | null>(null)
  const [resultLoading, setResultLoading] = useState(false)


  const [actionRules, setActionRules] = useState<ActionRule[]>([])
  const [actionLoading, setActionLoading] = useState(false)


  const [permissionMembers, setPermissionMembers] = useState<DomainKnowledgePermissionMember[]>([])
  const [permissionLoading, setPermissionLoading] = useState(false)
  const [permissionSaving, setPermissionSaving] = useState(false)
  const [permissionKeyword, setPermissionKeyword] = useState('')
  const permDebounceRef = useRef<ReturnType<typeof setTimeout>>()

  const reloadPermissions = useCallback(() => {
    if (!id) return
    setPermissionLoading(true)
    getDomainKnowledgePermissions(id, permissionKeyword || undefined)
      .then((data) => setPermissionMembers(data.members))
      .catch((err: any) => message.error(err?.message || t('common.loadFailed')))
      .finally(() => setPermissionLoading(false))
  }, [id, permissionKeyword])

  const handlePermKeywordChange = (val: string) => {
    setPermissionKeyword(val)
    if (permDebounceRef.current) clearTimeout(permDebounceRef.current)
    permDebounceRef.current = setTimeout(() => {
      if (!id) return
      setPermissionLoading(true)
      getDomainKnowledgePermissions(id, val || undefined)
        .then((data) => setPermissionMembers(data.members))
        .catch(() => {   })
        .finally(() => setPermissionLoading(false))
    }, 300)
  }

  const handlePermRoleChange = (userId: string, role: 'view' | 'manage') => {
    setPermissionMembers((prev) =>
      prev.map((m) => (m.userId === userId ? { ...m, role } : m)),
    )
  }

  const handleSavePermissions = async () => {
    if (!id) return
    setPermissionSaving(true)
    try {
      await saveDomainKnowledgePermissions(id, {
        members: permissionMembers.map((m) => ({
          userId: m.userId,
          role: m.role,
        })),
      })
      message.success(t('domainKnowledge.permissionSaveSuccess'))
    } catch (err: any) {
      message.error(err?.message || t('domainKnowledge.permissionSaveFailed'))
    } finally {
      setPermissionSaving(false)
    }
  }

  const loadedTabsRef = useRef<Set<string>>(new Set())


  useEffect(() => {
    if (!id) return
    setDetailLoading(true)
    getDomainKnowledgeDetail(id)
      .then(setDetail)
      .catch((err: any) => message.error(err?.message || t('common.loadFailed')))
      .finally(() => setDetailLoading(false))
  }, [id])


  const loadTabData = useCallback(
    (tabKey: string) => {
      if (!id || loadedTabsRef.current.has(tabKey)) return
      loadedTabsRef.current.add(tabKey)

      switch (tabKey) {
        case 'datasource':
          setDataSourcesLoading(true)
          getDomainKnowledgeDataSources(id)
            .then(setDataSources)
            .catch((err: any) => message.error(err?.message || t('common.loadFailed')))
            .finally(() => setDataSourcesLoading(false))
          break

        case 'result':
          setResultLoading(true)
          Promise.all([
            getOntologyStatistics(id),
            getOntologyEntityTypes(id),
            getOntologyRelationTypes(id),
          ])
            .then(([stats, entityTypes, relationTypes]) => {
              setResultStats(stats)
              setOntologySummaries(entityTypes.items)
              setRelationSummaries(relationTypes.items)
            })
            .catch((err: any) => message.error(err?.message || t('common.loadFailed')))
            .finally(() => setResultLoading(false))
          break

        case 'action':
          setActionLoading(true)
          getDomainKnowledgeActionRules(id)
            .then(setActionRules)
            .catch((err: any) => message.error(err?.message || t('common.loadFailed')))
            .finally(() => setActionLoading(false))
          break

        case 'permission':
          setPermissionLoading(true)
          getDomainKnowledgePermissions(id)
            .then((data) => setPermissionMembers(data.members))
            .catch((err: any) => message.error(err?.message || t('common.loadFailed')))
            .finally(() => setPermissionLoading(false))
          break
      }
    },
    [id],
  )

  useEffect(() => {
    loadTabData(activeTab)
  }, [activeTab, loadTabData])


  const renderSectionHeader = (title: string, icon: React.ReactNode, showAdd = true) => (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 16,
      }}
    >
      <h3
        style={{
          margin: 0,
          fontSize: 15,
          fontWeight: 600,
          color: '#0b2b5c',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        {icon} {title}
      </h3>
      {showAdd && (
        <Button
          type="primary"
          style={{ padding: '6px 16px', fontSize: 13, height: 'auto' }}
          icon={<PlusOutlined />}
        >
          New {title.replace('Settings', '').replace('Management', '').replace('设置', '').replace('管理', '')}
        </Button>
      )}
    </div>
  )


  const renderTabContent = () => {
    switch (activeTab) {
      case 'datasource':
        return (
          <div
            className="config-section"
            style={{
              background: '#fff',
              borderRadius: 14,
              border: '1px solid #eef2f6',
              padding: 24,
              boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 16,
              }}
            >
              <h3
                style={{
                  margin: 0,
                  fontSize: 15,
                  fontWeight: 600,
                  color: '#0b2b5c',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <ApiOutlined style={{ color: '#3b82f6' }} /> {t('domainKnowledge.configuredDataSources')}
              </h3>
              <Button
                type="primary"
                style={{ padding: '6px 16px', fontSize: 13, height: 'auto' }}
                icon={<PlusOutlined />}
                onClick={() => setAddDsOpen(true)}
              >
                {t('dataSource.addDataSource')}
              </Button>
            </div>
            {dataSourcesLoading ? (
              <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>
                {t('dataSource.loading')}
              </div>
            ) : (
              dataSources.map((ds) => {
                const DsIcon = dataSourceIconMap[ds.iconType] || CloudOutlined
                return (
                  <div
                    key={ds.id}
                    onClick={() => navigate(ds.path)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 14,
                      padding: '14px 16px',
                      border: '1px solid #eef2f6',
                      borderRadius: 10,
                      marginBottom: 10,
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      textDecoration: 'none',
                      color: 'inherit',
                    }}
                    onMouseEnter={(e) => {
                      ;(e.currentTarget as HTMLElement).style.borderColor = '#dbe7f5'
                      ;(e.currentTarget as HTMLElement).style.background = '#fafcff'
                    }}
                    onMouseLeave={(e) => {
                      ;(e.currentTarget as HTMLElement).style.borderColor = '#eef2f6'
                      ;(e.currentTarget as HTMLElement).style.background = '#fff'
                    }}
                  >
                    <div
                      style={{
                        width: 40,
                        height: 40,
                        borderRadius: 8,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 18,
                        background: ds.iconBg,
                        color: ds.iconColor,
                        flexShrink: 0,
                      }}
                    >
                      <DsIcon />
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 14, fontWeight: 500, color: '#1e293b' }}>
                        {ds.name}{' '}
                        <span
                          style={{ fontSize: 12, color: '#94a3b8', fontWeight: 400 }}
                        >
                          · {t(ds.type)}
                        </span>
                      </div>
                      <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>
                        {describeDataSource(ds)}
                      </div>
                    </div>
                    <span
                      style={{ fontSize: 13, color: '#64748b', whiteSpace: 'nowrap' }}
                    >
                      <FileTextOutlined style={{ marginRight: 4 }} />
                      {t('domainKnowledge.documentsCount', { count: ds.docs })}
                    </span>
                    <Tag
                      color={dataSourceStatusView[ds.status].color}
                      style={{ fontSize: 11 }}
                    >
                      {t(dataSourceStatusView[ds.status].tKey)}
                    </Tag>
                    <span
                      style={{
                        fontSize: 12,
                        color: '#3b82f6',
                        cursor: 'pointer',
                        padding: '4px 12px',
                        borderRadius: 6,
                      }}
                      onClick={(e) => {
                        e.stopPropagation()
                        openEditModal(ds)
                      }}
                    >
                      {t('dataSource.edit')}
                    </span>
                    <span
                      style={{
                        fontSize: 12,
                        color: '#ef4444',
                        cursor: 'pointer',
                        padding: '4px 12px',
                        borderRadius: 6,
                      }}
                      onClick={(e) => {
                        e.stopPropagation()
                        Modal.confirm({
                          title: t('dataSource.deleteDocument'),
                          content: t('dataSource.deleteDataSourceConfirm', { name: ds.name }),
                          okText: t('dataSource.delete'),
                          cancelText: t('dataSource.cancel'),
                          okButtonProps: { danger: true },
                          onOk: async () => {
                            await deleteDataSource(ds.id)
                            message.success(t('common.deletedSuccess'))
                            reloadDataSources()
                          },
                        })
                      }}
                    >
                      {t('dataSource.delete')}
                    </span>
                    <RightOutlined style={{ fontSize: 12, color: '#94a3b8' }} />
                  </div>
                )
              })
            )}
          </div>
        )

      case 'parse':
        return <ParserConfigContent kbId={id} />

      case 'compile':
        return <CompileTab kbId={id!} />

      case 'synonym':
        return <SynonymTab kbId={id!} />

      case 'result':
        return (
          <div>
            { }
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3,1fr)',
                gap: 16,
                marginBottom: 20,
              }}
            >
              {((): Array<{ label: string; value: string; color: string }> => {
                if (resultStats) {
                  return [
                    { label: 'Source Files', value: resultStats.source_file_count.toLocaleString(), color: '#f97316' },
                    { label: 'Ontology Instances', value: resultStats.ontology_instance_count.toLocaleString(), color: '#3b82f6' },
                    { label: 'Ontology Relations', value: resultStats.ontology_relation_count.toLocaleString(), color: '#10b981' },
                  ]
                }
                return [
                  { label: 'Source Files', value: '--', color: '#f97316' },
                  { label: 'Ontology Instances', value: '--', color: '#3b82f6' },
                  { label: 'Ontology Relations', value: '--', color: '#10b981' },
                ]
              })().map((s) => (
                <div
                  key={s.label}
                  style={{
                    textAlign: 'center',
                    padding: 20,
                    background: '#f8fafc',
                    borderRadius: 10,
                    border: '1px solid #eef2f6',
                  }}
                >
                  <div style={{ fontSize: 28, fontWeight: 700, color: s.color }}>
                    {s.value}
                  </div>
                  <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 4 }}>
                    {s.label}
                  </div>
                </div>
              ))}
            </div>

            { }
            <div
              className="config-section"
              style={{
                background: '#fff',
                borderRadius: 14,
                border: '1px solid #eef2f6',
                padding: 24,
                marginBottom: 20,
                boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
              }}
            >
              <h3
                style={{
                  margin: '0 0 4px',
                  fontSize: 15,
                  fontWeight: 600,
                  color: '#0b2b5c',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <ShareAltOutlined style={{ color: '#3b82f6' }} /> Ontology Instances{' '}
                <span style={{ fontSize: 12, fontWeight: 400, color: '#94a3b8' }}>
                  (Entity instances extracted by AI)
                </span>
              </h3>
              <p style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16 }}>
                Displays ontology instances extracted by AI. View details to inspect all instances and attributes for an ontology type.
              </p>
              <Table
                columns={[
                  {
                    title: 'Name',
                    dataIndex: 'display_name',
                    key: 'display_name',
                    render: (v: string, r: OntologyInstanceSummary) => (
                      <span style={{ fontWeight: 600, color: '#0b2b5c' }}>{v || r.name}</span>
                    ),
                  },
                  { title: 'Description', dataIndex: 'description', key: 'description', render: (v: string) => <span style={{ color: '#64748b' }}>{v || '—'}</span> },
                  {
                    title: 'Build Status',
                    dataIndex: 'build_status',
                    key: 'build_status',
                    render: (v: string) => (
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '2px 10px',
                          borderRadius: 12,
                          fontSize: 12,
                          fontWeight: 500,
                          background: v === 'built' ? '#ecfdf5' : '#fef3c7',
                          color: v === 'built' ? '#059669' : '#d97706',
                        }}
                      >
                        {v === 'built' ? 'Built' : v === 'empty' ? 'Not Built' : v}
                      </span>
                    ),
                  },
                  {
                    title: 'Instances',
                    dataIndex: 'instance_count',
                    key: 'instance_count',
                    render: (v: number) => (
                      <span style={{ fontWeight: 600, color: '#3b82f6' }}>
                        {(v ?? 0).toLocaleString()}
                      </span>
                    ),
                  },
                  {
                    title: 'Actions',
                    key: 'actions',
                    width: 120,
                    render: (_: unknown, record: OntologyInstanceSummary) => (
                      <a
                        className="yx-table-action"
                        onClick={() =>
                          navigate(`/domain-knowledge/${id}/result/instances/${encodeURIComponent(record.name)}`)
                        }
                      >
                        View Details
                      </a>
                    ),
                  },
                ]}
                dataSource={ontologySummaries}
                rowKey="name"
                pagination={false}
                size="middle"
                loading={resultLoading}
              />
            </div>

            { }
            <div
              className="config-section"
              style={{
                background: '#fff',
                borderRadius: 14,
                border: '1px solid #eef2f6',
                padding: 24,
                marginBottom: 20,
                boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
              }}
            >
              <h3
                style={{
                  margin: '0 0 4px',
                  fontSize: 15,
                  fontWeight: 600,
                  color: '#0b2b5c',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <ShareAltOutlined style={{ color: '#8b5cf6' }} /> Relation Instances{' '}
                <span style={{ fontSize: 12, fontWeight: 400, color: '#94a3b8' }}>
                  (Relation instances extracted by AI)
                </span>
              </h3>
              <p style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16 }}>
                Displays relation instances extracted by AI. View details to inspect all instances for a relation type.
              </p>
              <Table
                columns={[
                  {
                    title: 'Source Object',
                    dataIndex: 'source_display_name',
                    key: 'source_display_name',
                    render: (v: string, r: RelationInstanceSummary) => (
                      <span
                        style={{
                          padding: '2px 8px',
                          borderRadius: 6,
                          background: '#eff6ff',
                          color: '#3b82f6',
                          fontSize: 12,
                          fontWeight: 500,
                        }}
                      >
                        {v || r.source || '—'}
                      </span>
                    ),
                  },
                  {
                    title: 'Relation Name',
                    dataIndex: 'display_name',
                    key: 'display_name',
                    render: (v: string, r: RelationInstanceSummary) => (
                      <strong style={{ color: '#0b2b5c' }}>{v || r.name}</strong>
                    ),
                  },
                  {
                    title: 'Target Object',
                    dataIndex: 'target_display_name',
                    key: 'target_display_name',
                    render: (v: string, r: RelationInstanceSummary) => (
                      <span
                        style={{
                          padding: '2px 8px',
                          borderRadius: 6,
                          background: '#ecfdf5',
                          color: '#059669',
                          fontSize: 12,
                          fontWeight: 500,
                        }}
                      >
                        {v || r.target || '—'}
                      </span>
                    ),
                  },
                  {
                    title: 'Description',
                    dataIndex: 'description',
                    key: 'description',
                    render: (v: string) => (
                      <span style={{ fontSize: 13, color: '#64748b' }}>{v || '—'}</span>
                    ),
                  },
                  {
                    title: 'Cardinality',
                    dataIndex: 'cardinality',
                    key: 'cardinality',
                    render: (v: string) => {
                      const colorMap: Record<string, { bg: string; color: string }> = {
                        'many_to_one': { bg: '#eff6ff', color: '#3b82f6' },
                        'many_to_many': { bg: '#fef3c7', color: '#d97706' },
                        'one_to_one': { bg: '#ecfdf5', color: '#059669' },
                        'one_to_many': { bg: '#eff6ff', color: '#3b82f6' },
                      }
                      const labelMap: Record<string, string> = {
                        'many_to_one': 'Many-to-One', 'many_to_many': 'Many-to-Many',
                        'one_to_one': 'One-to-One', 'one_to_many': 'One-to-Many',
                      }
                      const c = colorMap[v] || { bg: '#f1f5f9', color: '#64748b' }
                      return (
                        <span
                          style={{
                            padding: '2px 8px',
                            borderRadius: 6,
                            background: c.bg,
                            color: c.color,
                            fontSize: 12,
                            fontWeight: 500,
                          }}
                        >
                          {labelMap[v] || v}
                        </span>
                      )
                    },
                  },
                  {
                    title: 'Build Status',
                    dataIndex: 'build_status',
                    key: 'build_status',
                    render: (v: string) => (
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '2px 10px',
                          borderRadius: 12,
                          fontSize: 12,
                          fontWeight: 500,
                          background: v === 'built' ? '#ecfdf5' : '#fef3c7',
                          color: v === 'built' ? '#059669' : '#d97706',
                        }}
                      >
                        {v === 'built' ? 'Built' : v === 'empty' ? 'Not Built' : v}
                      </span>
                    ),
                  },
                  {
                    title: 'Instances',
                    dataIndex: 'instance_count',
                    key: 'instance_count',
                    render: (v: number) => (
                      <span style={{ fontWeight: 600, color: '#3b82f6' }}>
                        {(v ?? 0).toLocaleString()}
                      </span>
                    ),
                  },
                  {
                    title: 'Actions',
                    key: 'actions',
                    width: 120,
                    render: (_: unknown, record: RelationInstanceSummary) => (
                      <a
                        className="yx-table-action"
                        onClick={() =>
                          navigate(`/domain-knowledge/${id}/result/relations/${encodeURIComponent(record.name)}`)
                        }
                      >
                        View Details
                      </a>
                    ),
                  },
                ]}
                dataSource={relationSummaries}
                rowKey="name"
                pagination={false}
                size="middle"
                loading={resultLoading}
              />
            </div>

            { }
            <div
              className="config-section"
              style={{
                background: '#fff',
                borderRadius: 14,
                border: '1px solid #eef2f6',
                padding: 24,
                marginBottom: 20,
                boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <h3
                  style={{
                    margin: 0,
                    fontSize: 15,
                    fontWeight: 600,
                    color: '#0b2b5c',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <ShareAltOutlined style={{ color: '#8b5cf6' }} /> Ontology Graph
                </h3>
                <Button
                  type="primary"
                  style={{ padding: '6px 20px', fontSize: 13, height: 'auto' }}
                  icon={<EyeOutlined />}
                  onClick={() => navigate(`/domain-knowledge/${id}/graph`)}
                >
                  View Full Graph
                </Button>
              </div>
              <p style={{ fontSize: 13, color: '#94a3b8', marginBottom: 0, marginTop: 8 }}>
                View the complete semantic graph of ontology entities, attributes, and relations in this knowledge base.
              </p>
            </div>
          </div>
        )

      case 'action':
        return (
          <div
            className="config-section"
            style={{
              background: '#fff',
              borderRadius: 14,
              border: '1px solid #eef2f6',
              padding: 24,
              boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 16,
              }}
            >
              <h3
                style={{
                  margin: 0,
                  fontSize: 15,
                  fontWeight: 600,
                  color: '#0b2b5c',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <ThunderboltOutlined style={{ color: '#8b5cf6' }} /> Trigger Rules
              </h3>
              <Button
                type="primary"
                style={{ padding: '6px 16px', fontSize: 13, height: 'auto' }}
                icon={<PlusOutlined />}
              >
                New Rule
              </Button>
            </div>
            <p style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16 }}>
              Define actions that run automatically when parsing or compilation results meet specified conditions.
            </p>
            {actionLoading ? (
              <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>
                {t('dataSource.loading')}
              </div>
            ) : (
              actionRules.map((rule, i) => {
                const TrigIcon = actionIconMap[rule.triggerIconType] || BugOutlined
                const ActIcon = actionIconMap[rule.actionIconType] || BellOutlined
                return (
                  <div
                    key={rule.id}
                    style={{
                      border: '1px solid #eef2f6',
                      borderRadius: 10,
                      padding: '16px 20px',
                      marginBottom: 12,
                      background: '#fff',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <div
                        style={{ display: 'flex', alignItems: 'center', gap: 12 }}
                      >
                        <span
                          style={{
                            fontSize: 14,
                            fontWeight: 600,
                            color: '#0b2b5c',
                          }}
                        >
                          {rule.name}
                        </span>
                        <Tag
                          color={
                            rule.status === '启用' ? 'success' : 'warning'
                          }
                          style={{ fontSize: 11 }}
                        >
                          {rule.status}
                        </Tag>
                      </div>
                      <div
                        style={{ display: 'flex', alignItems: 'center', gap: 8 }}
                      >
                        <label
                          style={{
                            position: 'relative',
                            display: 'inline-block',
                            width: 36,
                            height: 20,
                            cursor: 'pointer',
                            margin: 0,
                          }}
                        >
                          <input
                            type="checkbox"
                            defaultChecked={rule.status === '启用'}
                            style={{ opacity: 0, width: 0, height: 0 }}
                          />
                          <span
                            style={{
                              position: 'absolute',
                              cursor: 'pointer',
                              top: 0,
                              left: 0,
                              right: 0,
                              bottom: 0,
                              background:
                                rule.status === '启用' ? '#3b82f6' : '#cbd5e1',
                              borderRadius: 20,
                              transition: '0.3s',
                            }}
                          />
                          <span
                            style={{
                              position: 'absolute',
                              height: 14,
                              width: 14,
                              left: rule.status === '启用' ? 19 : 3,
                              bottom: 3,
                              background: '#fff',
                              borderRadius: '50%',
                              transition: '0.3s',
                            }}
                          />
                        </label>
                        <a className="yx-table-action">{t('common.edit')}</a>
                        <a
                          className="yx-table-action"
                          style={{ color: '#ef4444' }}
                        >
                          {t('dataSource.delete')}
                        </a>
                      </div>
                    </div>
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: 20,
                        marginTop: 14,
                        paddingTop: 14,
                        borderTop: '1px solid #f1f5f9',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          gap: 10,
                          alignItems: 'flex-start',
                        }}
                      >
                        <div
                          style={{
                            width: 28,
                            height: 28,
                            borderRadius: '50%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: 13,
                            flexShrink: 0,
                            background: rule.triggerIconBg,
                            color: rule.triggerIconColor,
                          }}
                        >
                          <TrigIcon />
                        </div>
                        <div>
                          <div
                            style={{
                              fontSize: 11,
                              color: '#94a3b8',
                              textTransform: 'uppercase',
                              letterSpacing: 0.5,
                              marginBottom: 2,
                            }}
                          >
                            Trigger Condition
                          </div>
                          <div
                            style={{
                              fontSize: 13,
                              color: '#475569',
                              lineHeight: 1.5,
                            }}
                          >
                            {renderRuleText(rule.triggerText)}
                          </div>
                        </div>
                      </div>
                      <div
                        style={{
                          display: 'flex',
                          gap: 10,
                          alignItems: 'flex-start',
                        }}
                      >
                        <div
                          style={{
                            width: 28,
                            height: 28,
                            borderRadius: '50%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: 13,
                            flexShrink: 0,
                            background: rule.actionIconBg,
                            color: rule.actionIconColor,
                          }}
                        >
                          <ActIcon />
                        </div>
                        <div>
                          <div
                            style={{
                              fontSize: 11,
                              color: '#94a3b8',
                              textTransform: 'uppercase',
                              letterSpacing: 0.5,
                              marginBottom: 2,
                            }}
                          >
                            Action
                          </div>
                          <div
                            style={{
                              fontSize: 13,
                              color: '#475569',
                              lineHeight: 1.5,
                            }}
                          >
                            {renderRuleText(rule.actionText)}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        )

      case 'permission':
        return (
          <div
            className="config-section"
            style={{
              background: '#fff',
              borderRadius: 14,
              border: '1px solid #eef2f6',
              padding: 24,
              boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 16,
              }}
            >
              <h3
                style={{
                  margin: 0,
                  fontSize: 15,
                  fontWeight: 600,
                  color: '#0b2b5c',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <TeamOutlined style={{ color: '#3b82f6' }} /> Permissions
              </h3>
              <Button
                style={{ padding: '6px 16px', fontSize: 13, height: 'auto' }}
                icon={<PlusOutlined />}
                onClick={() => message.info(t('domainKnowledge.addMemberSoon'))}
              >
                Add Member
              </Button>
            </div>
            <p style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16 }}>
              Manage knowledge base access. Members can be Managers or Viewers.
            </p>
            {permissionLoading ? (
              <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>
                {t('dataSource.loading')}
              </div>
            ) : (
              <>
                <table
                  style={{
                    width: '100%',
                    borderCollapse: 'collapse',
                    fontSize: 13,
                  }}
                >
                  <thead>
                    <tr>
                      <th
                        style={{
                          textAlign: 'left',
                          padding: '10px 12px',
                          fontWeight: 600,
                          color: '#64748b',
                          borderBottom: '2px solid #e8edf3',
                          fontSize: 12,
                        }}
                      >
                        User
                      </th>
                      <th
                        style={{
                          textAlign: 'left',
                          padding: '10px 12px',
                          fontWeight: 600,
                          color: '#64748b',
                          borderBottom: '2px solid #e8edf3',
                          fontSize: 12,
                        }}
                      >
                        Role
                      </th>
                      <th
                        style={{
                          textAlign: 'left',
                          padding: '10px 12px',
                          fontWeight: 600,
                          color: '#64748b',
                          borderBottom: '2px solid #e8edf3',
                          fontSize: 12,
                        }}
                      >
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {permissionMembers.map((u) => (
                      <tr key={u.userId}>
                        <td
                          style={{
                            padding: '10px 12px',
                            borderBottom: '1px solid #f1f5f9',
                          }}
                        >
                          <div style={{ fontWeight: 500, color: '#0b2b5c' }}>
                            {u.name}
                          </div>
                        </td>
                        <td
                          style={{
                            padding: '10px 12px',
                            borderBottom: '1px solid #f1f5f9',
                          }}
                        >
                          <select
                            value={u.role}
                            onChange={(e) =>
                              handlePermRoleChange(
                                u.userId,
                                e.target.value as 'view' | 'manage',
                              )
                            }
                            style={{
                              padding: '6px 28px 6px 12px',
                              border: '1px solid #d1d5db',
                              borderRadius: 6,
                              fontSize: 13,
                              color: '#0b2b5c',
                              background: '#fff',
                              cursor: 'pointer',
                              outline: 'none',
                            }}
                          >
                            <option value="manage">Manager</option>
                            <option value="view">Viewer</option>
                          </select>
                        </td>
                        <td
                          style={{
                            padding: '10px 12px',
                            borderBottom: '1px solid #f1f5f9',
                          }}
                        >
                          <a
                            className="yx-table-action"
                            style={{ cursor: 'pointer' }}
                            onClick={() => {
                              setPermissionMembers((prev) =>
                                prev.filter((m) => m.userId !== u.userId),
                              )
                            }}
                          >
                            Remove
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                { }
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'flex-end',
                    gap: 12,
                    marginTop: 20,
                    paddingTop: 16,
                    borderTop: '1px solid #eef2f6',
                  }}
                >
                  <Button
                    type="primary"
                    loading={permissionSaving}
                    onClick={handleSavePermissions}
                  >
                    Save Permissions
                  </Button>
                </div>
              </>
            )}
          </div>
        )

      default:
        return null
    }
  }


  return (
    <div
      style={{
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif',
        color: '#1e293b',
        letterSpacing: 0,
      }}
    >
      { }
      <div style={{ marginBottom: 16 }}>
        <a
          onClick={() => navigate('/domain-knowledge')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            fontSize: 14,
            color: '#64748b',
            cursor: 'pointer',
            padding: '4px 0',
          }}
        >
          <ArrowLeftOutlined style={{ fontSize: 12 }} /> Back to Knowledge Bases
        </a>
      </div>

      { }
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          marginBottom: 24,
          padding: '20px 24px',
          background: '#fff',
          borderRadius: 14,
          border: '1px solid #eef2f6',
          boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
        }}
      >
        <div
          style={{
            width: 52,
            height: 52,
            borderRadius: 12,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 24,
            background: '#eff6ff',
            color: '#3b82f6',
            flexShrink: 0,
          }}
        >
          <DatabaseOutlined />
        </div>
        {detailLoading ? (
          <div style={{ flex: 1 }}>
            <h2
              style={{
                fontSize: 20,
                fontWeight: 700,
                color: '#0b2b5c',
                margin: 0,
              }}
            >
              {t('dataSource.loading')}
            </h2>
          </div>
        ) : detail ? (
          <>
            <div style={{ flex: 1 }}>
              <h2
                style={{
                  fontSize: 20,
                  fontWeight: 700,
                  color: '#0b2b5c',
                  margin: 0,
                }}
              >
                {detail.name}
              </h2>
              <div
                style={{
                  display: 'flex',
                  gap: 8,
                  marginTop: 6,
                  flexWrap: 'wrap',
                }}
              >
                <span
                  style={{
                    fontSize: 12,
                    padding: '3px 10px',
                    borderRadius: 6,
                    background: '#f1f5f9',
                    color: '#64748b',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                  }}
                >
                  <GlobalOutlined style={{ color: '#3b82f6' }} />{' '}
                  {detail.spaceName}
                </span>
                <span
                  style={{
                    fontSize: 12,
                    padding: '3px 10px',
                    borderRadius: 6,
                    background: '#f1f5f9',
                    color: '#64748b',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                  }}
                >
                  <FileTextOutlined /> {t('domainKnowledge.documentsCount', { count: detail.documentCount })}
                </span>
                <span
                  style={{
                    fontSize: 12,
                    padding: '3px 10px',
                    borderRadius: 6,
                    background: '#f1f5f9',
                    color: '#64748b',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                  }}
                >
                  <ShareAltOutlined /> {detail.entityCount.toLocaleString()} {t('domainKnowledge.entityCount')}
                </span>
                <span
                  style={{
                    fontSize: 12,
                    padding: '3px 10px',
                    borderRadius: 6,
                    background: '#f1f5f9',
                    color: '#64748b',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                  }}
                >
                  <ShareAltOutlined /> {detail.relationCount.toLocaleString()} {t('domainKnowledge.relationCount')}
                </span>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div
                style={{
                  fontSize: 14,
                  fontWeight: 600,
                  color:
                    detail.status === 'synced'
                      ? '#10b981'
                      : detail.status === 'failed'
                        ? '#ef4444'
                        : '#f59e0b',
                }}
              >
                {t(statusTextMap[detail.status])}
              </div>
              <div
                style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}
              >
                {t('domainKnowledge.lastUpdated', { time: detail.updatedAt })}
              </div>
            </div>
          </>
        ) : null}
      </div>

      { }
      <div
        style={{
          display: 'flex',
          gap: 0,
          borderBottom: '2px solid #e2e8f0',
          marginBottom: 24,
        }}
      >
        {tabs.map((tab) => {
          const Icon = tab.icon
          const active = activeTab === tab.key
          return (
            <div
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                padding: '12px 24px',
                fontSize: 14,
                fontWeight: 500,
                color: active ? '#3b82f6' : '#64748b',
                cursor: 'pointer',
                borderBottom: `2px solid ${active ? '#3b82f6' : 'transparent'}`,
                marginBottom: -2,
                transition: 'all 0.2s ease',
                userSelect: 'none',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <Icon /> {t(tab.tKey)}
            </div>
          )
        })}
      </div>

      { }
      {renderTabContent()}

      { }
      <Modal
        wrapClassName="yx-domain-space-modal"
        title={
          <span>
            <EditOutlined style={{ color: '#3b82f6', marginRight: 8 }} />
            {t('dataSource.editDataSource')}
          </span>
        }
        open={!!editingDs}
        onCancel={() => setEditingDs(null)}
        onOk={async () => {
          if (!editingDs || !editingName.trim()) {
            message.warning(t('validation.nameRequired'))
            return
          }
          setSubmittingEdit(true)
          try {
            const cfg = buildEditConfig()
            await updateDataSource(editingDs.id, { name: editingName.trim(), config_json: cfg })
            message.success(t('common.updatedSuccess'))
            setEditingDs(null)
            reloadDataSources()
          } catch (err: any) {
            message.error(err?.message || t('common.updateFailed'))
          } finally {
            setSubmittingEdit(false)
          }
        }}
        confirmLoading={submittingEdit}
        okText={t('common.save')}
        cancelText={t('dataSource.cancel')}
        width={560}
      >
        <div style={{ marginBottom: 16, fontSize: 13, color: '#64748b' }}>
          {t('dataSource.accessMethod')}：<strong>{editingDs ? t(editingDs.type) : ''}</strong>
        </div>
        <Form layout="vertical">
          <Form.Item label="Data Source Name" required>
            <Input
              value={editingName}
              onChange={(e) => setEditingName(e.target.value)}
              placeholder="Enter a data source name"
            />
          </Form.Item>

          {editingDs?.accessType === 'api' && (
            <>
              <Form.Item label="Endpoint URL">
                <Input value={getEditField('endpoint')} onChange={(v) => setEditField('endpoint', v.target.value)} placeholder="https://api.example.com/documents" />
              </Form.Item>
              <Form.Item label="HTTP Method">
                <Select value={getEditField('method') || 'GET'} onChange={(v) => setEditField('method', v)} options={[{ value: 'GET', label: 'GET' }, { value: 'POST', label: 'POST' }]} />
              </Form.Item>
              <Form.Item label="Authentication">
                <Select
                  value={(editingDs?.configJson?.auth?.type) || 'none'}
                  onChange={(v) => setEditField('auth', { ...(editingDs?.configJson?.auth || {}), type: v })}
                  options={[
                    { value: 'none', label: 'None (Public API)' },
                    { value: 'bearer', label: 'Bearer Token' },
                    { value: 'api_key', label: 'API Key' },
                    { value: 'basic', label: 'Basic (username:password)' },
                  ]}
                />
              </Form.Item>
              <Form.Item label="Credential / Token" tooltip="Stored encrypted. Leave blank to keep the current value; enter a new value to replace it.">
                <Input.Password
                  placeholder="Enter a new credential (leave blank to keep current)"
                  onChange={(v) => setEditField('auth', { ...(editingDs?.configJson?.auth || {}), token: v.target.value })}
                />
              </Form.Item>
              <Form.Item label="API Key Header Name">
                <Input value={getEditField('auth')?.header_name || ''} onChange={(v) => setEditField('auth', { ...(editingDs?.configJson?.auth || {}), header_name: v.target.value })} placeholder="X-API-Key" />
              </Form.Item>
              <Form.Item label="Document List JSONPath">
                <Input value={getEditField('list_path') || '$.data.items'} onChange={(v) => setEditField('list_path', v.target.value)} placeholder="$.data.items" />
              </Form.Item>
              <Form.Item label="Download URL Field">
                <Input value={getEditField('file_url_field') || 'url'} onChange={(v) => setEditField('file_url_field', v.target.value)} placeholder="url" />
              </Form.Item>
              <Form.Item label="File Name Field">
                <Input value={getEditField('file_name_field') || 'name'} onChange={(v) => setEditField('file_name_field', v.target.value)} placeholder="name" />
              </Form.Item>
            </>
          )}

          {editingDs?.accessType === 'storage' && (
            <>
              <Form.Item label="Storage Backend">
                <Select value={getEditField('backend') || 'minio'} onChange={(v) => setEditField('backend', v)} options={[
                    { value: 'minio', label: 'MinIO' },
                    { value: 's3', label: 'AWS S3' },
                    { value: 'cos', label: 'Tencent Cloud COS' },
                    { value: 'oss', label: 'Alibaba Cloud OSS' },
                  ]} />
              </Form.Item>
              <Form.Item label="Endpoint">
                <Input value={getEditField('endpoint')} onChange={(v) => setEditField('endpoint', v.target.value)} placeholder="http://minio:9000" />
              </Form.Item>
              <Form.Item label="Bucket">
                <Input value={getEditField('bucket')} onChange={(v) => setEditField('bucket', v.target.value)} placeholder="product-files" />
              </Form.Item>
              <Form.Item label="Prefix">
                <Input value={getEditField('prefix')} onChange={(v) => setEditField('prefix', v.target.value)} placeholder="kb/finance/" />
              </Form.Item>
              <Form.Item label="Credential (AK:SK)" tooltip="Stored encrypted. Leave blank to keep the current value; enter a new value to replace it.">
                <Input.Password
                  placeholder="Enter a new credential (leave blank to keep current)"
                  onChange={(v) => setEditField('credential', v.target.value)}
                />
              </Form.Item>
              <Form.Item label="Included Extensions (comma-separated)">
                <Input.TextArea autoSize={{ minRows: 2, maxRows: 4 }} value={editingExtStr} onChange={(e) => setEditingExtStr(e.target.value)} />
              </Form.Item>
            </>
          )}

          {editingDs?.accessType === 'api_push' && (
            <>
              <Form.Item label="Allowed File Types (comma-separated)">
                <Input.TextArea autoSize={{ minRows: 2, maxRows: 4 }} value={editingExtStr} onChange={(e) => setEditingExtStr(e.target.value)} />
              </Form.Item>
              <Form.Item label="Maximum File Size (MB)">
                <InputNumber min={1} max={500} value={Number(getEditField('max_file_mb')) || 50} onChange={(v) => setEditField('max_file_mb', v ?? 50)} style={{ width: '100%' }} />
              </Form.Item>
            </>
          )}

          {editingDs?.accessType === 'file' && (
            <Alert
              type="info"
              showIcon
              style={{ marginTop: 4 }}
              description="File upload requires no additional configuration. Select files on the upload page. PDF, Office documents, images, audio, and video are supported."
            />
          )}
        </Form>
      </Modal>

      <AddDataSourceModal
        open={addDsOpen}
        kbId={id!}
        existingTypes={dataSources.map((ds) => ds.accessType)}
        onClose={() => setAddDsOpen(false)}
        onCreated={() => {
          setAddDsOpen(false)
          reloadDataSources()
        }}
      />
    </div>
  )
}
