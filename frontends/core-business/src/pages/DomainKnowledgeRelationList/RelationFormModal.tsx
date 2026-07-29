import React, { useState, useCallback, forwardRef, useImperativeHandle } from 'react';
import { useTranslation } from 'react-i18next';
import { message, Modal, Select } from 'antd';
import { createOntologyRelation, updateOntologyRelation, searchOntologyInstances } from '@/api/domainKnowledge';
import type { RelationInstanceRow } from '@/types/domainKnowledge';

const ENTITY_SEP = '|';

export interface RelationFormModalHandle {
  openCreate: () => void;
  openEdit: (row: RelationInstanceRow) => void;
}

interface RelationFormModalProps {
  id: string;
  typeNameMap: Record<string, string>;
  relTypeOptions: Array<{ value: string; label: string }>;
  onSaved: () => void;
}

const RelationFormModal = forwardRef<RelationFormModalHandle, RelationFormModalProps>(function RelationFormModal(
  { id, typeNameMap, relTypeOptions, onSaved },
  ref,
) {
  const { t } = useTranslation();

  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [saving, setSaving] = useState(false);

  const [formSourceType, setFormSourceType] = useState('');
  const [formSourceName, setFormSourceName] = useState('');
  const [formRelType, setFormRelType] = useState('');
  const [formTargetType, setFormTargetType] = useState('');
  const [formTargetName, setFormTargetName] = useState('');

  const [sourceOptions, setSourceOptions] = useState<Array<{ value: string; label: string }>>([]);
  const [targetOptions, setTargetOptions] = useState<Array<{ value: string; label: string }>>([]);

  const [editIdentity, setEditIdentity] = useState<{
    sourceType: string;
    sourceName: string;
    relType: string;
    targetType: string;
    targetName: string;
  } | null>(null);

  // ── 暴露给父组件的方法 ──
  useImperativeHandle(
    ref,
    () => ({
      openCreate: () => {
        setModalMode('create');
        setFormSourceType('');
        setFormSourceName('');
        setSourceOptions([]);
        setFormRelType('');
        setFormTargetType('');
        setFormTargetName('');
        setTargetOptions([]);
        setEditIdentity(null);
        setModalOpen(true);
      },
      openEdit: (row: RelationInstanceRow) => {
        setModalMode('edit');
        setFormSourceType(row.source_type);
        setFormSourceName(row.source);
        setFormRelType(row.relation_type);
        setFormTargetType(row.target_type);
        setFormTargetName(row.target);

        setSourceOptions([
          {
            value: `${row.source_type}${ENTITY_SEP}${row.source}`,
            label: `${row.source} (${row.source_type})`,
          },
        ]);
        setTargetOptions([
          {
            value: `${row.target_type}${ENTITY_SEP}${row.target}`,
            label: `${row.target} (${row.target_type})`,
          },
        ]);

        setEditIdentity({
          sourceType: row.source_type,
          sourceName: row.source,
          relType: row.relation_type,
          targetType: row.target_type,
          targetName: row.target,
        });
        setModalOpen(true);
      },
    }),
    [],
  );

  // ── 实体搜索 ──
  const searchEntities = useCallback(
    async (kw: string, setter: (opts: Array<{ value: string; label: string }>) => void) => {
      if (!id || !kw.trim()) return;
      try {
        const res = await searchOntologyInstances(id, kw.trim(), 20);
        const opts = (res.items || []).map((item: any) => ({
          value: `${item.entity_type || item.type || ''}${ENTITY_SEP}${item.canonical_name || item.name}`,
          label: `${item.canonical_name || item.name} (${item.entity_type || item.type})`,
        }));
        setter(opts);
      } catch {
        /* silent */
      }
    },
    [id],
  );

  const [debounceTimer, setDebounceTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  const debouncedSourceSearch = useCallback(
    (kw: string) => {
      if (debounceTimer) clearTimeout(debounceTimer);
      const timer = setTimeout(() => searchEntities(kw, setSourceOptions), 300);
      setDebounceTimer(timer);
    },
    [searchEntities, debounceTimer],
  );

  const debouncedTargetSearch = useCallback(
    (kw: string) => {
      if (debounceTimer) clearTimeout(debounceTimer);
      const timer = setTimeout(() => searchEntities(kw, setTargetOptions), 300);
      setDebounceTimer(timer);
    },
    [searchEntities, debounceTimer],
  );

  // ── Select 选择 ──
  const handleSourceSelect = useCallback((value: string) => {
    const [type, ...rest] = value.split(ENTITY_SEP);
    const name = rest.join(ENTITY_SEP);
    setFormSourceType(type);
    setFormSourceName(name);
    setSourceOptions((prev) => {
      if (prev.some((o) => o.value === value)) return prev;
      return [{ value, label: `${name} (${type})` }, ...prev];
    });
  }, []);

  const handleTargetSelect = useCallback((value: string) => {
    const [type, ...rest] = value.split(ENTITY_SEP);
    const name = rest.join(ENTITY_SEP);
    setFormTargetType(type);
    setFormTargetName(name);
    setTargetOptions((prev) => {
      if (prev.some((o) => o.value === value)) return prev;
      return [{ value, label: `${name} (${type})` }, ...prev];
    });
  }, []);

  // ── 保存 ──
  const handleSave = useCallback(async () => {
    if (!formSourceName.trim() || !formRelType || !formTargetName.trim()) return;

    setSaving(true);
    try {
      if (modalMode === 'create') {
        await createOntologyRelation(
          id,
          formSourceType,
          formSourceName.trim(),
          formRelType,
          formTargetType,
          formTargetName.trim(),
        );
      } else if (editIdentity) {
        await updateOntologyRelation(
          id,
          editIdentity.sourceType,
          editIdentity.sourceName,
          editIdentity.relType,
          editIdentity.targetType,
          editIdentity.targetName,
          { relation_type: formRelType },
        );
      }
      setModalOpen(false);
      onSaved();
    } catch (err: any) {
      message.error(err?.message || t('common.saveFailed'));
    } finally {
      setSaving(false);
    }
  }, [
    id,
    formSourceType,
    formSourceName,
    formRelType,
    formTargetType,
    formTargetName,
    modalMode,
    editIdentity,
    onSaved,
    t,
  ]);

  return (
    <Modal
      title={
        <span style={{ fontSize: 18, fontWeight: 700, color: '#0b2b5c' }}>
          {modalMode === 'create' ? t('domainKnowledge.newRelation') : t('compile.relation.editBtn')}
        </span>
      }
      open={modalOpen}
      onCancel={() => setModalOpen(false)}
      width={600}
      centered
      confirmLoading={saving}
      okText={t('common.save')}
      cancelText={t('common.cancel')}
      onOk={handleSave}
      destroyOnClose
    >
      {/* 源实体 */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: '#0b2b5c', marginBottom: 8 }}>
          {t('compile.relation.sourceObject')} <span style={{ color: '#ef4444' }}>*</span>
        </div>
        {modalMode === 'edit' ? (
          <div
            style={{
              padding: '6px 12px',
              background: '#f8fafc',
              borderRadius: 6,
              border: '1px solid #e2e8f0',
              color: '#64748b',
              fontSize: 13,
            }}
          >
            {formSourceName} ({typeNameMap[formSourceType] || formSourceType})
          </div>
        ) : (
          <Select
            value={formSourceName ? `${formSourceType}${ENTITY_SEP}${formSourceName}` : undefined}
            onSearch={debouncedSourceSearch}
            onChange={handleSourceSelect}
            options={sourceOptions}
            placeholder={t('compile.relation.sourceEntityPlaceholder')}
            style={{ width: '100%' }}
            size="middle"
            showSearch
            filterOption={false}
            notFoundContent={null}
          />
        )}
      </div>

      {/* 关系类型 */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: '#0b2b5c', marginBottom: 8 }}>
          {t('compile.relation.name')} <span style={{ color: '#ef4444' }}>*</span>
        </div>
        <Select
          value={formRelType || undefined}
          onChange={setFormRelType}
          options={relTypeOptions}
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
        {modalMode === 'edit' ? (
          <div
            style={{
              padding: '6px 12px',
              background: '#f8fafc',
              borderRadius: 6,
              border: '1px solid #e2e8f0',
              color: '#64748b',
              fontSize: 13,
            }}
          >
            {formTargetName} ({typeNameMap[formTargetType] || formTargetType})
          </div>
        ) : (
          <Select
            value={formTargetName ? `${formTargetType}${ENTITY_SEP}${formTargetName}` : undefined}
            onSearch={debouncedTargetSearch}
            onChange={handleTargetSelect}
            options={targetOptions}
            placeholder={t('compile.relation.targetEntityPlaceholder')}
            style={{ width: '100%' }}
            size="middle"
            showSearch
            filterOption={false}
            notFoundContent={null}
          />
        )}
      </div>
    </Modal>
  );
});

export default RelationFormModal;
