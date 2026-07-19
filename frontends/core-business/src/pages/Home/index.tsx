import React from 'react'
import { useTranslation } from 'react-i18next'
import { Row, Col, Card, Typography, Statistic } from 'antd'
import { SearchOutlined, AppstoreOutlined, DatabaseOutlined, FileTextOutlined, RightOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { MOCK_DOMAIN_SPACES } from '../../data/mock'
import { colors, radius } from '@jonex/platform-theme/tokens'

const { Title, Text } = Typography

export default function CoreBusinessHome() {
  const { t } = useTranslation()
  const navigate = useNavigate()

  const STATS = [
    { title: t('domainSpace.title'), value: 6, icon: <AppstoreOutlined />, color: colors.accent },
    { title: '知识条目', value: 12890, icon: <DatabaseOutlined />, color: '#10b981' },
    { title: '文档总数', value: 4720, icon: <FileTextOutlined />, color: '#f59e0b' },
    { title: '本月检索', value: '38,562', icon: <SearchOutlined />, color: '#8b5cf6' },
  ]

  return (
    <div>
      <div className="page-title" style={{ marginBottom: 24 }}>
        <Title level={1} style={{ fontSize: 24, fontWeight: 700, color: colors.brandDark, marginBottom: 4 }}>
          {t('domainKnowledge.title')}
        </Title>
        <Text type="secondary" style={{ fontSize: 14 }}>知识检索、领域空间、知识管理与领域配置</Text>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {STATS.map((s) => (
          <Col xs={12} sm={6} key={s.title}>
            <Card style={{ borderRadius: radius.card }} styles={{ body: { padding: '20px 24px' } }}>
              <Statistic
                title={<span style={{ fontSize: 13, color: colors.textSecondary }}>{s.title}</span>}
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
          {t('domainSpace.title')}
        </Title>
        <a onClick={() => navigate('/domain-space')} style={{ fontSize: 13, color: colors.accent, cursor: 'pointer' }}>
          {t('home.viewDetails')} <RightOutlined style={{ fontSize: 12 }} />
        </a>
      </div>
      <Row gutter={[16, 16]}>
        {MOCK_DOMAIN_SPACES.slice(0, 4).map((space) => (
          <Col xs={24} sm={12} lg={6} key={space.id}>
            <Card
              hoverable
              style={{ borderRadius: radius.card }}
              onClick={() => navigate('/domain-space')}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                <div style={{
                  width: 42, height: 42, borderRadius: 10,
                  background: `linear-gradient(135deg, ${colors.accentSoft}, ${colors.accent})`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff', fontSize: 18,
                }}>
                  {space.name.charAt(0)}
                </div>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 600, color: colors.brandDark }}>{space.name}</div>
                  <span className={`yx-status-badge ${space.status}`}>
                    {space.status === 'active' ? t('status.active') : t('status.inactive')}
                  </span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 16, fontSize: 12, color: colors.textMuted }}>
                <span>文档 {space.docCount}</span>
                <span>知识 {space.knowledgeCount}</span>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <div style={{ marginTop: 32 }}>
        <Title level={2} style={{ fontSize: 17, fontWeight: 600, color: colors.brandDark, marginBottom: 16 }}>
          {t('home.quickStart')}
        </Title>
        <Row gutter={[16, 16]}>
          {[
            { label: t('knowledgeSearch.title'), desc: t('knowledgeSearch.allDomainDesc'), path: '/knowledge-search', icon: <SearchOutlined /> },
            { label: t('domainSpace.title'), desc: '管理领域空间', path: '/domain-space', icon: <AppstoreOutlined /> },
            { label: t('domainKnowledge.title'), desc: '领域知识条目', path: '/domain-knowledge', icon: <DatabaseOutlined /> },
            { label: '领域配置', desc: '领域服务与检索', path: '/domain-management', icon: <AppstoreOutlined /> },
          ].map((action) => (
            <Col xs={24} sm={12} md={6} key={action.label}>
              <a
                onClick={() => navigate(action.path)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 14,
                  padding: '18px 20px', background: colors.white,
                  borderRadius: radius.btn, border: `1px solid ${colors.borderLight}`,
                  textDecoration: 'none', cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = colors.borderAccent
                  e.currentTarget.style.boxShadow = '0 2px 8px rgba(59,130,246,0.08)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = colors.borderLight
                  e.currentTarget.style.boxShadow = 'none'
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
  )
}
