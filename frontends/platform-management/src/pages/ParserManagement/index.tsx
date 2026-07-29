import {
  SearchOutlined,
  VideoCameraOutlined,
  AudioOutlined,
  FileImageOutlined,
  FileTextOutlined,
  GlobalOutlined,
  PartitionOutlined,
} from '@ant-design/icons';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button, Input } from 'antd';
import { listParsers, type ParserItem } from '@/api/parsers';
import './index.css';

interface DisplayField {
  label: string;
  value: string;
}

interface PrototypeParserView {
  desc: string;
  color: string;
  icon: React.ReactNode;
  fields: DisplayField[];
  order: number;
}

const BUILT_IN_PARSER_NAME_KEYS: Record<string, string> = {
  video_full_pipeline: 'parserManagement.nameVideo',
  parser_demo_video: 'parserManagement.nameVideo',
  audio_transcribe: 'parserManagement.nameAudio',
  parser_demo_audio: 'parserManagement.nameAudio',
  image_parse: 'parserManagement.nameImage',
  parser_demo_image: 'parserManagement.nameImage',
  document_parse: 'parserManagement.nameDocument',
  parser_demo_document: 'parserManagement.nameDocument',
  text_parse: 'parserManagement.nameText',
  parser_demo_text: 'parserManagement.nameText',
  parser_demo_web: 'parserManagement.nameWeb',
  parser_demo_cad: 'parserManagement.nameCad',
};

function parserDisplayName(parser: ParserItem, t: (key: string) => string): string {
  const key = BUILT_IN_PARSER_NAME_KEYS[parser.id];
  return key ? t(key) : parser.name;
}

function getPrototypeParsers(
  t: (key: string, options?: Record<string, unknown>) => string,
): Record<string, PrototypeParserView> {
  return {
    video: {
      desc: t('parserManagement.videoDesc'),
      color: '#ef4444',
      icon: <VideoCameraOutlined />,
      fields: [
        { label: t('parserManagement.keyFrameExtraction'), value: t('parserManagement.smartMode') },
        { label: t('parserManagement.resolutionLimit'), value: '1080p' },
      ],
      order: 0,
    },
    audio: {
      desc: t('parserManagement.audioDesc'),
      color: '#8b5cf6',
      icon: <AudioOutlined />,
      fields: [
        { label: t('parserManagement.transcriptionModel'), value: t('parserManagement.generalTranscriptionModel') },
        { label: t('parserManagement.outputFormat'), value: 'SRT' },
      ],
      order: 1,
    },
    image: {
      desc: t('parserManagement.imageDesc'),
      color: '#f59e0b',
      icon: <FileImageOutlined />,
      fields: [
        { label: t('parserManagement.ocrEngine'), value: t('parserManagement.builtInOcr') },
        { label: t('parserManagement.imageCompression'), value: t('parserManagement.highQuality') },
      ],
      order: 2,
    },
    document: {
      desc: t('parserManagement.documentDesc'),
      color: '#3b82f6',
      icon: <FileTextOutlined />,
      fields: [
        { label: t('parserManagement.layoutPreservation'), value: t('parserManagement.layoutEnabled') },
        { label: t('parserManagement.tableExtraction'), value: t('parserManagement.smartExtraction') },
      ],
      order: 3,
    },
    txt: {
      desc: t('parserManagement.textDesc'),
      color: '#3b82f6',
      icon: <FileTextOutlined />,
      fields: [
        { label: t('parserManagement.layoutPreservation'), value: t('parserManagement.layoutEnabled') },
        { label: t('parserManagement.tableExtraction'), value: t('parserManagement.smartExtraction') },
      ],
      order: 4,
    },
    web: {
      desc: t('parserManagement.webDesc'),
      color: '#94a3b8',
      icon: <GlobalOutlined />,
      fields: [
        { label: t('parserManagement.renderMode'), value: t('parserManagement.staticRender') },
        { label: t('parserManagement.scrapeDepth'), value: '--' },
      ],
      order: 5,
    },
    cad: {
      desc: t('parserManagement.cadDesc'),
      color: '#94a3b8',
      icon: <PartitionOutlined />,
      fields: [
        { label: t('parserManagement.precisionLevel'), value: t('parserManagement.standardPrecision') },
        { label: t('parserManagement.layerExtraction'), value: t('parserManagement.allLayers') },
      ],
      order: 6,
    },
  };
}

function iconForType(type: string, parsers: Record<string, PrototypeParserView>): React.ReactNode {
  return parsers[type]?.icon || <FileTextOutlined />;
}

function colorForType(type: string, active: boolean, parsers: Record<string, PrototypeParserView>): string {
  if (!active) return '#94a3b8';
  return parsers[type]?.color || '#3b82f6';
}

