import React, { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Button, Card, Space, Breadcrumb } from 'antd';
import { ArrowLeftOutlined, ReloadOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { getOntologyStatistics } from '@/api/domainKnowledge';
import type { OntologyStatistics } from '@/types/domainKnowledge';
import KnowledgeGraphPanel from '@/components/KnowledgeGraphPanel';

export default function DomainKnowledgeGraph() {
  const { t } = useTranslation();
  const { id: kbId } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [stats, setStats] = useState<OntologyStatistics | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const loadStats = useCallback(async () => {
    if (!kbId) return;
    try {
      const statsData = await getOntologyStatistics(kbId);
      setStats(statsData);
    } catch {
      // stats 加载失败不影响图谱主体
    }
  }, [kbId]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  const handleRefresh = () => {
    loadStats();
    setRefreshKey((k) => k + 1);
  };

  return (
    <div>
      {/* 面包屑 */}
      <div style={{ marginBottom: 16 }}>
        <Breadcrumb
          items={[
            {
              title: (
                <a onClick={() => navigate('/domain-knowledge')} style={{ color: '#64748b' }}>
                  {t('domainKnowledge.management')}
                </a>
              ),
            },
            {
              title: (
                <a onClick={() => navigate(`/domain-knowledge/${kbId}`)} style={{ color: '#64748b' }}>
                  {t('domainKnowledge.detail')}
                </a>
              ),
            },
            {
              title: <span style={{ color: '#0b2b5c', fontWeight: 500 }}>{t('domainKnowledge.graphBreadcrumb')}</span>,
            },
          ]}
        />
      </div>

      {/* 返回按钮 */}
      <a
        onClick={() => navigate(`/domain-knowledge/${kbId}`)}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          marginBottom: 16,
          fontSize: 14,
          color: '#64748b',
          cursor: 'pointer',
        }}
      >
        <ArrowLeftOutlined /> {t('domainKnowledge.backToResults')}
      </a>

      {/* 顶部信息卡 */}
      <Card
        style={{
          borderRadius: 14,
          marginBottom: 20,
          border: '1px solid #eef2f6',
          boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
        }}
        styles={{ body: { padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 16 } }}
      >
        <div
          style={{
            width: 42,
            height: 42,
            borderRadius: 10,
            background: 'linear-gradient(135deg,#8b5cf6,#7c3aed)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 18,
            color: '#fff',
          }}
        >
          🔗
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#0b2b5c' }}>{t('domainKnowledge.graphTitle')}</div>
          <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 2 }}>
            {stats
              ? t('domainKnowledge.graphStats', {
                  name: stats.knowledge_base_name || '',
                  instances: stats.ontology_instance_count,
                  relations: stats.ontology_relation_count,
                })
              : t('common.loading')}
          </div>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} size="small" onClick={handleRefresh}>
            {t('common.refresh')}
          </Button>
        </Space>
      </Card>

      {/* 主体 */}
      <div style={{ display: 'flex', gap: 20, minHeight: 600 }}>
        <KnowledgeGraphPanel key={refreshKey} kbId={kbId!} />

        {/* 右侧边栏 */}
        <Card
          style={{
            width: 220,
            flexShrink: 0,
            borderRadius: 14,
            border: '1px solid #eef2f6',
            boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
          }}
          styles={{ body: { padding: 20 } }}
        >
          <h4
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: '#0b2b5c',
              marginBottom: 14,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <InfoCircleOutlined style={{ color: '#3b82f6' }} /> {t('domainKnowledge.graphSidebarTitle')}
          </h4>
          {stats ? (
            <>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: 12,
                  padding: '4px 0',
                  color: '#64748b',
                }}
              >
                <span>{t('domainKnowledge.graphEntityTotal')}</span>
                <span style={{ fontWeight: 600, color: '#0b2b5c' }}>{stats.ontology_instance_count}</span>
              </div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: 12,
                  padding: '4px 0',
                  color: '#64748b',
                }}
              >
                <span>{t('domainKnowledge.graphRelationTotal')}</span>
                <span style={{ fontWeight: 600, color: '#0b2b5c' }}>{stats.ontology_relation_count}</span>
              </div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: 12,
                  padding: '4px 0',
                  color: '#64748b',
                }}
              >
                <span>{t('domainKnowledge.graphSourceDocs')}</span>
                <span style={{ fontWeight: 600, color: '#0b2b5c' }}>{stats.source_file_count}</span>
              </div>
            </>
          ) : (
            <div style={{ fontSize: 12, color: '#94a3b8', textAlign: 'center', padding: 20 }}>
              {t('common.loading')}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
