import React, { useState, useEffect, useCallback, useRef } from 'react'
import { Input, Button, Table, Tag, Select, Space, message } from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
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
  FilePdfOutlined,
  FileWordOutlined,
  FileExcelOutlined,
  FileImageOutlined,
  AudioOutlined,
  VideoCameraOutlined,
  FileOutlined,
  BellOutlined,
  PictureOutlined,
  SoundOutlined,
  TeamOutlined,
  BugOutlined,
  CheckCircleOutlined,
  MessageOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import type {
  DomainKnowledgeDetail as DomainKnowledgeDetailType,
  DataSourceConfig,
  ParserFileConfig,
  OntologyTemplate,
  ValidationRule,
  PromptTemplate,
  CompileEntity,
  EntityDistribution,
  RelationDistribution,
  LogicRule,
  ActionRule,
  DomainKnowledgeResultStats,
  GraphSummary,
  RuleTextSegment,
} from '@/types/domainKnowledge'
import { statusTextMap, severityColorMap } from '@/types/domainKnowledge'
import {
  getDomainKnowledgeDetail,
  getDomainKnowledgeDataSources,
  getDomainKnowledgeParserConfigs,
  getDomainKnowledgeOntologyTemplates,
  getDomainKnowledgeValidationRules,
  getDomainKnowledgePrompts,
  getDomainKnowledgeEntities,
  getDomainKnowledgeEntityDistribution,
  getDomainKnowledgeRelationDistribution,
  getDomainKnowledgeLogicRules,
  getDomainKnowledgeActionRules,
  getDomainKnowledgeResultStats,
  getDomainKnowledgeGraphSummary,
} from '@/api/domainKnowledge'

const ENTITY_PAGE_SIZE = 6

const tabs = [
  { key: 'datasource', label: '数据源设置', icon: ApiOutlined },
  { key: 'parse', label: '解析引擎设置', icon: ControlOutlined },
  { key: 'compile', label: '编译引擎设置', icon: CodeOutlined },
  { key: 'result', label: '领域知识结果', icon: BarChartOutlined },
  // { key: 'action', label: 'Action', icon: ThunderboltOutlined },
]

const dataSourceIconMap: Record<string, React.ComponentType<any>> = {
  api: CloudOutlined,
  upload: UploadOutlined,
  storage: FolderOpenOutlined,
}

