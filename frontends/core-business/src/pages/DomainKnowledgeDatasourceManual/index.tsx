import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, Input, Space, message } from 'antd';
import {
  ArrowLeftOutlined,
  UploadOutlined,
  TagOutlined,
  GlobalOutlined,
  FileTextOutlined,
  FileOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import type { ManualDocItem, DomainKnowledgeDetail as DomainKnowledgeDetailType } from '@/types/domainKnowledge';
import { getDomainKnowledgeDetail } from '@/api/domainKnowledge';
import { getManualDocList } from '@/api/domainKnowledge';
import DataSourceDocTable from '@/components/datasource/DataSourceDocTable';
import DocumentStatusFilter from '@/components/DocumentStatusFilter';
import DocumentStatsBar from '@/components/DocumentStatsBar';
import { type DocPhase } from '@/utils/docPhase';
import { FORMAT_DISPLAY } from '@/constants/upload';

const PAGE_SIZE = 7;

export default function DomainKnowledgeDatasourceManual() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // ── header info ──────────────────────────────────────
  const [detail, setDetail] = useState<DomainKnowledgeDetailType | null>(null);
  const [detailLoading, setDetailLoading] = useState(true);

  // ── doc list ──────────────────────────────────────────
  const [docs, setDocs] = useState<ManualDocItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [keywordInput, setKeywordInput] = useState('');
  const [keyword, setKeyword] = useState('');
  const [phase, setPhase] = useState<DocPhase[]>([]);
  const [loading, setLoading] = useState(false);
  // 手动刷新计数器：删除后递增，强制单一数据 effect 重新拉取（即使 page 未变）
  const [reloadFlag, setReloadFlag] = useState(0);

  const debounceRef = useRef<ReturnType<typeof setTimeout>>();
  // ── fetch header ──────────────────────────────────────
  useEffect(() => {
    if (!id) return;
    setDetailLoading(true);
    getDomainKnowledgeDetail(id)
      .then(setDetail)
      .catch((err: any) => message.error(err?.message || t('common.knowledgeBaseDetailLoadFailed')))
      .finally(() => setDetailLoading(false));
  }, [id, t]);

  // ── fetch doc list ────────────────────────────────────
  const fetchList = useCallback(
    async (p: number, kw: string, ph: DocPhase[]) => {
      if (!id) return;
      setLoading(true);
      try {
        const result = await getManualDocList({
          knowledgeBaseId: id,
          page: p,
          pageSize: PAGE_SIZE,
          keyword: kw || undefined,
          phase: ph.length ? ph : undefined,
        });
        setDocs(result.list);
        setTotal(result.pagination.total);
      } catch (err: any) {
        message.error(err?.message || t('common.docListLoadFailed'));
      } finally {
        setLoading(false);
      }
    },
    [id, t],
  );

  // ── keyword debounce → 关键词变化时重置回第 1 页 ────────
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setKeyword(keywordInput);
      setPage(1);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [keywordInput]);

  // ── 唯一数据拉取来源：page / keyword / 手动刷新(reloadFlag) 任一变化即拉取 ──
  // 翻页和刷新都收敛到此 effect，避免「点击页码 1 时 page 守卫拦截而不发请求」。
  useEffect(() => {
    fetchList(page, keyword, phase);
  }, [page, keyword, phase, reloadFlag, fetchList]);

  return (
    <div>
      <a
        onClick={() => navigate(`/domain-knowledge/${id}/detail`)}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          marginBottom: 16,
          fontSize: 14,
          color: '#64748b',
          cursor: 'pointer',
        }}
      >
        <ArrowLeftOutlined /> {t('domainKnowledge.backToKnowledgeDetail')}
      </a>

      <Card
        style={{
          borderRadius: 14,
          marginBottom: 24,
          border: '1px solid #eef2f6',
          boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
        }}
        bodyStyle={{
          padding: '20px 24px',
          display: 'flex',
          alignItems: 'center',
          gap: 16,
        }}
      >
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: 12,
            background: '#eff6ff',
            color: '#3b82f6',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 22,
            flexShrink: 0,
          }}
        >
          <UploadOutlined />
        </div>
        <div style={{ flex: 1 }}>
          <h2
            style={{
              fontSize: 18,
              fontWeight: 700,
              color: '#0b2b5c',
              margin: 0,
            }}
          >
            {detailLoading
              ? t('common.loading')
              : detail
                ? t('domainKnowledge.manualUploadWithName', {
                    name: detail.name,
                  })
                : t('route.datasourceManual')}
          </h2>
          <div
            style={{
              display: 'flex',
              gap: 16,
              marginTop: 4,
              fontSize: 13,
              color: '#64748b',
              flexWrap: 'wrap',
            }}
          >
            <span>
              <TagOutlined style={{ marginRight: 4 }} />
              {t('domainKnowledge.manualUpload')}
            </span>
            <span>
              <GlobalOutlined style={{ marginRight: 4 }} />
              {detail?.spaceName || '--'}
            </span>
            <span>
              <FileTextOutlined style={{ marginRight: 4 }} />
              {t('domainKnowledge.docsCount', { count: total })}
            </span>
            <span>
              <FileOutlined style={{ marginRight: 4 }} />
              {FORMAT_DISPLAY}
            </span>
          </div>
        </div>
      </Card>

      <Card
        style={{
          borderRadius: 14,
          border: '1px solid #eef2f6',
          boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
        }}
        bodyStyle={{ padding: 0 }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 20px',
            borderBottom: '1px solid #eef2f6',
          }}
        >
          <Space>
            <span
              style={{
                fontSize: 14,
                fontWeight: 600,
                color: '#0b2b5c',
              }}
            >
              {t('domainKnowledge.documentList')}
            </span>
            <Input
              prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
              placeholder={t('common.keywordSearch')}
              style={{ width: 240 }}
              value={keywordInput}
              onChange={(e) => setKeywordInput(e.target.value)}
            />
          </Space>
          <DocumentStatusFilter
            value={phase}
            onChange={(p) => {
              setPhase(p);
              setPage(1);
            }}
          />
        </div>
        <div
          style={{
            padding: '12px 20px',
            borderBottom: '1px solid #eef2f6',
          }}
        >
          <DocumentStatsBar knowledgeBaseId={id || ''} reloadFlag={reloadFlag} />
        </div>
        <DataSourceDocTable kbId={id || ''} docs={docs} loading={loading} pageSize={PAGE_SIZE} />
      </Card>
    </div>
  );
}
