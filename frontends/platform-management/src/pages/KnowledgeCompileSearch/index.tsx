import React from 'react';
import { Input, Button, List, Tag, Card, Empty } from 'antd';
import { SearchOutlined, FileTextOutlined } from '@ant-design/icons';
import { colors, radius } from '@jonex/platform-theme/tokens';
import { useTranslation } from 'react-i18next';

const resultDefs = [
  { id: 'cardioGuide', score: 0.96, tagCount: 2 },
  { id: 'lipidConsensus', score: 0.93, tagCount: 2 },
  { id: 'blockchainFinance', score: 0.89, tagCount: 2 },
  { id: 'riskModel', score: 0.87, tagCount: 2 },
  { id: 'privacyLaw', score: 0.84, tagCount: 2 },
];

export default function KnowledgeCompileSearch() {
  const { t } = useTranslation();
  const [query, setQuery] = React.useState('');
  const [resultIds, setResultIds] = React.useState<string[]>([]);
  const [searched, setSearched] = React.useState(false);
  const mockResults = resultDefs.map((result) => ({
    ...result,
    title: t(`knowledgeCompile.demo.search.${result.id}.title`),
    source: t(`knowledgeCompile.demo.search.${result.id}.source`),
    type: t(`knowledgeCompile.demo.search.${result.id}.type`),
    tags: Array.from({ length: result.tagCount }, (_, index) =>
      t(`knowledgeCompile.demo.search.${result.id}.tag${index + 1}`),
    ),
  }));
  const results = mockResults.filter((result) => resultIds.includes(result.id));

  const handleSearch = () => {
    if (!query.trim()) return;
    setResultIds(
      mockResults.filter((r) => r.title.includes(query) || r.tags.some((tag) => tag.includes(query))).map((r) => r.id),
    );
    setSearched(true);
  };

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('knowledgeCompile.searchTitle')}</h1>
        <p style={{ color: colors.textSecondary, margin: '4px 0 0', fontSize: 14 }}>
          {t('knowledgeCompile.searchDesc')}
        </p>
      </div>

      <Card
        style={{ borderRadius: radius.card, border: `1px solid ${colors.border}`, marginBottom: 20 }}
        styles={{ body: { padding: 24 } }}
      >
        <div style={{ display: 'flex', gap: 12 }}>
          <Input
            prefix={<SearchOutlined />}
            placeholder={t('knowledgeCompile.searchKnowledge')}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onPressEnter={handleSearch}
            style={{ flex: 1 }}
            size="large"
          />
          <Button type="primary" size="large" onClick={handleSearch}>
            {t('common.search')}
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
              dangerouslySetInnerHTML={{ __html: t('knowledgeCompile.searchResults', { count: results.length }) }}
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
                      <Tag color="blue">{item.type}</Tag>
                    </div>
                    <div style={{ fontSize: 12, color: colors.textMuted, display: 'flex', gap: 16 }}>
                      <span>
                        {t('knowledgeCompile.source')}: {item.source}
                      </span>
                      <span>
                        {t('knowledgeCompile.similarity')}: {(item.score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div style={{ marginTop: 6, display: 'flex', gap: 4 }}>
                      {item.tags.map((t) => (
                        <Tag key={t} style={{ fontSize: 11 }}>
                          {t}
                        </Tag>
                      ))}
                    </div>
                  </div>
                </List.Item>
              )}
            />
          ) : (
            <Empty description={t('knowledgeCompile.noSearchResults')} />
          )}
        </Card>
      )}
    </div>
  );
}
