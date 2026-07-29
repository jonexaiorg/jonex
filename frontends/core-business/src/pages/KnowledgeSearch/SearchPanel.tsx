import React from 'react';
import { useTranslation } from 'react-i18next';
import { Input, Select, Button, Card } from 'antd';
import { SearchOutlined, ArrowRightOutlined, StopOutlined } from '@ant-design/icons';
import type { KnowledgeSearchDomain } from '@/types/knowledgeSearch';

interface SearchPanelProps {
  selectedDomain: string;
  visibleDomains: KnowledgeSearchDomain[];
  query: string;
  isSearching: boolean;
  onDomainChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onSearch: () => void;
  onStop: () => void;
}

export default function SearchPanel({
  selectedDomain,
  visibleDomains,
  query,
  isSearching,
  onDomainChange,
  onQueryChange,
  onSearch,
  onStop,
}: SearchPanelProps) {
  const { t } = useTranslation();

  return (
    <Card style={{ borderRadius: 16, marginBottom: 24 }} styles={{ body: { padding: '24px 28px' } }}>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <Select
          value={selectedDomain}
          onChange={onDomainChange}
          style={{ minWidth: 160, height: 48 }}
          size="large"
          options={visibleDomains.map((d) => ({
            value: d.id,
            label: d.id === 'all' ? t('knowledgeSearch.allDomain') : d.name,
          }))}
        />
        <Input
          prefix={<SearchOutlined style={{ color: '#94a3b8', fontSize: 16 }} />}
          placeholder={t('knowledgeSearch.searchPlaceholder')}
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onPressEnter={onSearch}
          style={{ height: 48, fontSize: 15, background: '#f8fafc', borderRadius: 10 }}
        />
        <Button
          type="primary"
          icon={<ArrowRightOutlined />}
          onClick={onSearch}
          loading={isSearching}
          style={{ height: 48, padding: '0 28px', fontSize: 15, borderRadius: 10, flexShrink: 0 }}
        >
          {t('knowledgeSearch.search')}
        </Button>
        {isSearching && (
          <Button
            icon={<StopOutlined />}
            onClick={onStop}
            style={{ height: 48, padding: '0 18px', fontSize: 15, borderRadius: 10, flexShrink: 0 }}
          >
            {t('knowledgeSearch.stop')}
          </Button>
        )}
      </div>
    </Card>
  );
}
