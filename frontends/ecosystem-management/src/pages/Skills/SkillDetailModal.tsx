import React from 'react';
import { useTranslation } from 'react-i18next';
import { Button, Modal, Space, Tag, Typography, Descriptions } from 'antd';
import {
  FileImageOutlined,
  AudioOutlined,
  FileTextOutlined,
  VideoCameraOutlined,
  DatabaseOutlined,
  SearchOutlined as FusionSearchOutlined,
} from '@ant-design/icons';
import type { SkillItem } from '../../api/skills';

const { Text, Paragraph } = Typography;

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  image: <FileImageOutlined />,
  voice: <AudioOutlined />,
  document: <FileTextOutlined />,
  video: <VideoCameraOutlined />,
  fusion: <FusionSearchOutlined />,
  custom: <DatabaseOutlined />,
};

const CATEGORY_LABEL_KEYS: Record<string, string> = {
  image: 'skills.categoryImage',
  voice: 'skills.categoryVoice',
  document: 'skills.categoryDocument',
  video: 'skills.categoryVideo',
  fusion: 'skills.categoryFusion',
  custom: 'skills.categoryCustom',
};

const BUILT_IN_SKILL_KEYS: Record<string, string> = {
  skill_image_recognition: 'imageRecognition',
  skill_speech_to_text: 'speechToText',
  skill_document_layout: 'documentLayout',
  skill_video_understanding: 'videoUnderstanding',
  skill_multimodal_search: 'multimodalSearch',
  skill_data_extraction: 'dataExtraction',
};

const SCHEMA_DESCRIPTION_KEYS: Record<string, string> = {
  file_url: 'skills.schemaDescriptions.fileUrl',
  tasks: 'skills.schemaDescriptions.tasks',
  language: 'skills.schemaDescriptions.language',
  speaker_diarization: 'skills.schemaDescriptions.speakerDiarization',
  output_format: 'skills.schemaDescriptions.outputFormat',
  sample_rate: 'skills.schemaDescriptions.sampleRate',
  modalities: 'skills.schemaDescriptions.modalities',
  top_k: 'skills.schemaDescriptions.topK',
  schema: 'skills.schemaDescriptions.schema',
  doc_type: 'skills.schemaDescriptions.documentType',
};

function localizeSchemaDescriptions(value: unknown, t: (key: string) => string, parentKey = ''): unknown {
  if (Array.isArray(value)) return value.map((item) => localizeSchemaDescriptions(item, t, parentKey));
  if (!value || typeof value !== 'object') return value;
  return Object.fromEntries(
    Object.entries(value as Record<string, unknown>).map(([key, item]) => {
      if (key === 'description' && typeof item === 'string') {
        const translationKey = SCHEMA_DESCRIPTION_KEYS[parentKey];
        return [key, translationKey ? t(translationKey) : item];
      }
      return [key, localizeSchemaDescriptions(item, t, key)];
    }),
  );
}

function formatJsonSchema(schema: Record<string, unknown>): string {
  try {
    return JSON.stringify(schema, null, 2);
  } catch {
    return '{}';
  }
}

function getSkillDetail(skill: SkillItem, t: (key: string) => string) {
  const key = BUILT_IN_SKILL_KEYS[skill.id];
  if (!key) {
    return {
      name: skill.name,
      description: skill.description || '',
      instruction: skill.instruction,
    };
  }
  return {
    name: t(`skills.builtIn.${key}.name`),
    description: t(`skills.builtIn.${key}.description`),
    instruction: t(`skills.builtIn.${key}.instruction`),
  };
}

interface SkillDetailModalProps {
  open: boolean;
  skill: SkillItem | null;
  onClose: () => void;
}

export default function SkillDetailModal({ open, skill, onClose }: SkillDetailModalProps) {
  const { t } = useTranslation();
  const detail = skill ? getSkillDetail(skill, t) : null;

  return (
    <Modal
      title={
        <Space>
          <span style={{ fontSize: 24 }}>{CATEGORY_ICONS[skill?.category || 'custom']}</span>
          <span>{detail?.name}</span>
        </Space>
      }
      open={open}
      onCancel={onClose}
      footer={<Button onClick={onClose}>{t('common.close')}</Button>}
      width={680}
    >
      {skill && detail && (
        <div>
          <Descriptions column={2} size="small" bordered style={{ marginBottom: 16 }}>
            <Descriptions.Item label={t('skills.categoryLabel')}>
              {t(CATEGORY_LABEL_KEYS[skill.category])}
            </Descriptions.Item>
            <Descriptions.Item label={t('common.status')}>
              <Tag color={skill.enabled ? 'green' : 'default'}>
                {skill.enabled ? t('skills.enabled') : t('skills.disabled')}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label={t('skills.toolName')} span={2}>
              <code>{skill.tool_name}</code>
            </Descriptions.Item>
          </Descriptions>

          <Text strong style={{ display: 'block', marginBottom: 8 }}>
            {t('skills.instruction')}
          </Text>
          <Paragraph style={{ background: '#f8fafc', padding: 12, borderRadius: 8, fontSize: 13, lineHeight: 1.7 }}>
            {detail.instruction}
          </Paragraph>

          <Text strong style={{ display: 'block', marginBottom: 8, marginTop: 16 }}>
            {t('skills.inputSchema')}
          </Text>
          <pre
            style={{
              background: '#1e293b',
              color: '#e2e8f0',
              padding: 12,
              borderRadius: 8,
              fontSize: 12,
              overflow: 'auto',
              maxHeight: 200,
            }}
          >
            {formatJsonSchema(
              (BUILT_IN_SKILL_KEYS[skill.id]
                ? localizeSchemaDescriptions(skill.input_schema, t)
                : skill.input_schema) as Record<string, unknown>,
            )}
          </pre>

          <Text strong style={{ display: 'block', marginBottom: 8, marginTop: 16 }}>
            {t('skills.outputSchema')}
          </Text>
          <pre
            style={{
              background: '#1e293b',
              color: '#e2e8f0',
              padding: 12,
              borderRadius: 8,
              fontSize: 12,
              overflow: 'auto',
              maxHeight: 200,
            }}
          >
            {formatJsonSchema(skill.output_schema)}
          </pre>

          <Text strong style={{ display: 'block', marginBottom: 8, marginTop: 16 }}>
            {t('skills.capability')}
          </Text>
          <pre
            style={{
              background: '#f8fafc',
              padding: 12,
              borderRadius: 8,
              fontSize: 12,
              overflow: 'auto',
              maxHeight: 150,
            }}
          >
            {formatJsonSchema(skill.capability || {})}
          </pre>
        </div>
      )}
    </Modal>
  );
}
