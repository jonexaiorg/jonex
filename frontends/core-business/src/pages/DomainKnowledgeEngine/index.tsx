import React from 'react'
import { Button, Card, Select, Tag, Input, Space } from 'antd'
import { SaveOutlined, ReloadOutlined, ThunderboltOutlined, RocketOutlined, NodeIndexOutlined, SearchOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'

export default function DomainKnowledgeEngine() {
  const { t } = useTranslation()

  const engines = [
    {
      key: 'parser', title: t('domainEngine.parser'), icon: <ThunderboltOutlined />, status: t('domainEngine.running'),
      fields: [
        { label: t('domainEngine.engineVersion'), value: t('domainEngine.latest', { val: 'v3.2.1' }), type: 'select', options: [t('domainEngine.latest', { val: 'v3.2.1' }), 'v3.1.0'] },
        { label: t('domainEngine.concurrency'), value: '8', type: 'input' },
        { label: t('domainEngine.memoryLimit'), value: '8 GB', type: 'select', options: ['4 GB', '8 GB', '16 GB'] },
        { label: t('domainEngine.timeout'), value: t('domainEngine.seconds', { val: 300 }), type: 'input' },
      ],
    },
    {
      key: 'compile', title: t('domainEngine.compile'), icon: <RocketOutlined />, status: t('domainEngine.running'),
      fields: [
        { label: t('domainEngine.engineVersion'), value: t('domainEngine.latest', { val: 'v2.5.0' }), type: 'select', options: [t('domainEngine.latest', { val: 'v2.5.0' }), 'v2.4.2'] },
        { label: t('domainEngine.batchSize'), value: t('domainEngine.itemsPerBatch', { val: 1000 }), type: 'input' },
        { label: t('domainEngine.maxEntity'), value: '50000', type: 'input' },
        { label: t('domainEngine.relationDepth'), value: t('domainEngine.layer1', { val: 3 }), type: 'select', options: [t('domainEngine.layer1', { val: 1 }), t('domainEngine.layer1', { val: 3 }), t('domainEngine.layer1', { val: 5 }), t('domainEngine.layer1', { val: 10 })] },
      ],
    },
    {
      key: 'vector', title: t('domainEngine.vector'), icon: <NodeIndexOutlined />, status: t('domainEngine.running'),
      fields: [
        { label: t('domainEngine.engineVersion'), value: 'v1.8.3', type: 'select', options: ['v1.8.3'] },
        { label: t('domainEngine.vectorDimension'), value: '768', type: 'select', options: ['256', '768', '1024'] },
        { label: t('domainEngine.batchProcess'), value: t('domainEngine.itemsPerBatch', { val: 64 }), type: 'input' },
        { label: t('domainEngine.gpuAccel'), value: t('domainEngine.enabled'), type: 'select', options: [t('domainEngine.enabled'), t('domainEngine.disabled')] },
      ],
    },
    {
      key: 'search', title: t('domainEngine.search'), icon: <SearchOutlined />, status: t('domainEngine.running'),
      fields: [
        { label: t('domainEngine.engineVersion'), value: 'v2.1.0', type: 'select', options: ['v2.1.0'] },
        { label: t('domainEngine.searchAlgo'), value: 'HNSW', type: 'select', options: ['HNSW', 'IVF', 'FLAT'] },
        { label: 'Top-K 默认值', value: '10', type: 'input' },
        { label: t('domainEngine.cacheStrategy'), value: 'LRU', type: 'select', options: ['LRU', 'LFU', 'TTL'] },
      ],
    },
  ]

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('knowledgeSearch.engineConfig')}</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 14 }}>管理各引擎的参数与运行配置</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 20 }}>
        {engines.map((engine) => (
          <Card key={engine.key} style={{ borderRadius: 12, border: '1px solid #e2e8f0' }} bodyStyle={{ padding: 24 }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
              {engine.icon} {engine.title}
              <Tag color="success" style={{ marginLeft: 'auto', fontSize: 11 }}>{engine.status}</Tag>
            </h3>
            {engine.fields.map((f) => (
              <div className="yx-form-row" key={f.label}>
                <label>{f.label}</label>
                {f.type === 'select' ? (
                  <Select defaultValue={f.value} style={{ width: '100%' }} options={(f.options!).map((o) => ({ value: o, label: o }))} />
                ) : (
                  <Input defaultValue={f.value} />
                )}
              </div>
            ))}
          </Card>
        ))}
      </div>

      <div style={{ marginTop: 20, display: 'flex', gap: 12 }}>
        <Button type="primary" icon={<SaveOutlined />}>{t('common.save')}</Button>
        <Button icon={<ReloadOutlined />}>重启引擎</Button>
      </div>
    </div>
  )
}
