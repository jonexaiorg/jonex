import React from 'react'
import { Input, Button, List, Tag, Card, Empty } from 'antd'
import { useTranslation } from 'react-i18next'
import { SearchOutlined, FileTextOutlined } from '@ant-design/icons'
import { colors, radius } from '@jonex/platform-theme/tokens'

const mockResults = [
  { id: '1', title: '心血管疾病诊疗指南（2025 版）', source: '医疗知识库', type: '文档片段', score: 0.96, tags: ['心血管', '临床指南'] },
  { id: '2', title: '血脂异常管理共识', source: '医疗知识库', type: '文档片段', score: 0.93, tags: ['血脂', '管理共识'] },
  { id: '3', title: '区块链在供应链金融中的应用', source: '金融知识库', type: '文档片段', score: 0.89, tags: ['区块链', '供应链金融'] },
  { id: '4', title: '智能风控模型设计规范', source: '金融知识库', type: '文档片段', score: 0.87, tags: ['风控', '模型设计'] },
  { id: '5', title: '个人信息保护法实施细则', source: '法律知识库', type: '法律条文', score: 0.84, tags: ['个人信息', '法律'] },
]

export default function KnowledgeCompileSearch() {
  const { t } = useTranslation()
  const [query, setQuery] = React.useState('')
  const [results, setResults] = React.useState<typeof mockResults>([])
  const [searched, setSearched] = React.useState(false)

  const handleSearch = () => {
    if (!query.trim()) return
    setResults(mockResults.filter((r) => r.title.includes(query) || r.tags.some((t) => t.includes(query))))
    setSearched(true)
  }

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('knowledgeCompile.search')}</h1>
        <p style={{ color: colors.textSecondary, margin: '4px 0 0', fontSize: 14 }}>
          {t('knowledgeCompile.searchDesc', '搜索已编译的知识库内容')}
        </p>
      </div>

      <Card style={{ borderRadius: radius.card, border: `1px solid ${colors.border}`, marginBottom: 20 }} styles={{ body: { padding: 24 } }}>
        <div style={{ display: 'flex', gap: 12 }}>
          <Input
            prefix={<SearchOutlined />}
            placeholder={t('knowledgeCompile.searchPlaceholder', '输入关键词搜索编译知识...')}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onPressEnter={handleSearch}
            style={{ flex: 1 }}
            size="large"
          />
          <Button type="primary" size="large" onClick={handleSearch}>
            {t('operationLog.search')}
          </Button>
        </div>
      </Card>

      {searched && (
        <Card style={{ borderRadius: radius.card, border: `1px solid ${colors.border}` }} styles={{ body: { padding: 24 } }}>
          <div style={{ marginBottom: 16, color: colors.textSecondary, fontSize: 13 }}>
            {t('knowledgeCompile.foundResults', { count: results.length })}
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
                      <span>{t('knowledgeCompile.source', '来源')}: {item.source}</span>
                      <span>{t('knowledgeCompile.relevance', '相关度')}: {(item.score * 100).toFixed(0)}%</span>
                    </div>
                    <div style={{ marginTop: 6, display: 'flex', gap: 4 }}>
                      {item.tags.map((t) => (
                        <Tag key={t} style={{ fontSize: 11 }}>{t}</Tag>
                      ))}
                    </div>
                  </div>
                </List.Item>
              )}
            />
          ) : (
            <Empty description={t('knowledgeCompile.noResults', '未找到匹配的编译结果')} />
          )}
        </Card>
      )}
    </div>
  )
}
