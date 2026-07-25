import React from 'react'
import {
  FileTextOutlined,
  ShareAltOutlined,
  LikeOutlined,
  DislikeOutlined,
  RobotOutlined,
  ApartmentOutlined,
} from '@ant-design/icons'
import type { OntologyStatistics } from '@/types/domainKnowledge'

// ── Types ──────────────────────────────────────────────────
export interface TabConfig {
  key: string
  label: string
  count: number
  icon: React.ReactNode
}

// ── Tabs（count 由调用方传入，其中 like/dislike 来自搜索反馈统计） ────────
export function buildTabs(
  t: (key: string, options?: Record<string, unknown>) => string,
  stats: OntologyStatistics,
  likeCount = 0,
  dislikeCount = 0,
): TabConfig[] {
  return [
    { key: 'ontology', label: t('domainKnowledge.ontologyInstances'), count: stats.ontology_instance_count, icon: <RobotOutlined /> },
    { key: 'relation', label: t('domainKnowledge.relationInstances'), count: stats.ontology_relation_count, icon: <ShareAltOutlined /> },
    { key: 'graph', label: t('domainKnowledge.graphBreadcrumb'), count: 0, icon: <ApartmentOutlined /> },
    // { key: 'like', label: '用户赞采纳', count: likeCount, icon: <LikeOutlined /> },
    // { key: 'dislike', label: '用户踩采纳', count: dislikeCount, icon: <DislikeOutlined /> },
  ]
}

// ── Stats 卡片 ─────────────────────────────────────────────
export function buildStats(
  t: (key: string, options?: Record<string, unknown>) => string,
  stats: OntologyStatistics,
  ontologyInstanceCount?: number,
  relationInstanceCount?: number,
) {
  return [
    { label: t('compile.statDocuments'), value: stats.source_file_count, icon: <FileTextOutlined style={{ color: '#3b82f6' }} /> },
    { label: t('domainKnowledge.ontologyInstances'), value: ontologyInstanceCount ?? stats.ontology_instance_count, icon: <RobotOutlined style={{ color: '#22c55e' }} /> },
    { label: t('domainKnowledge.relationInstances'), value: relationInstanceCount ?? stats.ontology_relation_count, icon: <ShareAltOutlined style={{ color: '#f59e0b' }} /> },
  ]
}
