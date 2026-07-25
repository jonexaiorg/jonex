import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Button,
  Card,
  Space,
  Tag,
  Tabs,
  Spin,
  Typography,
  message,
} from 'antd'
import {
  ArrowLeftOutlined,
  FileTextOutlined,
  ReloadOutlined,
  BuildOutlined,
  FilePdfOutlined,
  BranchesOutlined,
  FileOutlined,
} from '@ant-design/icons'
import { getManualDocumentDetail, getOntologyEntityTypes, getOntologyRelationTypes, reparseDocument, retryDocumentOntology } from '@/api/domainKnowledge'
import type { ManualDocItem, OntologyInstanceSummary, RelationInstanceSummary } from '@/types/domainKnowledge'
import StageDetailCard from './StageDetailCard'
import CompileResultPanel from './CompileResultPanel'
import type { ProcessingStage } from './StageDetailCard'

const { Title } = Typography

function getDocStatusText(t: (key: string) => string): Record<string, string> {
  return {
    compiled: t('domainKnowledge.docStatus.compiled'),
    parsing: t('domainKnowledge.docStatus.parsing'),
    pending: t('domainKnowledge.docStatus.pending'),
  }
}

const DOC_STATUS_COLOR: Record<string, string> = {
  compiled: '#22c55e',
  parsing: '#3b82f6',
  pending: '#94a3b8',
}


export default function DomainKnowledgeDocumentResult() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { id = '', docId = '' } = useParams<{ id: string; docId: string }>()
  const [doc, setDoc] = useState<ManualDocItem | null>(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('parse')
  const [activeSubNav, setActiveSubNav] = useState('ontology')
  const [reparseLoading, setReparseLoading] = useState(false)
  const [recompileLoading, setRecompileLoading] = useState(false)
  const [entityTypes, setEntityTypes] = useState<OntologyInstanceSummary[] | null>(null)
  const [relationTypes, setRelationTypes] = useState<RelationInstanceSummary[] | null>(null)

  useEffect(() => {
    if (!id || !docId) return
    setLoading(true)
    getManualDocumentDetail(id, docId, t)
      .then(setDoc)
      .catch(() => message.error(t('domainKnowledge.documentDetailLoadFailed')))
      .finally(() => setLoading(false))

    getOntologyEntityTypes(id)
      .then((res) => setEntityTypes(res.items))
      .catch(() => {})

    getOntologyRelationTypes(id)
      .then((res) => setRelationTypes(res.items))
      .catch(() => {})
  }, [id, docId, t])

  const handleReparse = async () => {
    setReparseLoading(true)
    try {
      await reparseDocument(docId)
      message.success(t('domainKnowledge.reparseTriggered'))
    } catch (err: any) {
      message.error(err?.message || t('domainKnowledge.reparseFailed'))
    } finally {
      setReparseLoading(false)
    }
  }

  const handleRecompile = async () => {
    setRecompileLoading(true)
    try {
      await retryDocumentOntology(id, docId)
      message.success(t('domainKnowledge.recompileTriggered'))
    } catch (err: any) {
      message.error(err?.message || t('domainKnowledge.retryOntologyFailed'))
    } finally {
      setRecompileLoading(false)
    }
  }

  const fileIcon = (type?: string) => {
    const t = (type || '').toLowerCase()
    if (t === 'pdf') return <FilePdfOutlined style={{ color: '#ef4444', fontSize: 32 }} />
    return <FileTextOutlined style={{ color: '#3b82f6', fontSize: 32 }} />
  }

  const stages: ProcessingStage[] = [
    {
      key: 'parse',
      label: t('domainKnowledge.stage.parseResult'),
      icon: <FileOutlined />,
    },
    {
      key: 'compile',
      label: t('domainKnowledge.stage.compileResult'),
      icon: <BranchesOutlined />,
    },
  ]

  const activeStage = stages.find((s) => s.key === activeTab) || stages[0]

  const tabItems = stages.map((stage) => ({
    key: stage.key,
    label: (
      <Space size={6}>
        {stage.icon}
        <span>{stage.label}</span>
      </Space>
    ),
    children: stage.key === 'compile' ? (
      <CompileResultPanel kbId={id} docId={docId} activeSubNav={activeSubNav} onSubNavChange={setActiveSubNav} entityTypes={entityTypes} relationTypes={relationTypes} />
    ) : (
      <StageDetailCard stage={stage} docId={docId} />
    ),
  }))

  return (
    <div style={{ padding: '0 0 24px' }}>
      <Spin spinning={loading}>
        <Card
          style={{
            borderRadius: 12,
            border: '1px solid #eef2f6',
            boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
            marginBottom: 16,
          }}
          styles={{ body: { padding: '20px 24px' } }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 16,
              flexWrap: 'wrap',
            }}
          >
            <Space align="center" size={16}>
              <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => navigate(`/domain-knowledge/${id}`)}
                style={{ borderRadius: 8 }}
              >
                {t('common.back')}
              </Button>

              {fileIcon(doc?.type)}

              <Space direction="vertical" size={4}>
                <Space align="center" size={12}>
                  <Title level={4} style={{ margin: 0, color: '#0b2b5c', fontSize: 18 }}>
                    {doc?.name || t('domainKnowledge.documentResultTitle')}
                  </Title>
                  <Tag
                    style={{
                      border: 'none',
                      borderRadius: 6,
                      fontSize: 12,
                      color: '#fff',
                      background: DOC_STATUS_COLOR[doc?.status || ''] || '#94a3b8',
                    }}
                  >
                    {getDocStatusText(t)[doc?.status || ''] || doc?.status || t('common.unknown')}
                  </Tag>
                </Space>

                <Space
                  size={16}
                  style={{
                    color: '#64748b',
                    fontSize: 13,
                    flexWrap: 'wrap',
                  }}
                >
                  <span>{doc?.type?.toUpperCase() || '—'}</span>
                  <span>{doc?.size || '—'}</span>
                  <span>{doc?.uploadTime || '—'}</span>
                </Space>
              </Space>
            </Space>

            <Space size={12}>
              <Button
                icon={<ReloadOutlined />}
                style={{ borderRadius: 8 }}
                loading={reparseLoading}
                onClick={handleReparse}
              >
                {t('domainKnowledge.reparse')}
              </Button>
              <Button
                icon={<BuildOutlined />}
                style={{ borderRadius: 8 }}
                loading={recompileLoading}
                onClick={handleRecompile}
              >
                {t('domainKnowledge.recompile')}
              </Button>
            </Space>
          </div>
        </Card>

        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
          style={{
            background: '#fff',
            borderRadius: 12,
            border: '1px solid #eef2f6',
            boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
            padding: '0 24px 24px',
          }}
        />
      </Spin>
    </div>
  )
}
