import React from 'react'
import { useTranslation } from 'react-i18next'
import { Card } from 'antd'
import { RobotOutlined, ShareAltOutlined, ApartmentOutlined } from '@ant-design/icons'
import OntologyTab from '@/pages/DomainKnowledgeCompileResults/OntologyTab'
import RelationTab from '@/pages/DomainKnowledgeCompileResults/RelationTab'
import GraphTab from '@/pages/DomainKnowledgeCompileResults/GraphTab'
import type { OntologyInstanceSummary, RelationInstanceSummary } from '@/types/domainKnowledge'

interface CompileResultPanelProps {
  kbId: string
  docId?: string
  activeSubNav: string
  onSubNavChange: (key: string) => void
  entityTypes: OntologyInstanceSummary[] | null
  relationTypes: RelationInstanceSummary[] | null
}

export default function CompileResultPanel({
  kbId,
  docId,
  activeSubNav,
  onSubNavChange,
  entityTypes,
  relationTypes,
}: CompileResultPanelProps) {
  const { t } = useTranslation()

  const navItems = [
    { key: 'ontology', label: t('domainKnowledge.ontologyInstances'), icon: <RobotOutlined /> },
    { key: 'relation', label: t('domainKnowledge.relationInstances'), icon: <ShareAltOutlined /> },
    { key: 'graph', label: t('domainKnowledge.graphBreadcrumb'), icon: <ApartmentOutlined /> },
  ]

  return (
    <Card
      style={{
        borderRadius: 12,
        border: '1px solid #eef2f6',
        boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
        overflow: 'hidden',
      }}
      styles={{ body: { padding: 0 } }}
    >
      <div style={{ display: 'flex', height: 'calc(100vh - 300px)', minHeight: 500, overflow: 'hidden' }}>
        <div
          style={{
            width: 180,
            borderRight: '1px solid #f1f5f9',
            padding: '12px 8px',
            background: '#fafbfc',
            flexShrink: 0,
            overflowY: 'auto',
          }}
        >
          {navItems.map((item) => {
            const active = activeSubNav === item.key
            return (
              <div
                key={item.key}
                onClick={() => onSubNavChange(item.key)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '12px 16px',
                  borderRadius: 8,
                  cursor: 'pointer',
                  fontSize: 14,
                  fontWeight: 500,
                  color: active ? '#3b82f6' : '#64748b',
                  background: active ? '#eff6ff' : 'transparent',
                  transition: 'all 0.2s',
                  marginBottom: 4,
                }}
              >
                {item.icon}
                <span>{item.label}</span>
              </div>
            )
          })}
        </div>

        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {activeSubNav === 'ontology' && (
            <OntologyTab
              kbId={kbId}
              docId={docId}
              data={entityTypes}
              title={t('domainKnowledge.ontologyInstances')}
            />
          )}
          {activeSubNav === 'relation' && (
            <RelationTab kbId={kbId} docId={docId} data={relationTypes} title={t('domainKnowledge.relationInstances')} />
          )}
          {activeSubNav === 'graph' && <GraphTab kbId={kbId} />}
        </div>
      </div>
    </Card>
  )
}
