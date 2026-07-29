import React from 'react';
import { Button, Card, Select, Tag, Input, Space } from 'antd';
import {
  SaveOutlined,
  ReloadOutlined,
  ThunderboltOutlined,
  RocketOutlined,
  NodeIndexOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

export default function DomainKnowledgeEngine() {
  const { t } = useTranslation();

  const engines = [
    {
      key: 'parser',
      title: t('domainKnowledge.engine.parserEngine'),
      icon: <ThunderboltOutlined />,
      status: t('domainKnowledge.engine.statusRunning'),
      fields: [
        {
          label: t('domainKnowledge.engine.engineVersion'),
          value: t('common.latest', { version: 'v3.2.1' }),
          type: 'select',
          options: [t('common.latest', { version: 'v3.2.1' }), 'v3.1.0'],
        },
        { label: t('domainKnowledge.engine.concurrency'), value: '8', type: 'input' },
        {
          label: t('domainKnowledge.engine.memoryLimit'),
          value: '8 GB',
          type: 'select',
          options: ['4 GB', '8 GB', '16 GB'],
        },
        { label: t('domainKnowledge.engine.timeout'), value: `300 ${t('common.seconds')}`, type: 'input' },
      ],
    },
    {
      key: 'compile',
      title: t('domainKnowledge.engine.compileEngine'),
      icon: <RocketOutlined />,
      status: t('domainKnowledge.engine.statusRunning'),
      fields: [
        {
          label: t('domainKnowledge.engine.engineVersion'),
          value: t('common.latest', { version: 'v2.5.0' }),
          type: 'select',
          options: [t('common.latest', { version: 'v2.5.0' }), 'v2.4.2'],
        },
        {
          label: t('domainKnowledge.engine.compileBatchSize'),
          value: `1000 ${t('domainKnowledge.engine.itemsPerBatch')}`,
          type: 'input',
        },
        { label: t('domainKnowledge.engine.maxEntities'), value: '50000', type: 'input' },
        {
          label: t('domainKnowledge.engine.relationDepth'),
          value: `3 ${t('domainKnowledge.engine.layers')}`,
          type: 'select',
          options: [
            `1 ${t('domainKnowledge.engine.layers')}`,
            `3 ${t('domainKnowledge.engine.layers')}`,
            `5 ${t('domainKnowledge.engine.layers')}`,
            `10 ${t('domainKnowledge.engine.layers')}`,
          ],
        },
      ],
    },
    {
      key: 'vector',
      title: t('domainKnowledge.engine.vectorEngine'),
      icon: <NodeIndexOutlined />,
      status: t('domainKnowledge.engine.statusRunning'),
      fields: [
        { label: t('domainKnowledge.engine.engineVersion'), value: 'v1.8.3', type: 'select', options: ['v1.8.3'] },
        {
          label: t('domainKnowledge.engine.vectorDimension'),
          value: '768',
          type: 'select',
          options: ['256', '768', '1024'],
        },
        {
          label: t('domainKnowledge.engine.batchSize'),
          value: `64 ${t('domainKnowledge.engine.itemsPerBatch')}`,
          type: 'input',
        },
        {
          label: t('domainKnowledge.engine.gpuAccel'),
          value: t('domainKnowledge.engine.enabled'),
          type: 'select',
          options: [t('domainKnowledge.engine.enabled'), t('domainKnowledge.engine.disabled')],
        },
      ],
    },
    {
      key: 'search',
      title: t('domainKnowledge.engine.searchEngine'),
      icon: <SearchOutlined />,
      status: t('domainKnowledge.engine.statusRunning'),
      fields: [
        { label: t('domainKnowledge.engine.engineVersion'), value: 'v2.1.0', type: 'select', options: ['v2.1.0'] },
        {
          label: t('domainKnowledge.engine.retrievalAlgo'),
          value: 'HNSW',
          type: 'select',
          options: ['HNSW', 'IVF', 'FLAT'],
        },
        { label: t('domainKnowledge.engine.defaultTopK'), value: '10', type: 'input' },
        {
          label: t('domainKnowledge.engine.cacheStrategy'),
          value: 'LRU',
          type: 'select',
          options: ['LRU', 'LFU', 'TTL'],
        },
      ],
    },
  ];

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('domainKnowledge.engine.config')}</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 14 }}>{t('domainKnowledge.engine.configDesc')}</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 20 }}>
        {engines.map((engine) => (
          <Card key={engine.key} style={{ borderRadius: 12, border: '1px solid #e2e8f0' }} bodyStyle={{ padding: 24 }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
              {engine.icon} {engine.title}
              <Tag color="success" style={{ marginLeft: 'auto', fontSize: 11 }}>
                {engine.status}
              </Tag>
            </h3>
            {engine.fields.map((f) => (
              <div className="yx-form-row" key={f.label}>
                <label>{f.label}</label>
                {f.type === 'select' ? (
                  <Select
                    defaultValue={f.value}
                    style={{ width: '100%' }}
                    options={f.options!.map((o) => ({ value: o, label: o }))}
                  />
                ) : (
                  <Input defaultValue={f.value} />
                )}
              </div>
            ))}
          </Card>
        ))}
      </div>

      <div style={{ marginTop: 20, display: 'flex', gap: 12 }}>
        <Button type="primary" icon={<SaveOutlined />}>
          {t('common.saveConfig')}
        </Button>
        <Button icon={<ReloadOutlined />}>{t('common.restartEngine')}</Button>
      </div>
    </div>
  );
}
