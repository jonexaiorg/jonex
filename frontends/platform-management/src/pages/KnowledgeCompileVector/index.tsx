import React from 'react';
import { Input, Button, Card, List, Tag, Empty } from 'antd';
import { SearchOutlined, FileTextOutlined } from '@ant-design/icons';
import { colors, radius } from '@jonex/platform-theme/tokens';
import { useTranslation } from 'react-i18next';

const vectorResultDefs = [
  { id: 'medicalImaging', score: 0.98, dim: 768 },
  { id: 'riskFeatures', score: 0.95, dim: 768 },
  { id: 'contractLaw', score: 0.91, dim: 768 },
  { id: 'angiography', score: 0.88, dim: 768 },
];

export default function KnowledgeCompileVector() {
  const { t } = useTranslation();
  const [query, setQuery] = React.useState('');
  const [resultIds, setResultIds] = React.useState<string[]>([]);
  const [searched, setSearched] = React.useState(false);
  const mockVectorResults = vectorResultDefs.map((result) => ({
    ...result,
    title: t(`knowledgeCompile.demo.vector.${result.id}.title`),
    chunk: t(`knowledgeCompile.demo.vector.${result.id}.chunk`),
    source: t(`knowledgeCompile.demo.vector.${result.id}.source`),
  }));
  const results = mockVectorResults.filter((result) => resultIds.includes(result.id));

  const handleSearch = () => {
    if (!query.trim()) return;
    setResultIds(mockVectorResults.filter((r) => r.title.includes(query) || r.chunk.includes(query)).map((r) => r.id));
    setSearched(true);
  };

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('knowledgeCompile.vectorPageTitle')}</h1>
        <p style={{ color: colors.textSecondary, margin: '4px 0 0', fontSize: 14 }}>
          {t('knowledgeCompile.vectorPageDesc')}
        </p>
      </div>

      <Card
        style={{ borderRadius: radius.card, border: `1px solid ${colors.border}`, marginBottom: 20 }}
        styles={{ body: { padding: 24 } }}
      >
        <div style={{ display: 'flex', gap: 12 }}>
          <Input
            prefix={<SearchOutlined />}
            placeholder={t('knowledgeCompile.vectorSearchPlaceholder')}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onPressEnter={handleSearch}
            style={{ flex: 1 }}
            size="large"
          />
          <Button type="primary" size="large" onClick={handleSearch}>
            {t('knowledgeCompile.vectorSearchBtn')}
          </Button>
        </div>
      </Card>

      {searched && (
        <Card
          style={{ borderRadius: radius.card, border: `1px solid ${colors.border}` }}
          styles={{ body: { padding: 24 } }}
        >
          <div style={{ marginBottom: 16, color: colors.textSecondary, fontSize: 13 }}>
            <span
              dangerouslySetInnerHTML={{
                __html: t('knowledgeCompile.vectorResults', { dim: 768, count: results.length }),
              }}
            />
          </div>
          {results.length > 0 ? (
            <List
              dataSource={results}
              renderItem={(item) => (
                <List.Item style={{ padding: '14px 0' }}>
                  <div style={{ width: '100%' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      <FileTextOutlined style={{ color: colors.accent }} />
                      <span style={{ fontWeight: 600, fontSize: 15, color: colors.textPrimary }}>{item.title}</span>
                      <Tag color="blue">
                        {t('knowledgeCompile.similarityScore')}: {(item.score * 100).toFixed(0)}%
                      </Tag>
                    </div>
                    <p style={{ color: colors.textSecondary, fontSize: 13, lineHeight: 1.6, margin: '4px 0' }}>
                      {item.chunk}
                    </p>
                    <div style={{ fontSize: 12, color: colors.textMuted }}>
                      {t('knowledgeCompile.source')}: {item.source}
                    </div>
                  </div>
                </List.Item>
              )}
            />
          ) : (
            <Empty description={t('knowledgeCompile.noVectorResults')} />
          )}
        </Card>
      )}
    </div>
  );
}
