import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal, Button, Input, Select, message } from 'antd';
import { SaveOutlined, CloseOutlined } from '@ant-design/icons';
import debounce from 'lodash/debounce';
import { searchOntologyInstances } from '@/api/domainKnowledge';

const ENTITY_SEP = '|';

interface EditRelationModalProps {
  open: boolean;
  mode: 'create' | 'edit';
  kbId: string;
  /** 关系类型选项 */
  relationTypeOptions: Array<{ value: string; label: string }>;
  /** 编辑模式时传入初始数据 */
  initialData?: {
    sourceType: string;
    sourceName: string;
    relationType: string;
    targetType: string;
    targetName: string;
  } | null;
  onSave: (data: {
    sourceType: string;
    sourceName: string;
    relationType: string;
    targetType: string;
    targetName: string;
  }) => void;
  onCancel: () => void;
}

export default function EditRelationModal({
  open,
  mode,
  kbId,
  relationTypeOptions,
  initialData,
  onSave,
  onCancel,
}: EditRelationModalProps) {
  const { t } = useTranslation();
  const isCreate = mode === 'create';

  const [sourceType, setSourceType] = useState('');
  const [sourceName, setSourceName] = useState('');
  const [sourceOptions, setSourceOptions] = useState<Array<{ value: string; label: string }>>([]);
  const [relType, setRelType] = useState('');
  const [targetType, setTargetType] = useState('');
  const [targetName, setTargetName] = useState('');
  const [targetOptions, setTargetOptions] = useState<Array<{ value: string; label: string }>>([]);

  useEffect(() => {
    if (open) {
      if (isCreate) {
        setSourceType('');
        setSourceName('');
        setSourceOptions([]);
        setRelType('');
        setTargetType('');
        setTargetName('');
        setTargetOptions([]);
      } else if (initialData) {
        setSourceType(initialData.sourceType);
        setSourceName(initialData.sourceName);
        setSourceOptions(
          initialData.sourceName
            ? [
                {
                  value: `${initialData.sourceType}${ENTITY_SEP}${initialData.sourceName}`,
                  label: `${initialData.sourceName} (${initialData.sourceType})`,
                },
              ]
            : [],
        );
        setRelType(initialData.relationType);
        setTargetType(initialData.targetType);
        setTargetName(initialData.targetName);
        setTargetOptions(
          initialData.targetName
            ? [
                {
                  value: `${initialData.targetType}${ENTITY_SEP}${initialData.targetName}`,
                  label: `${initialData.targetName} (${initialData.targetType})`,
                },
              ]
            : [],
        );
      }
      // 打开时预取实体列表
      searchOntologyInstances(kbId, '', 20)
        .then((res) => {
          const opts = buildEntityOptions(res.items || []);
          setSourceOptions((prev) => {
            // 保留已选中的项（创建模式 prev 为空，直接覆盖）
            if (isCreate) return opts;
            const merged = [...prev];
            opts.forEach((o) => {
              if (!merged.some((m) => m.value === o.value)) merged.push(o);
            });
            return merged;
          });
          setTargetOptions((prev) => {
            if (isCreate) return opts;
            const merged = [...prev];
            opts.forEach((o) => {
              if (!merged.some((m) => m.value === o.value)) merged.push(o);
            });
            return merged;
          });
        })
        .catch(() => {});
    }
  }, [open, initialData, isCreate, kbId]);

  const buildEntityOptions = (items: any[]) =>
    items.map((item: any) => ({
      value: `${item.entity_type || item.type || ''}${ENTITY_SEP}${item.canonical_name || item.name}`,
      label: `${item.canonical_name || item.name} (${item.entity_type || item.type})`,
    }));

  const debouncedSourceSearch = debounce(async (kw: string) => {
    if (!kw.trim()) return;
    try {
      const res = await searchOntologyInstances(kbId, kw.trim(), 20);
      setSourceOptions(buildEntityOptions(res.items || []));
    } catch {
      /* silent */
    }
  }, 300);

  const debouncedTargetSearch = debounce(async (kw: string) => {
    if (!kw.trim()) return;
    try {
      const res = await searchOntologyInstances(kbId, kw.trim(), 20);
      setTargetOptions(buildEntityOptions(res.items || []));
    } catch {
      /* silent */
    }
  }, 300);

  const resetForm = () => {
    setSourceType('');
    setSourceName('');
    setSourceOptions([]);
    setRelType('');
    setTargetType('');
    setTargetName('');
    setTargetOptions([]);
  };

  const handleSave = () => {
    if (!sourceName.trim()) {
      message.warning(t('common.required'));
      return;
    }
    if (!relType) {
      message.warning(t('common.required'));
      return;
    }
    if (!targetName.trim()) {
      message.warning(t('common.required'));
      return;
    }

    onSave({
      sourceType,
      sourceName: sourceName.trim(),
      relationType: relType,
      targetType,
      targetName: targetName.trim(),
    });
    resetForm();
  };

  const handleCancel = () => {
    resetForm();
    onCancel();
  };

  const handleSourceSelect = (value: string) => {
    const [type, ...rest] = value.split(ENTITY_SEP);
    const name = rest.join(ENTITY_SEP);
    setSourceType(type);
    setSourceName(name);
    // 保留选中项到 options，确保 Select 能显示 label 而非 raw value
    setSourceOptions((prev) => {
      if (prev.some((o) => o.value === value)) return prev;
      const label = `${name} (${type})`;
      return [{ value, label }, ...prev];
    });
  };

  const handleTargetSelect = (value: string) => {
    const [type, ...rest] = value.split(ENTITY_SEP);
    const name = rest.join(ENTITY_SEP);
    setTargetType(type);
    setTargetName(name);
    setTargetOptions((prev) => {
      if (prev.some((o) => o.value === value)) return prev;
      const label = `${name} (${type})`;
      return [{ value, label }, ...prev];
    });
  };

  return (
    <Modal
      title={
        <span style={{ fontSize: 18, fontWeight: 700, color: '#0b2b5c' }}>
          {isCreate ? t('compile.relation.createBtn') : t('compile.relation.editBtn')}
        </span>
      }
      open={open}
      onCancel={handleCancel}
      width={600}
      centered
      footer={
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
          <Button size="middle" onClick={handleCancel}>
            {t('common.cancel')}
          </Button>
          <Button type="primary" size="middle" icon={<SaveOutlined />} onClick={handleSave}>
            {t('common.save')}
          </Button>
        </div>
      }
      styles={{ body: { padding: '24px 24px 12px' } }}
      closeIcon={<CloseOutlined style={{ color: '#64748b' }} />}
    >
      {/* 源实体 */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: '#0b2b5c', marginBottom: 8 }}>
          {t('compile.relation.sourceObject')} <span style={{ color: '#ef4444' }}>*</span>
        </div>
        <Select
          value={sourceName ? `${sourceType}${ENTITY_SEP}${sourceName}` : undefined}
          onSearch={(kw) => {
            debouncedSourceSearch(kw);
          }}
          onChange={handleSourceSelect}
          options={sourceOptions}
          placeholder={t('compile.relation.sourceEntityPlaceholder')}
          style={{ width: '100%' }}
          size="middle"
          showSearch
          filterOption={false}
          notFoundContent={undefined}
        />
      </div>

      {/* 关系类型 */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: '#0b2b5c', marginBottom: 8 }}>
          {t('compile.relation.name')} <span style={{ color: '#ef4444' }}>*</span>
        </div>
        <Select
          value={relType || undefined}
          onChange={setRelType}
          options={relationTypeOptions}
          placeholder={t('compile.relation.namePlaceholder')}
          style={{ width: '100%' }}
          size="middle"
        />
      </div>

      {/* 目标实体 */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: '#0b2b5c', marginBottom: 8 }}>
          {t('compile.relation.targetObject')} <span style={{ color: '#ef4444' }}>*</span>
        </div>
        <Select
          value={targetName ? `${targetType}${ENTITY_SEP}${targetName}` : undefined}
          onSearch={(kw) => {
            debouncedTargetSearch(kw);
          }}
          onChange={handleTargetSelect}
          options={targetOptions}
          placeholder={t('compile.relation.targetEntityPlaceholder')}
          style={{ width: '100%' }}
          size="middle"
          showSearch
          filterOption={false}
          notFoundContent={undefined}
        />
      </div>
    </Modal>
  );
}
