import React from 'react';
import { useTranslation } from 'react-i18next';
import { Card, Row, Col, Typography } from 'antd';
import { colors, radius } from '@jonex/platform-theme/tokens';
const { Title, Text } = Typography;
import { MOCK_SCENARIOS } from '../../data/mock';

const MATURITY_LABEL_KEYS: Record<string, string> = {
  production: 'common.maturityProduction',
  pilot: 'common.maturityPilot',
  planning: 'common.maturityPlanning',
};
const MATURITY_CLASS: Record<string, string> = {
  production: 'active',
  pilot: 'running',
  planning: 'pending',
};

export default function ScenarioCatalog() {
  const { t } = useTranslation();
  return (
    <div>
      <div className="page-title">
        <Title level={1} style={{ fontSize: 24, fontWeight: 700, color: colors.brandDark, marginBottom: 4 }}>
          {t('scenarioCatalog.title')}
        </Title>
        <Text type="secondary">{t('scenarioCatalog.subtitle')}</Text>
      </div>
      <Row gutter={[20, 20]}>
        {MOCK_SCENARIOS.map((s) => (
          <Col xs={24} md={12} key={s.id}>
            <Card hoverable style={{ borderRadius: radius.card }} styles={{ body: { padding: 24 } }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: 12,
                    background: `linear-gradient(135deg, ${colors.accentSoft}, ${colors.accent})`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#fff',
                    fontSize: 22,
                  }}
                >
                  {s.name.charAt(0)}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span style={{ fontSize: 16, fontWeight: 600, color: colors.brandDark }}>{s.name}</span>
                    <span className={`yx-status-badge ${MATURITY_CLASS[s.maturity]}`}>
                      {t(MATURITY_LABEL_KEYS[s.maturity] || s.maturity)}
                    </span>
                  </div>
                  <div style={{ fontSize: 13, color: colors.textMuted, marginBottom: 4 }}>
                    {t('scenarioCatalog.industry', { industry: s.industry })}{' '}
                    {t('scenarioCatalog.adapterCount', { count: s.adapterCount })}
                  </div>
                  <div style={{ fontSize: 13, color: colors.textSecondary, marginBottom: 8 }}>{s.description}</div>
                  <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 8 }}>
                    {s.useCases.map((u, i) => (
                      <span key={i} className="yx-tag">
                        {u}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}
