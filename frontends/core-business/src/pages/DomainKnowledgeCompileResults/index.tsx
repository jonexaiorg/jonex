import { useState, useMemo, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { Button, Card, Tag, Tabs, Space, Spin } from 'antd';
import { ArrowLeftOutlined, DatabaseOutlined } from '@ant-design/icons';
import type { OntologyStatistics, OntologyInstanceSummary, RelationInstanceSummary } from '@/types/domainKnowledge';
import { getOntologyStatistics, getOntologyEntityTypes, getOntologyRelationTypes } from '@/api/domainKnowledge';
import { getSearchFeedbackStats } from '@/api/knowledgeSearch';
import type { SearchFeedbackStats } from '@/types/knowledgeSearch';
import { buildTabs, buildStats } from './config';
import type { TabConfig } from './config';
import OntologyTab from './OntologyTab';
import RelationTab from './RelationTab';
import GraphTab from './GraphTab';
import LikeTab from './LikeTab';
import DislikeTab from './DislikeTab';

const renderTabLabel = (item: TabConfig) => (
  <Space size={6}>
    {item.icon}
    <span>{item.label}</span>
    {item.count > 0 && <span style={{ color: '#94a3b8', fontSize: 12 }}>{item.count}</span>}
  </Space>
);

export default function DomainKnowledgeCompileResults() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id = '' } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState('ontology');
  const [statsData, setStatsData] = useState<OntologyStatistics | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);

  const [entityTypes, setEntityTypes] = useState<OntologyInstanceSummary[] | null>(null);
  const [relationTypes, setRelationTypes] = useState<RelationInstanceSummary[] | null>(null);
  const [feedbackStats, setFeedbackStats] = useState<SearchFeedbackStats | null>(null);

  // 进入页面请求统计 + 本体实例 + 关系实例 + 反馈统计
  useEffect(() => {
    if (!id) return;
    setStatsLoading(true);
    getOntologyStatistics(id)
      .then(setStatsData)
      .catch(() => {})
      .finally(() => setStatsLoading(false));

    getOntologyEntityTypes(id)
      .then((res) => setEntityTypes(res.items.map((item) => ({ ...item, type: item.name }))))
      .catch(() => {});

    getOntologyRelationTypes(id)
      .then((res) => setRelationTypes(res.items))
      .catch(() => {});

    getSearchFeedbackStats(id)
      .then(setFeedbackStats)
      .catch(() => {});
  }, [id]);

  const tabs = useMemo(
    () => (statsData ? buildTabs(t, statsData, feedbackStats?.like_count, feedbackStats?.dislike_count) : []),
    [statsData, feedbackStats, t],
  );
  const stats = useMemo(() => (statsData ? buildStats(t, statsData) : []), [statsData, t]);

  const tabContent = useMemo(() => {
    switch (activeTab) {
      case 'ontology':
        return <OntologyTab kbId={id} data={entityTypes} />;
      case 'relation':
        return <RelationTab kbId={id} data={relationTypes} />;
      case 'graph':
        return <GraphTab kbId={id} />;
      case 'like':
        return <LikeTab kbId={id} />;
      case 'dislike':
        return <DislikeTab kbId={id} />;
      default:
        return null;
    }
  }, [activeTab, id, entityTypes, relationTypes]);

  return (
    <div>
      {/* Header */}
      <div
        style={{
          background: '#fff',
          borderRadius: 12,
          padding: '20px 24px',
          border: '1px solid #eef2f6',
          marginBottom: 16,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            marginBottom: 12,
          }}
        >
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate(`/domain-knowledge/${id}`)}
            style={{ borderRadius: 8 }}
          >
            {t('common.back')}
          </Button>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1 }}>
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 10,
                background: '#eff6ff',
                color: '#3b82f6',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 20,
              }}
            >
              <DatabaseOutlined />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 18, fontWeight: 700, color: '#0b2b5c' }}>
                  {statsData?.knowledge_base_name || t('domainKnowledge.detail')}
                </span>
                <Tag color="success" style={{ margin: 0, borderRadius: 6, fontSize: 12 }}>
                  {t('status.compiled')}
                </Tag>
              </div>
              <div
                style={{
                  fontSize: 13,
                  color: '#94a3b8',
                  marginTop: 4,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                }}
              >
                <span>{t('common.fullCompileResults')}</span>
                {statsData?.last_update_time && <span>{new Date(statsData.last_update_time).toLocaleString()}</span>}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <Spin spinning={statsLoading}>
        <div
          style={{
            display: 'flex',
            gap: 16,
            marginBottom: 16,
          }}
        >
          {stats.map((s) => (
            <Card
              key={s.label}
              styles={{
                body: {
                  padding: '20px 24px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                },
              }}
              style={{
                flex: 1,
                borderRadius: 12,
                border: '1px solid #eef2f6',
                boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
              }}
            >
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: 12,
                  background: '#f8fafc',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 22,
                }}
              >
                {s.icon}
              </div>
              <div>
                <div
                  style={{
                    fontSize: 24,
                    fontWeight: 700,
                    color: '#0b2b5c',
                    lineHeight: 1,
                  }}
                >
                  {s.value.toLocaleString()}
                </div>
                <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 4 }}>{s.label}</div>
              </div>
            </Card>
          ))}
        </div>
      </Spin>

      {/* Tabs & Table */}
      <Card
        style={{
          borderRadius: 12,
          border: '1px solid #eef2f6',
          boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
        }}
        styles={{ body: { padding: 0 } }}
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabs.map((t) => ({
            key: t.key,
            label: renderTabLabel(t),
          }))}
          style={{ padding: '0 20px' }}
        />

        {tabContent}
      </Card>
    </div>
  );
}
