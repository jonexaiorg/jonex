import React from 'react';
import { Row, Col, Card, Typography, Statistic } from 'antd';
import { SearchOutlined, AppstoreOutlined, DatabaseOutlined, FileTextOutlined, RightOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { MOCK_DOMAIN_SPACES } from '../../data/mock';
import { colors, radius } from '@jonex/platform-theme/tokens';

const { Title, Text } = Typography;

const STATS = [
  { titleKey: 'domainSpace.management', value: 6, icon: <AppstoreOutlined />, color: colors.accent },
  { titleKey: 'home.knowledgeItems', value: 12890, icon: <DatabaseOutlined />, color: '#10b981' },
  { titleKey: 'home.totalDocuments', value: 4720, icon: <FileTextOutlined />, color: '#f59e0b' },
  { titleKey: 'home.monthlySearches', value: '38,562', icon: <SearchOutlined />, color: '#8b5cf6' },
];

export default function CoreBusinessHome() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <div>
      <div className="page-title" style={{ marginBottom: 24 }}>
        <Title level={1} style={{ fontSize: 24, fontWeight: 700, color: colors.brandDark, marginBottom: 4 }}>
          {t('home.title')}
        </Title>
        <Text type="secondary" style={{ fontSize: 14 }}>
          {t('home.welcomeDescription')}
        </Text>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {STATS.map((s) => (
          <Col xs={12} sm={6} key={s.titleKey}>
            <Card style={{ borderRadius: radius.card }} styles={{ body: { padding: '20px 24px' } }}>
              <Statistic
                title={<span style={{ fontSize: 13, color: colors.textSecondary }}>{t(s.titleKey)}</span>}
                value={s.value}
                valueStyle={{ fontSize: 28, fontWeight: 700, color: colors.brandDark }}
                prefix={<span style={{ fontSize: 20, color: s.color, marginRight: 8 }}>{s.icon}</span>}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Title level={2} style={{ fontSize: 17, fontWeight: 600, color: colors.brandDark, margin: 0 }}>
          {t('domainSpace.management')}
        </Title>
        <a onClick={() => navigate('/domain-space')} style={{ fontSize: 13, color: colors.accent, cursor: 'pointer' }}>
          {t('common.viewAll')} <RightOutlined style={{ fontSize: 12 }} />
        </a>
      </div>
      <Row gutter={[16, 16]}>
        {MOCK_DOMAIN_SPACES.slice(0, 4).map((space) => (
          <Col xs={24} sm={12} lg={6} key={space.id}>
            <Card hoverable style={{ borderRadius: radius.card }} onClick={() => navigate('/domain-space')}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                <div
                  style={{
                    width: 42,
                    height: 42,
                    borderRadius: 10,
                    background: `linear-gradient(135deg, ${colors.accentSoft}, ${colors.accent})`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#fff',
                    fontSize: 18,
                  }}
                >
                  {space.name.charAt(0)}
                </div>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 600, color: colors.brandDark }}>{space.name}</div>
                  <span className={`yx-status-badge ${space.status}`}>
                    {t(space.status === 'active' ? 'status.active' : 'status.inactive')}
                  </span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 16, fontSize: 12, color: colors.textMuted }}>
                <span>
                  {t('home.documents')} {space.docCount}
                </span>
                <span>
                  {t('home.knowledge')} {space.knowledgeCount}
                </span>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <div style={{ marginTop: 32 }}>
        <Title level={2} style={{ fontSize: 17, fontWeight: 600, color: colors.brandDark, marginBottom: 16 }}>
          {t('home.quickActions')}
        </Title>
        <Row gutter={[16, 16]}>
          {[
            {
              label: t('knowledgeSearch.title'),
              desc: t('home.knowledgeSearchDesc'),
              path: '/knowledge-search',
              icon: <SearchOutlined />,
            },
            {
              label: t('domainSpace.management'),
              desc: t('home.manageSpaces'),
              path: '/domain-space',
              icon: <AppstoreOutlined />,
            },
            {
              label: t('home.knowledgeManagement'),
              desc: t('home.knowledgeEntries'),
              path: '/domain-knowledge',
              icon: <DatabaseOutlined />,
            },
            {
              label: t('domainConfig.title'),
              desc: t('domainConfig.description'),
              path: '/domain-management',
              icon: <AppstoreOutlined />,
            },
          ].map((action, i) => (
            <Col xs={24} sm={12} md={6} key={i}>
              <a
                onClick={() => navigate(action.path)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 14,
                  padding: '18px 20px',
                  background: colors.white,
                  borderRadius: radius.btn,
                  border: `1px solid ${colors.borderLight}`,
                  textDecoration: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = colors.borderAccent;
                  e.currentTarget.style.boxShadow = '0 2px 8px rgba(59,130,246,0.08)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = colors.borderLight;
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <span style={{ fontSize: 22, color: colors.accent }}>{action.icon}</span>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 500, color: colors.textPrimary }}>{action.label}</div>
                  <div style={{ fontSize: 12, color: colors.textMuted }}>{action.desc}</div>
                </div>
              </a>
            </Col>
          ))}
        </Row>
      </div>
    </div>
  );
}
