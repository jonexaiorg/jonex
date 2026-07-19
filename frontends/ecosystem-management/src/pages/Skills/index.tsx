import React, { useState, useEffect, useMemo, useCallback } from 'react'
import {
  Button, Card, Input, Select, Tag, Switch, Modal, message, Spin, Result,
  Space, Typography, Descriptions,
} from 'antd'
import {
  SearchOutlined, ArrowLeftOutlined,
  FileImageOutlined, AudioOutlined, FileTextOutlined,
  VideoCameraOutlined, DatabaseOutlined, SearchOutlined as FusionSearchOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { colors } from '@jonex/platform-theme/tokens'
import {
  fetchSkills, enableSkill, disableSkill,
  type SkillItem, type FetchSkillsParams,
} from '../../api/skills'
import './index.css'

const { Text, Paragraph } = Typography

const CATEGORY_OPTIONS = [
  'image', 'voice', 'document', 'video', 'fusion', 'custom',
] as const

const CATEGORY_LABELS: Record<string, string> = {
  image: 'skill.imageProcessing',
  voice: 'skill.voiceProcessing',
  document: 'skill.documentProcessing',
  video: 'skill.videoProcessing',
  fusion: 'skill.fusionRetrieval',
  custom: 'skill.other',
}

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  image: <FileImageOutlined />,
  voice: <AudioOutlined />,
  document: <FileTextOutlined />,
  video: <VideoCameraOutlined />,
  fusion: <FusionSearchOutlined />,
  custom: <DatabaseOutlined />,
}

const CATEGORY_GRADIENTS: Record<string, string> = {
  image: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
  voice: 'linear-gradient(135deg, #10b981, #059669)',
  document: 'linear-gradient(135deg, #f97316, #ea580c)',
  video: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
  fusion: 'linear-gradient(135deg, #ef4444, #dc2626)',
  custom: 'linear-gradient(135deg, #06b6d4, #0891b2)',
}

function formatJsonSchema(schema: Record<string, unknown>): string {
  try {
    return JSON.stringify(schema, null, 2)
  } catch {
    return '{}'
  }
}