const parserFileIconMap: Record<string, React.ComponentType<any>> = {
  pdf: FilePdfOutlined,
  word: FileWordOutlined,
  excel: FileExcelOutlined,
  ppt: FileOutlined,
  image: FileImageOutlined,
  audio: AudioOutlined,
  video: VideoCameraOutlined,
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
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('datasource')

  // ── detail header ────────────────────────────────────
  const [detail, setDetail] = useState<DomainKnowledgeDetailType | null>(null)
  const [detailLoading, setDetailLoading] = useState(true)

  // ── datasource tab ────────────────────────────────────
  const [dataSources, setDataSources] = useState<DataSourceConfig[]>([])
  const [dataSourcesLoading, setDataSourcesLoading] = useState(false)

  // ── parse tab ─────────────────────────────────────────
  const [parserConfigs, setParserConfigs] = useState<ParserFileConfig[]>([])
  const [parserConfigsLoading, setParserConfigsLoading] = useState(false)

  // ── compile tab ───────────────────────────────────────
  const [ontologyTemplates, setOntologyTemplates] = useState<OntologyTemplate[]>([])
  const [validationRules, setValidationRules] = useState<ValidationRule[]>([])
  const [prompts, setPrompts] = useState<PromptTemplate[]>([])
  const [compileLoading, setCompileLoading] = useState(false)

  // ── result tab ────────────────────────────────────────
  const [entities, setEntities] = useState<CompileEntity[]>([])
  const [entityTotal, setEntityTotal] = useState(0)
  const [entityPage, setEntityPage] = useState(1)
  const [entityKeywordInput, setEntityKeywordInput] = useState('')
  const [entityKeyword, setEntityKeyword] = useState('')
  const [entityType, setEntityType] = useState('全部类型')
  const [entityLoading, setEntityLoading] = useState(false)

  const [entityDistribution, setEntityDistribution] = useState<EntityDistribution[]>([])
  const [relationDistribution, setRelationDistribution] = useState<RelationDistribution[]>([])
  const [logicRules, setLogicRules] = useState<LogicRule[]>([])
  const [resultStats, setResultStats] = useState<DomainKnowledgeResultStats | null>(null)
  const [graphSummary, setGraphSummary] = useState<GraphSummary | null>(null)
  const [resultLoading, setResultLoading] = useState(false)

  // ── action tab ────────────────────────────────────────
  const [actionRules, setActionRules] = useState<ActionRule[]>([])
  const [actionLoading, setActionLoading] = useState(false)

  const loadedTabsRef = useRef<Set<string>>(new Set())
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  // ── fetch detail ──────────────────────────────────────
  useEffect(() => {
    if (!id) return
    setDetailLoading(true)
    getDomainKnowledgeDetail(id)
      .then(setDetail)
      .catch((err: any) => message.error(err?.message || '获取知识库详情失败'))
      .finally(() => setDetailLoading(false))
  }, [id])

  // ── load tab data lazily ──────────────────────────────
  const loadTabData = useCallback(
    (tabKey: string) => {
      if (!id || loadedTabsRef.current.has(tabKey)) return
      loadedTabsRef.current.add(tabKey)

      switch (tabKey) {
        case 'datasource':
          setDataSourcesLoading(true)
          getDomainKnowledgeDataSources(id)
            .then(setDataSources)
            .catch((err: any) => message.error(err?.message || '获取数据源失败'))
            .finally(() => setDataSourcesLoading(false))
          break

        case 'parse':
          setParserConfigsLoading(true)
          getDomainKnowledgeParserConfigs(id)
            .then(setParserConfigs)
            .catch((err: any) => message.error(err?.message || '获取解析配置失败'))
            .finally(() => setParserConfigsLoading(false))
          break

        case 'compile':
          setCompileLoading(true)
          Promise.all([
            getDomainKnowledgeOntologyTemplates(id),
            getDomainKnowledgeValidationRules(id),
            getDomainKnowledgePrompts(id),
          ])
            .then(([templates, rules, promptsData]) => {
              setOntologyTemplates(templates)
              setValidationRules(rules)
              setPrompts(promptsData)
            })
            .catch((err: any) => message.error(err?.message || '获取编译配置失败'))
            .finally(() => setCompileLoading(false))
          break

        case 'result':
          setResultLoading(true)
          Promise.all([
            getDomainKnowledgeResultStats(id),
            getDomainKnowledgeGraphSummary(id),
            getDomainKnowledgeLogicRules(id),
          ])
            .then(([stats, graph, rulesData]) => {
              setResultStats(stats)
              setGraphSummary(graph)
              setLogicRules(rulesData)
              // derive distributions from graph summary
              getDomainKnowledgeEntityDistribution().then(setEntityDistribution)
              getDomainKnowledgeRelationDistribution().then(setRelationDistribution)
            })
            .catch((err: any) => message.error(err?.message || '获取结果数据失败'))
            .finally(() => setResultLoading(false))
          // entities are fetched separately with pagination
          fetchEntities(1, '', '全部类型')
          break

        case 'action':
          setActionLoading(true)
          getDomainKnowledgeActionRules(id)
            .then(setActionRules)
            .catch((err: any) => message.error(err?.message || '获取触发规则失败'))
            .finally(() => setActionLoading(false))
          break
      }
    },
    [id],
  )

  useEffect(() => {
    loadTabData(activeTab)
  }, [activeTab, loadTabData])

  // ── entity fetch with pagination ──────────────────────
  const fetchEntities = useCallback(
    async (page: number, keyword: string, type: string) => {
      if (!id) return
      setEntityLoading(true)
      try {
        const result = await getDomainKnowledgeEntities({
          knowledgeBaseId: id,
          page,
          pageSize: ENTITY_PAGE_SIZE,
          keyword: keyword || undefined,
          entityType: type !== '全部类型' ? type : undefined,
        })
        setEntities(result.list)
        setEntityTotal(result.pagination.total)
      } catch (err: any) {
        message.error(err?.message || '获取实体列表失败')
      } finally {
        setEntityLoading(false)
      }
    },
    [id],
  )

  // entity keyword debounce
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setEntityKeyword(entityKeywordInput)
    }, 300)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [entityKeywordInput])

  // entity filters change → reload page 1
  useEffect(() => {
    if (activeTab === 'result') {
      fetchEntities(1, entityKeyword, entityType)
      setEntityPage(1)
    }
  }, [entityKeyword, entityType, activeTab, fetchEntities])

  // entity pagination change
  useEffect(() => {
    if (activeTab === 'result' && entityPage !== 1) {
      fetchEntities(entityPage, entityKeyword, entityType)
    }
  }, [entityPage])

  // ── render helpers ────────────────────────────────────
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
          新建{title.replace('设置', '').replace('管理', '')}
        </Button>
      )}
    </div>
  )

  const entityTotalPages = Math.max(1, Math.ceil(entityTotal / ENTITY_PAGE_SIZE))

  const entityPageNumbers = (): number[] => {
    const pages: number[] = []
    for (let i = 1; i <= entityTotalPages; i++) pages.push(i)
    return pages
  }

  // ── render tab content ────────────────────────────────
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
                <ApiOutlined style={{ color: '#3b82f6' }} /> 已配置数据源
              </h3>
              <Button
                type="primary"
                style={{ padding: '6px 16px', fontSize: 13, height: 'auto' }}
                icon={<PlusOutlined />}
              >
                添加数据源
              </Button>
            </div>
            {dataSourcesLoading ? (
              <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>
                加载中...
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
                          · {ds.type}
                        </span>
                      </div>
                      <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>
                        {ds.desc}
                      </div>
                    </div>
                    <span
                      style={{ fontSize: 13, color: '#64748b', whiteSpace: 'nowrap' }}
                    >
                      <FileTextOutlined style={{ marginRight: 4 }} />
                      {ds.docs} 文档
                    </span>
                    <Tag
                      color={ds.status === '运行中' ? 'success' : 'warning'}
                      style={{ fontSize: 11 }}
                    >
                      {ds.status}
                    </Tag>
                    <span
                      style={{
                        fontSize: 12,
                        color: '#3b82f6',
                        cursor: 'pointer',
                        padding: '4px 12px',
                        borderRadius: 6,
                      }}
                      onClick={(e) => e.stopPropagation()}
                    >
                      编辑
                    </span>
                    <span
                      style={{
                        fontSize: 12,
                        color: '#ef4444',
                        cursor: 'pointer',
                        padding: '4px 12px',
                        borderRadius: 6,
                      }}
                      onClick={(e) => e.stopPropagation()}
                    >
                      删除
                    </span>
                    <RightOutlined style={{ fontSize: 12, color: '#94a3b8' }} />
                  </div>
                )
              })
            )}
          </div>
        )

      case 'parse':
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
            <h3
              style={{
                fontSize: 15,
                fontWeight: 600,
                color: '#0b2b5c',
                marginBottom: 16,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <ControlOutlined style={{ color: '#8b5cf6' }} /> 文件类解析配置
            </h3>
            <Table
              columns={[
                {
                  title: '文件类型',
                  dataIndex: 'type',
                  key: 'type',
                  render: (v: string, r: ParserFileConfig) => {
                    const PIcon = parserFileIconMap[r.iconType] || FileOutlined
                    return (
                      <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <PIcon style={{ color: r.iconColor, width: 18 }} /> {v}
                      </span>
                    )
                  },
                },
                { title: '解析器', dataIndex: 'parser', key: 'parser' },
                {
                  title: '状态',
                  dataIndex: 'status',
                  key: 'status',
                  render: (v: string) => (
                    <Tag color={v === '启用' ? 'success' : 'warning'}>{v}</Tag>
                  ),
                },
                {
                  title: '操作',
                  key: 'actions',
                  render: () => <a className="yx-table-action">配置</a>,
                },
              ]}
              dataSource={parserConfigs}
              rowKey="type"
              pagination={false}
              size="middle"
              loading={parserConfigsLoading}
            />
          </div>
        )

      case 'compile':
        return (
          <div>
            {false && (
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
              {renderSectionHeader(
                '本体模板设置',
                <ShareAltOutlined style={{ color: '#8b5cf6' }} />,
              )}
              <p style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16 }}>
                定义知识库中实体类型、属性及关系的本体结构模板
              </p>
              <Table
                columns={[
                  {
                    title: '实体类型',
                    dataIndex: 'type',
                    key: 'type',
                    render: (v: string) => (
                      <span style={{ fontWeight: 500, color: '#0b2b5c' }}>{v}</span>
                    ),
                  },
                  {
                    title: '属性定义',
                    dataIndex: 'attrs',
                    key: 'attrs',
                    render: (v: string) => (
                      <span style={{ fontSize: 12, color: '#64748b' }}>{v}</span>
                    ),
                  },
                  {
                    title: '关系类型',
                    dataIndex: 'relations',
                    key: 'relations',
                    render: (v: string) => (
                      <span style={{ fontSize: 12, color: '#64748b' }}>{v}</span>
                    ),
                  },
                  { title: '版本', dataIndex: 'version', key: 'version' },
                  {
                    title: '状态',
                    dataIndex: 'status',
                    key: 'status',
                    render: (v: string) => (
                      <Tag color={v === '已发布' ? 'success' : 'warning'}>{v}</Tag>
                    ),
                  },
                  {
                    title: '操作',
                    key: 'actions',
                    render: () => (
                      <Space>
                        <a className="yx-table-action">编辑</a>
                        <a className="yx-table-action">配置</a>
                      </Space>
                    ),
                  },
                ]}
                dataSource={ontologyTemplates}
                rowKey="id"
                pagination={false}
                size="middle"
                loading={compileLoading}
              />
            </div>
            )}

            {false && (
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
              {renderSectionHeader(
                '本体验证规则设置',
                <CheckCircleOutlined style={{ color: '#10b981' }} />,
              )}
              <p style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16 }}>
                配置实体和关系的校验规则，确保知识抽取质量符合标准
              </p>
              <Table
                columns={[
                  {
                    title: '规则名称',
                    dataIndex: 'name',
                    key: 'name',
                    render: (v: string) => (
                      <span style={{ fontWeight: 500, color: '#0b2b5c' }}>{v}</span>
                    ),
                  },
                  { title: '适用实体', dataIndex: 'entity', key: 'entity' },
                  {
                    title: '验证条件',
                    dataIndex: 'condition',
                    key: 'condition',
                    render: (v: string) => (
                      <span style={{ fontSize: 12, color: '#64748b' }}>{v}</span>
                    ),
                  },
                  {
                    title: '严重级别',
                    dataIndex: 'severity',
                    key: 'severity',
                    render: (v: string) => (
                      <Tag color={severityColorMap[v as keyof typeof severityColorMap]}>
                        {v}
                      </Tag>
                    ),
                  },
                  {
                    title: '状态',
                    dataIndex: 'status',
                    key: 'status',
                    render: (v: string) => (
                      <Tag color={v === '启用' ? 'success' : 'warning'}>{v}</Tag>
                    ),
                  },
                  {
                    title: '操作',
                    key: 'actions',
                    render: () => <a className="yx-table-action">编辑</a>,
                  },
                ]}
                dataSource={validationRules}
                rowKey="id"
                pagination={false}
                size="middle"
                loading={compileLoading}
              />
            </div>
            )}

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
              {renderSectionHeader(
                '提示词管理',
                <MessageOutlined style={{ color: '#3b82f6' }} />,
              )}
              <p style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16 }}>
                管理知识编译过程中各环节使用的 LLM 提示词模板
              </p>
              <Table
                columns={[
                  {
                    title: '提示词名称',
                    dataIndex: 'name',
                    key: 'name',
                    render: (v: string) => (
                      <span
                        style={{
                          fontWeight: 500,
                          color: '#0b2b5c',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                        }}
                      >
                        <MessageOutlined
                          style={{ color: '#8b5cf6', fontSize: 11 }}
                        />
                        {v}
                      </span>
                    ),
                  },
                  {
                    title: '使用环节',
                    dataIndex: 'stage',
                    key: 'stage',
                    render: (v: string) => (
                      <span style={{ fontSize: 12, color: '#64748b' }}>{v}</span>
                    ),
                  },
                  { title: '模型', dataIndex: 'model', key: 'model' },
                  { title: '更新人', dataIndex: 'author', key: 'author' },
                  { title: '更新时间', dataIndex: 'date', key: 'date' },
                  {
                    title: '状态',
                    dataIndex: 'status',
                    key: 'status',
                    render: (v: string) => (
                      <Tag color={v === '已发布' ? 'success' : 'warning'}>{v}</Tag>
                    ),
                  },
                  {
                    title: '操作',
                    key: 'actions',
                    render: () => (
                      <Space>
                        <a className="yx-table-action">编辑</a>
                        <a className="yx-table-action">预览</a>
                      </Space>
                    ),
                  },
                ]}
                dataSource={prompts}
                rowKey="id"
                pagination={false}
                size="middle"
                loading={compileLoading}
              />
            </div>
          </div>
        )

      case 'result':
        return (
          <div>
            {/* Stat Grid */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(4,1fr)',
                gap: 16,
                marginBottom: 20,
              }}
            >
              {((): Array<{ label: string; value: string; color: string }> => {
                if (resultStats) {
                  return [
                    { label: '知识实体', value: resultStats.entityCount.toLocaleString(), color: '#3b82f6' },
                    { label: '知识关系', value: resultStats.relationCount.toLocaleString(), color: '#10b981' },
                    { label: '编译版本', value: String(resultStats.compileVersionCount), color: '#8b5cf6' },
                    { label: '源文件数', value: resultStats.sourceFileCount.toLocaleString(), color: '#f97316' },
                  ]
                }
                return [
                  { label: '知识实体', value: '--', color: '#3b82f6' },
                  { label: '知识关系', value: '--', color: '#10b981' },
                  { label: '编译版本', value: '--', color: '#8b5cf6' },
                  { label: '源文件数', value: '--', color: '#f97316' },
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
                      <div
                        style={{ fontSize: 28, fontWeight: 700, color: s.color }}
                      >
                        {s.value}
                      </div>
                      <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 4 }}>
                        {s.label}
                      </div>
                    </div>
                  ))}
            </div>

            {/* Entities */}
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
                  <ShareAltOutlined style={{ color: '#3b82f6' }} /> 实体
                </h3>
                <div style={{ display: 'flex', gap: 8 }}>
                  <Input
                    prefix={<SearchOutlined />}
                    placeholder="搜索实体..."
                    style={{ width: 200 }}
                    value={entityKeywordInput}
                    onChange={(e) => {
                      setEntityKeywordInput(e.target.value)
                      setEntityPage(1)
                    }}
                  />
                  <Select
                    value={entityType}
                    onChange={(val) => {
                      setEntityType(val)
                      setEntityPage(1)
                    }}
                    style={{ width: 120 }}
                    options={[
                      { value: '全部类型', label: '全部类型' },
                      ...entityDistribution.map((e) => ({ value: e.label, label: e.label })),
                    ]}
                  />
                </div>
              </div>
              <Table
                columns={[
                  {
                    title: '实体名称',
                    dataIndex: 'name',
                    key: 'name',
                    render: (v: string) => (
                      <span style={{ fontWeight: 500, color: '#0b2b5c' }}>{v}</span>
                    ),
                  },
                  {
                    title: '实体类型',
                    dataIndex: 'type',
                    key: 'type',
                    render: (v: string) => (
                      <Tag color="processing" style={{ fontSize: 11 }}>
                        {v}
                      </Tag>
                    ),
                  },
                  { title: '属性数', dataIndex: 'attrs', key: 'attrs' },
                  {
                    title: '关系数',
                    dataIndex: 'relations',
                    key: 'relations',
                  },
                  {
                    title: '创建时间',
                    dataIndex: 'createdAt',
                    key: 'createdAt',
                  },
                  {
                    title: '操作',
                    key: 'actions',
                    render: () => (
                      <Space>
                        <a className="yx-table-action">查看</a>
                        <a className="yx-table-action">详情</a>
                      </Space>
                    ),
                  },
                ]}
                dataSource={entities}
                rowKey="id"
                pagination={false}
                size="middle"
                loading={entityLoading}
              />
              {/* Entity Pagination */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-end',
                  gap: 6,
                  padding: '12px 0 0',
                  borderTop: '1px solid #eef2f6',
                  marginTop: 12,
                }}
              >
                <span
                  className={`yx-page-btn${entityPage <= 1 ? ' disabled' : ''}`}
                  onClick={() => entityPage > 1 && setEntityPage((p) => p - 1)}
                  style={{
                    width: 34,
                    height: 34,
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: 8,
                    border: '1px solid #e2e8f0',
                    cursor: entityPage <= 1 ? 'not-allowed' : 'pointer',
                    color: '#94a3b8',
                    fontSize: 12,
                    opacity: entityPage <= 1 ? 0.4 : 1,
                  }}
                >
                  {'<'}
                </span>
                {entityPageNumbers().map((n) => (
                  <span
                    key={n}
                    className={`yx-page-btn${n === entityPage ? ' active' : ''}`}
                    onClick={() => setEntityPage(n)}
                    style={{
                      width: 34,
                      height: 34,
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      borderRadius: 8,
                      background:
                        n === entityPage ? '#3b82f6' : 'transparent',
                      color: n === entityPage ? '#fff' : '#64748b',
                      fontWeight: n === entityPage ? 600 : 400,
                      fontSize: 13,
                      cursor: 'pointer',
                      border:
                        n === entityPage ? 'none' : '1px solid #e2e8f0',
                    }}
                  >
                    {n}
                  </span>
                ))}
                <span
                  className={`yx-page-btn${entityPage >= entityTotalPages ? ' disabled' : ''}`}
                  onClick={() =>
                    entityPage < entityTotalPages &&
                    setEntityPage((p) => p + 1)
                  }
                  style={{
                    width: 34,
                    height: 34,
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: 8,
                    border: '1px solid #e2e8f0',
                    cursor:
                      entityPage >= entityTotalPages
                        ? 'not-allowed'
                        : 'pointer',
                    color: '#94a3b8',
                    fontSize: 12,
                    opacity: entityPage >= entityTotalPages ? 0.4 : 1,
                  }}
                >
                  {'>'}
                </span>
                <span
                  style={{
                    fontSize: 13,
                    color: '#94a3b8',
                    marginLeft: 12,
                  }}
                >
                  共 {entityTotal.toLocaleString()} 条，{entityPage}/
                  {entityTotalPages} 页
                </span>
              </div>
            </div>

            {/* Knowledge Graph */}
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
                  <ShareAltOutlined style={{ color: '#10b981' }} /> 知识图谱
                </h3>
                <Button
                  style={{ padding: '6px 16px', fontSize: 13, height: 'auto' }}
                  icon={<EyeOutlined />}
                  onClick={() => navigate('graph')}
                >
                  查看全图
                </Button>
              </div>
              {graphSummary && (
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(4,1fr)',
                    gap: 12,
                    marginBottom: 16,
                  }}
                >
                  <div
                    style={{
                      background: '#f0f9ff',
                      borderRadius: 8,
                      padding: 14,
                      textAlign: 'center',
                      border: '1px solid #dbeafe',
                    }}
                  >
                    <div
                      style={{
                        fontSize: 20,
                        fontWeight: 700,
                        color: '#3b82f6',
                      }}
                    >
                      {graphSummary.entityTypeCount}
                    </div>
                    <div
                      style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}
                    >
                      实体类型
                    </div>
                  </div>
                  <div
                    style={{
                      background: '#f0fdf4',
                      borderRadius: 8,
                      padding: 14,
                      textAlign: 'center',
                      border: '1px solid #bbf7d0',
                    }}
                  >
                    <div
                      style={{
                        fontSize: 20,
                        fontWeight: 700,
                        color: '#10b981',
                      }}
                    >
                      {graphSummary.relationTotalCount.toLocaleString()}
                    </div>
                    <div
                      style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}
                    >
                      关系总数
                    </div>
                  </div>
                  <div
                    style={{
                      background: '#fefce8',
                      borderRadius: 8,
                      padding: 14,
                      textAlign: 'center',
                      border: '1px solid #fef08a',
                    }}
                  >
                    <div
                      style={{
                        fontSize: 20,
                        fontWeight: 700,
                        color: '#ca8a04',
                      }}
                    >
                      {graphSummary.relationTypeCount}
                    </div>
                    <div
                      style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}
                    >
                      关系类型
                    </div>
                  </div>
                  <div
                    style={{
                      background: '#fef2f2',
                      borderRadius: 8,
                      padding: 14,
                      textAlign: 'center',
                      border: '1px solid #fecaca',
                    }}
                  >
                    <div
                      style={{
                        fontSize: 20,
                        fontWeight: 700,
                        color: '#ef4444',
                      }}
                    >
                      {graphSummary.avgDegree}
                    </div>
                    <div
                      style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}
                    >
                      平均度数
                    </div>
                  </div>
                </div>
              )}
              {/* Distribution Charts */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 12,
                }}
              >
                <div
                  style={{
                    border: '1px solid #eef2f6',
                    borderRadius: 10,
                    padding: 16,
                    background: '#fafcff',
                  }}
                >
                  <div
                    style={{
                      fontSize: 13,
                      fontWeight: 600,
                      color: '#0b2b5c',
                      marginBottom: 10,
                    }}
                  >
                    核心实体分布
                  </div>
                  {entityDistribution.map((e) => (
                    <div
                      key={e.label}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        marginBottom: 8,
                      }}
                    >
                      <span
                        style={{ fontSize: 12, color: '#64748b', width: 70 }}
                      >
                        {e.label}
                      </span>
                      <div
                        style={{
                          flex: 1,
                          height: 8,
                          background: '#e2e8f0',
                          borderRadius: 4,
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          style={{
                            height: '100%',
                            width: `${e.pct}%`,
                            background: e.color,
                            borderRadius: 4,
                          }}
                        />
                      </div>
                      <span
                        style={{
                          fontSize: 12,
                          color: '#475569',
                          width: 40,
                          textAlign: 'right',
                        }}
                      >
                        {e.count.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
                <div
                  style={{
                    border: '1px solid #eef2f6',
                    borderRadius: 10,
                    padding: 16,
                    background: '#fafcff',
                  }}
                >
                  <div
                    style={{
                      fontSize: 13,
                      fontWeight: 600,
                      color: '#0b2b5c',
                      marginBottom: 10,
                    }}
                  >
                    关系类型统计
                  </div>
                  {relationDistribution.map((r) => (
                    <div
                      key={r.label}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        marginBottom: 8,
                      }}
                    >
                      <span
                        style={{ fontSize: 12, color: '#64748b', width: 80 }}
                      >
                        {r.label}
                      </span>
                      <div
                        style={{
                          flex: 1,
                          height: 8,
                          background: '#e2e8f0',
                          borderRadius: 4,
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          style={{
                            height: '100%',
                            width: `${r.pct}%`,
                            background: r.color,
                            borderRadius: 4,
                          }}
                        />
                      </div>
                      <span
                        style={{
                          fontSize: 12,
                          color: '#475569',
                          width: 50,
                          textAlign: 'right',
                        }}
                      >
                        {r.count.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Logic Rules */}
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
              {renderSectionHeader(
                '逻辑',
                <CodeOutlined style={{ color: '#8b5cf6' }} />,
              )}
              <p style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16 }}>
                基于知识图谱推导的业务逻辑规则，用于智能推理与分析
              </p>
              <Table
                columns={[
                  {
                    title: '逻辑名称',
                    dataIndex: 'name',
                    key: 'name',
                    render: (v: string) => (
                      <span style={{ fontWeight: 500, color: '#0b2b5c' }}>{v}</span>
                    ),
                  },
                  {
                    title: '类型',
                    dataIndex: 'type',
                    key: 'type',
                    render: (v: string) => (
                      <span style={{ fontSize: 12, color: '#64748b' }}>{v}</span>
                    ),
                  },
                  {
                    title: '条件',
                    dataIndex: 'condition',
                    key: 'condition',
                    render: (v: string) => (
                      <span style={{ fontSize: 12, color: '#64748b' }}>{v}</span>
                    ),
                  },
                  {
                    title: '结论',
                    dataIndex: 'conclusion',
                    key: 'conclusion',
                    render: (v: string) => (
                      <span style={{ fontSize: 12, color: '#64748b' }}>{v}</span>
                    ),
                  },
                  {
                    title: '置信度',
                    dataIndex: 'confidence',
                    key: 'confidence',
                    render: (v: string) => (
                      <span
                        style={{
                          fontWeight: 500,
                          color:
                            v.startsWith('9') || v.startsWith('8')
                              ? '#10b981'
                              : '#f97316',
                        }}
                      >
                        {v}
                      </span>
                    ),
                  },
                  {
                    title: '状态',
                    dataIndex: 'status',
                    key: 'status',
                    render: (v: string) => (
                      <Tag color={v === '启用' ? 'success' : 'warning'}>{v}</Tag>
                    ),
                  },
                  {
                    title: '操作',
                    key: 'actions',
                    render: () => <a className="yx-table-action">编辑</a>,
                  },
                ]}
                dataSource={logicRules}
                rowKey="id"
                pagination={false}
                size="middle"
                loading={resultLoading}
              />
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
                <ThunderboltOutlined style={{ color: '#8b5cf6' }} /> 触发规则
              </h3>
              <Button
                type="primary"
                style={{ padding: '6px 16px', fontSize: 13, height: 'auto' }}
                icon={<PlusOutlined />}
              >
                新建规则
              </Button>
            </div>
            <p style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16 }}>
              定义当知识库的解析或编译结果满足条件时自动执行的动作
            </p>
            {actionLoading ? (
              <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>
                加载中...
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
                        <a className="yx-table-action">编辑</a>
                        <a
                          className="yx-table-action"
                          style={{ color: '#ef4444' }}
                        >
                          删除
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
                            触发条件
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
                            执行动作
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

      default:
        return null
    }
  }

  // ── main render ───────────────────────────────────────
  return (
    <div>
      {/* Back Navigation */}
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
          <ArrowLeftOutlined style={{ fontSize: 12 }} /> 返回知识库列表
        </a>
      </div>

      {/* Knowledge Base Header */}
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
              加载中...
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
                  <FileTextOutlined /> {detail.documentCount.toLocaleString()}{' '}
                  文档
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
                  <ShareAltOutlined /> {detail.entityCount.toLocaleString()}{' '}
                  实体
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
                  <ShareAltOutlined /> {detail.relationCount.toLocaleString()}{' '}
                  关系
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
                {statusTextMap[detail.status]}
              </div>
              <div
                style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}
              >
                上次更新：{detail.updatedAt}
              </div>
            </div>
          </>
        ) : null}
      </div>

      {/* Tab Bar */}
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
              <Icon /> {tab.label}
            </div>
          )
        })}
      </div>

      {/* Tab Content */}
      {renderTabContent()}
    </div>
  )
}