function parserDesc(
  parser: ParserItem,
  parsers: Record<string, PrototypeParserView>,
  t: (key: string, options?: Record<string, unknown>) => string,
): string {
  return (
    parsers[parser.parser_type]?.desc ||
    t('parserManagement.fallbackDesc', { fileTypes: (parser.file_types || []).join('/'), name: parser.name })
  );
}

function formatProcessCount(value: unknown, active: boolean): string {
  if (!active) return '--';
  if (typeof value === 'number') return value.toLocaleString();
  if (typeof value === 'string' && value) return value;
  return '--';
}

function displayFields(
  parser: ParserItem,
  parsers: Record<string, PrototypeParserView>,
  t: (key: string, options?: Record<string, unknown>) => string,
): DisplayField[] {
  const prototype = parsers[parser.parser_type];
  if (prototype) return prototype.fields;

  const raw = parser.config_json?.display_fields;
  if (Array.isArray(raw)) {
    return raw
      .map((item) => ({
        label: String((item as any).label || ''),
        value: String((item as any).value || '--'),
      }))
      .filter((item) => item.label);
  }
  return [
    { label: t('parserManagement.supportedFormats'), value: (parser.file_types || []).slice(0, 4).join(' / ') || '--' },
    { label: t('parserManagement.parserTypeLabel'), value: parser.parser_type || '--' },
  ];
}

function getErrorMessage(error: unknown, t: (key: string, options?: Record<string, unknown>) => string): string {
  if (error instanceof Error) return error.message;
  return t('parserManagement.requestFailed');
}

export default function ParserManagement() {
  const { t } = useTranslation();
  const [search, setSearch] = useState('');
  const [parsers, setParsers] = useState<ParserItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const prototypeParsers = useMemo(() => getPrototypeParsers(t), [t]);

  const loadParsers = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const resp = await listParsers(0, 100);
      setParsers(resp.items || []);
    } catch (err) {
      setError(getErrorMessage(err, t));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    void loadParsers();
  }, [loadParsers]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    const visibleParsers = parsers
      .filter((parser) => Boolean(prototypeParsers[parser.parser_type]))
      .sort((a, b) => prototypeParsers[a.parser_type].order - prototypeParsers[b.parser_type].order);

    if (!q) return visibleParsers;
    return visibleParsers.filter((parser) => {
      const fileTypes = (parser.file_types || []).join(' ').toLowerCase();
      const displayName = parserDisplayName(parser, t).toLowerCase();
      return (
        parser.name.toLowerCase().includes(q) ||
        displayName.includes(q) ||
        parser.parser_type.toLowerCase().includes(q) ||
        fileTypes.includes(q)
      );
    });
  }, [parsers, search, prototypeParsers, t]);

  return (
    <div>
      <div className="yx-page-title">
        <h1 style={{ fontSize: 22, fontWeight: 700, color: '#0b2b5c', margin: 0 }}>
          {t('parserManagement.pageTitle')}
        </h1>
      </div>
      <div style={{ marginBottom: 20, marginTop: 8 }}>
        <Input
          prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
          placeholder={t('parserManagement.searchPlaceholder')}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: 240 }}
        />
      </div>

      {error && (
        <div className="parser-page-error">
          <span>{error}</span>
          <Button onClick={() => void loadParsers()}>{t('common.retry')}</Button>
        </div>
      )}

      <div className="parser-grid">
        {loading ? (
          <div className="parser-state">{t('parserManagement.loading')}</div>
        ) : filtered.length === 0 ? (
          <div className="parser-state">{t('parserManagement.empty')}</div>
        ) : (
          filtered.map((parser) => {
            const isActive = parser.status === 'active';
            const version = String(parser.config_json?.version || '--');
            const processCount = formatProcessCount(parser.config_json?.process_count, isActive);

            return (
              <div key={parser.id} className={`parser-card${isActive ? '' : ' grey'}`}>
                <div
                  className="parser-icon"
                  style={{ color: colorForType(parser.parser_type, isActive, prototypeParsers) }}
                >
                  {iconForType(parser.parser_type, prototypeParsers)}
                </div>
                {!isActive && <div className="future-tag">{t('parserManagement.comingSoon')}</div>}
                <h3>
                  {parser.name}{' '}
                  <span style={{ fontSize: 12, color: isActive ? '#22c55e' : '#94a3b8', fontWeight: 400 }}>
                    {isActive ? t('status.enabled') : t('status.disabled')}
                  </span>
                </h3>
                <div className="parser-desc">{parserDesc(parser, prototypeParsers, t)}</div>
                <div className="parser-meta">
                  <span>
                    {t('parserManagement.version')} {version}
                  </span>
                  <span>
                    {t('parserManagement.processCount')} {processCount}
                  </span>
                </div>
                {displayFields(parser, prototypeParsers, t).map((row) => (
                  <div key={row.label} className="form-row">
                    <label>{row.label}</label>
                    <div style={{ fontSize: 13, color: '#334155', padding: '2px 0' }}>{row.value}</div>
                  </div>
                ))}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