export default function Skills() {
  const { t } = useTranslation('business')
  const [items, setItems] = useState<SkillItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [keyword, setKeyword] = useState('')
  const [category, setCategory] = useState<string | undefined>()
  const [pagination, setPagination] = useState({ offset: 0, limit: 20, total: 0 })
  const [submittingId, setSubmittingId] = useState<string | null>(null)
  const [detailSkill, setDetailSkill] = useState<SkillItem | null>(null)

  const loadSkills = useCallback(async (next?: FetchSkillsParams) => {
    setLoading(true)
    setError(null)
    try {
      const params = next ?? { offset: 0, limit: 20, keyword, category }
      const result = await fetchSkills(params)
      setItems(result.items)
      setPagination({
        offset: result.offset ?? 0,
        limit: result.limit ?? 20,
        total: result.total,
      })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('skill.loadFailed'))
    } finally {
      setLoading(false)
    }
  }, [keyword, category, t])

  useEffect(() => {
    loadSkills()
  }, [])

  const filtered = useMemo(() => {
    return items.filter((s) => {
      if (keyword) {
        const q = keyword.toLowerCase()
        if (
          !s.name.toLowerCase().includes(q)
          && !(s.description || '').toLowerCase().includes(q)
          && !s.tool_name.toLowerCase().includes(q)
        ) {
          return false
        }
      }
      if (category && s.category !== category) return false
      return true
    })
  }, [items, keyword, category])

  async function handleToggle(skill: SkillItem) {
    setSubmittingId(skill.id)
    try {
      if (skill.enabled) {
        await disableSkill(skill.id)
        message.success(t('skill.disableSuccess'))
      } else {
        await enableSkill(skill.id)
        message.success(t('skill.enableSuccess'))
      }
      await loadSkills({ offset: pagination.offset, limit: pagination.limit, keyword, category })
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('common.operationFailed'))
    } finally {
      setSubmittingId(null)
    }
  }

  const reload = () => loadSkills({ offset: 0, limit: 20, keyword, category })


  if (loading && items.length === 0) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
        <Spin size="large" />
      </div>
    )
  }


  if (error) {
    return (
      <Result
        status="error"
        title={t('common.loadFailed')}
        subTitle={error}
        extra={<Button type="primary" onClick={reload}>{t('common.retry')}</Button>}
      />
    )
  }


  return (
    <div>
      { }
      <div style={{ marginBottom: 16 }}>
        <a
          href="/"
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            fontSize: 14, color: colors.textSecondary, textDecoration: 'none',
            padding: '4px 0',
          }}
        >
          <ArrowLeftOutlined style={{ fontSize: 12 }} /> {t('navigation.home')}
        </a>
      </div>

      { }
      <div className="yx-page-title">
        <h1 style={{ fontSize: 22, fontWeight: 700, color: colors.brandDark, margin: 0 }}>
          {t('skill.detailTitle')}
        </h1>
        <p style={{ color: colors.textMuted, margin: '4px 0 0', fontSize: 14 }}>
          {t('skill.detailDesc')}
        </p>
      </div>

      { }
      <div
        className="yx-toolbar"
        style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          marginBottom: 20, marginTop: 8,
        }}
      >
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <Input
            placeholder={t('skill.searchPlaceholder')}
            prefix={<SearchOutlined />}
            value={keyword}
            onChange={(e) => { setKeyword(e.target.value); setPagination(prev => ({ ...prev, offset: 0 })) }}
            allowClear
            style={{ width: 240 }}
          />
          <Select
            placeholder={t('skill.allCategories')}
            value={category}
            onChange={(v) => { setCategory(v); setPagination(prev => ({ ...prev, offset: 0 })) }}
            allowClear
            style={{ width: 140 }}
            options={CATEGORY_OPTIONS.map((c) => ({ label: t(CATEGORY_LABELS[c]), value: c }))}
          />
        </div>
        <span style={{ fontSize: 13, color: colors.textMuted }}>{t('skill.countText', { count: pagination.total })}</span>
      </div>

      { }
      {filtered.length === 0 ? (
        <div className="yx-empty-state">
          <p>{t('skill.noResults')}</p>
          <Button onClick={reload}>{t('common.refresh')}</Button>
        </div>
      ) : (

        <div className="skills-grid">
          {filtered.map((skill) => {
            const isBusy = submittingId === skill.id

            return (
              <Card
                key={skill.id}
                className="skills-card"
                hoverable
                actions={[
                  <Button
                    key="toggle"
                    type={skill.enabled ? 'default' : 'primary'}
                    size="small"
                    loading={isBusy}
                    danger={skill.enabled}
                    onClick={() => handleToggle(skill)}
                  >
                    {skill.enabled ? t('skill.disable') : t('skill.enable')}
                  </Button>,
                  <Button
                    key="detail"
                    type="text"
                    size="small"
                    icon={<EyeOutlined />}
                    onClick={() => setDetailSkill(skill)}
                  >
                    {t('skill.detail')}
                  </Button>,
                ]}
              >
                <Card.Meta
                  avatar={
                    <div
                      style={{
                        width: 48, height: 48, borderRadius: 12,
                        background: CATEGORY_GRADIENTS[skill.category] || CATEGORY_GRADIENTS.custom,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 22, color: '#fff',
                      }}
                    >
                      {CATEGORY_ICONS[skill.category] || CATEGORY_ICONS.custom}
                    </div>
                  }
                  title={
                    <Space>
                      <span>{skill.name}</span>
                      <Tag color={skill.enabled ? 'green' : 'default'}>
                        {skill.enabled ? t('skill.enabled') : t('skill.disabled')}
                      </Tag>
                    </Space>
                  }
                  description={
                    <div>
                      <Paragraph
                        ellipsis={{ rows: 2 }}
                        style={{ marginBottom: 8, color: colors.textSecondary, fontSize: 13 }}
                      >
                        {skill.description || t('common.noDescription')}
                      </Paragraph>
                      <Space size={[4, 4]} wrap style={{ marginBottom: 4 }}>
                        <Tag color="blue">{t(CATEGORY_LABELS[skill.category] || skill.category)}</Tag>
                        <Tag>{skill.tool_name}</Tag>
                        {skill.tags.map((t) => (
                          <Tag key={t} style={{ fontSize: 11 }}>{t}</Tag>
                        ))}
                      </Space>
                    </div>
                  }
                />
              </Card>
            )
          })}
        </div>
      )}

      { }
      <Modal
        title={
          <Space>
            <span style={{ fontSize: 24 }}>
              {CATEGORY_ICONS[detailSkill?.category || 'custom']}
            </span>
            <span>{detailSkill?.name}</span>
          </Space>
        }
        open={!!detailSkill}
        onCancel={() => setDetailSkill(null)}
        footer={
          <Button onClick={() => setDetailSkill(null)}>{t('common.close')}</Button>
        }
        width={680}
      >
        {detailSkill && (
          <div>
            <Descriptions column={2} size="small" bordered style={{ marginBottom: 16 }}>
              <Descriptions.Item label={t('skill.category')}>
                {t(CATEGORY_LABELS[detailSkill.category])}
              </Descriptions.Item>
              <Descriptions.Item label={t('skill.status')}>
                <Tag color={detailSkill.enabled ? 'green' : 'default'}>
                  {detailSkill.enabled ? t('skill.enabled') : t('skill.disabled')}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label={t('skill.toolName')} span={2}>
                <code>{detailSkill.tool_name}</code>
              </Descriptions.Item>
            </Descriptions>

            <Text strong style={{ display: 'block', marginBottom: 8 }}>{t('skill.instruction')}</Text>
            <Paragraph style={{
              background: '#f8fafc', padding: 12, borderRadius: 8,
              fontSize: 13, lineHeight: 1.7,
            }}>
              {detailSkill.instruction}
            </Paragraph>

            <Text strong style={{ display: 'block', marginBottom: 8, marginTop: 16 }}>{t('skill.inputSchema')}</Text>
            <pre style={{
              background: '#1e293b', color: '#e2e8f0', padding: 12, borderRadius: 8,
              fontSize: 12, overflow: 'auto', maxHeight: 200,
            }}>
              {formatJsonSchema(detailSkill.input_schema)}
            </pre>

            <Text strong style={{ display: 'block', marginBottom: 8, marginTop: 16 }}>{t('skill.outputSchema')}</Text>
            <pre style={{
              background: '#1e293b', color: '#e2e8f0', padding: 12, borderRadius: 8,
              fontSize: 12, overflow: 'auto', maxHeight: 200,
            }}>
              {formatJsonSchema(detailSkill.output_schema)}
            </pre>

            <Text strong style={{ display: 'block', marginBottom: 8, marginTop: 16 }}>{t('skill.capabilityDesc')}</Text>
            <pre style={{
              background: '#f8fafc', padding: 12, borderRadius: 8,
              fontSize: 12, overflow: 'auto', maxHeight: 150,
            }}>
              {formatJsonSchema(detailSkill.capability || {})}
            </pre>
          </div>
        )}
      </Modal>
    </div>
  )
}