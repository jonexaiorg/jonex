import React from 'react'
import { Input, Button, Card, List, Tag, Empty } from 'antd'
import { useTranslation } from 'react-i18next'
import { SearchOutlined, FileTextOutlined } from '@ant-design/icons'
import { colors, radius } from '@jonex/platform-theme/tokens'

const mockVectorResults = [
  { id: '1', title: '深度学习在医学影像诊断中的应用', chunk: '近年来，深度学习技术在医学影像领域取得了显著进展...', score: 0.98, dim: 768, source: '医疗知识库' },
  { id: '2', title: '金融风控模型特征工程实践', chunk: '特征工程是构建高效风控模型的关键步骤...', score: 0.95, dim: 768, source: '金融知识库' },
  { id: '3', title: '合同法第52条解析', chunk: '有下列情形之一的，合同无效：（一）一方以欺诈、胁迫的手段订立合同...', score: 0.91, dim: 768, source: '法律知识库' },
  { id: '4', title: '冠状动脉造影操作规范', chunk: '冠状动脉造影是诊断冠心病的金标准，操作规范包括...', score: 0.88, dim: 768, source: '医疗知识库' },
]

export default function KnowledgeCompileVector() {
  const { t } = useTranslation()
  const [query, setQuery] = React.useState('')
  const [results, setResults] = React.useState<typeof mockVectorResults>([])
  const [searched, setSearched] = React.useState(false)

  const handleSearch = () => {
    if (!query.trim()) return
    setResults(mockVectorResults.filter((r) => r.title.includes(query) || r.chunk.includes(query)))
    setSearched(true)
  }

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('knowledgeCompile.vector')}</h1>
        <p style={{ color: colors.textSecondary, margin: '4px 0 0', fontSize: 14 }}>
          {t('knowledgeCompile.vectorDesc', '基于向量语义相似度进行知识召回测试')}
        </p>
      </div>

      <Card style={{ borderRadius: radius.card, border: `1px solid ${colors.border}`, marginBottom: 20 }} styles={{ body: { padding: 24 } }}>
        <div style={{ display: 'flex', gap: 12 }}>
          <Input
            prefix={<SearchOutlined />}
            placeholder={t('knowledgeCompile.vectorPlaceholder', '输入查询文本，测试向量相似度召回...')}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onPressEnter={handleSearch}
            style={{ flex: 1 }}
            size="large"
          />
          <Button type="primary" size="large" onClick={handleSearch}>
            {t('knowledgeCompile.vector')}
          </Button>
        </div>
      </Card>

      {searched && (
        <Card style={{ borderRadius: radius.card, border: `1px solid ${colors.border}` }} styles={{ body: { padding: 24 } }}>
          <div style={{ marginBottom: 16, color: colors.textSecondary, fontSize: 13 }}>
            {t('knowledgeCompile.vectorResults', { dim: 768, count: results.length })}
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
                      <Tag color="blue">{t('knowledgeCompile.similarity', '相似度')}: {(item.score * 100).toFixed(0)}%</Tag>
                    </div>
                    <p style={{ color: colors.textSecondary, fontSize: 13, lineHeight: 1.6, margin: '4px 0' }}>
                      {item.chunk}
                    </p>
                    <div style={{ fontSize: 12, color: colors.textMuted }}>
                      {t('knowledgeCompile.source', '来源')}: {item.source}
                    </div>
                  </div>
                </List.Item>
              )}
            />
          ) : (
            <Empty description={t('knowledgeCompile.noVectorResults', '未找到向量检索结果')} />
          )}
        </Card>
      )}
    </div>
  )
}
