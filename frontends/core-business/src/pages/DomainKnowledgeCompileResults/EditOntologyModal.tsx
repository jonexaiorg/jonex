import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal, Button, Input, Select, message } from 'antd';
import { SaveOutlined, PlusOutlined, CloseOutlined } from '@ant-design/icons';

interface EditOntologyModalProps {
  open: boolean;
  mode?: 'create' | 'edit';
  /** 编辑模式时传入实例数据 */
  record: {
    name: string;
    type: string;
    aliases?: string[];
    description?: string;
    attributes?: Record<string, unknown> | null;
  } | null;
  ontologyOptions: Array<{ value: string; label: string }>;
  onSave: (data: {
    name: string;
    type: string;
    aliases?: string[];
    description?: string;
    attributes?: Record<string, unknown>;
  }) => void;
  onCancel: () => void;
}

export default function EditOntologyModal({
  open,
  mode = 'edit',
  record,
  ontologyOptions,
  onSave,
  onCancel,
}: EditOntologyModalProps) {
  const { t } = useTranslation();
  const isCreate = mode === 'create';

  const [entityType, setEntityType] = useState('');
  const [name, setName] = useState('');
  const [aliases, setAliases] = useState<string[]>([]);
  const [aliasInput, setAliasInput] = useState('');
  const [desc, setDesc] = useState('');
  const [attributes, setAttributes] = useState<Record<string, string>>({});
  const [attrKey, setAttrKey] = useState('');
  const [attrValue, setAttrValue] = useState('');

  useEffect(() => {
    if (open) {
      if (isCreate) {
        setEntityType('');
        setName('');
        setAliases([]);
        setDesc('');
        setAttributes({});
      } else if (record) {
        setEntityType(record.type);
        setName(record.name);
        setAliases(record.aliases ?? []);
        setDesc(record.description ?? '');
        setAttributes(
          record.attributes
            ? Object.fromEntries(
                Object.entries(record.attributes).map(([k, v]) => [k, typeof v === 'string' ? v : JSON.stringify(v)]),
              )
            : {},
        );
      }
      setAliasInput('');
      setAttrKey('');
      setAttrValue('');
    }
  }, [open, record, isCreate]);

  const resetForm = () => {
    setEntityType('');
    setName('');
    setAliases([]);
    setAliasInput('');
    setDesc('');
    setAttributes({});
    setAttrKey('');
    setAttrValue('');
  };

  const handleSave = () => {
    if (!name.trim()) {
      message.warning(t('common.nameRequired'));
      return;
    }
    if (!entityType) {
      message.warning(t('common.required'));
      return;
    }

    const payload = {
      name: name.trim(),
      type: entityType,
      aliases: aliases.length > 0 ? aliases : undefined,
      description: desc.trim() || undefined,
      attributes:
        Object.keys(attributes).length > 0
          ? Object.fromEntries(Object.entries(attributes).filter(([, v]) => v !== ''))
          : undefined,
    };

    onSave(payload);
    resetForm();
  };

  const handleCancel = () => {
    resetForm();
    onCancel();
  };

  const addAlias = () => {
    const val = aliasInput.trim();
    if (val && !aliases.includes(val)) {
      setAliases([...aliases, val]);
    }
    setAliasInput('');
  };

  const removeAlias = (alias: string) => {
    setAliases(aliases.filter((a) => a !== alias));
  };

  const addAttributeItem = () => {
    const key = attrKey.trim();
    if (key && !(key in attributes)) {
      setAttributes({ ...attributes, [key]: attrValue });
    }
    setAttrKey('');
    setAttrValue('');
  };

  const removeAttributeItem = (key: string) => {
    const next = { ...attributes };
    delete next[key];
    setAttributes(next);
  };

  return (
    <Modal
      title={
        <span style={{ fontSize: 18, fontWeight: 700, color: '#0b2b5c' }}>
          {isCreate ? t('compile.createInstance') : t('compile.editInstance', { name: record?.name || '' })}
        </span>
      }
      open={open}
      onCancel={handleCancel}
      width={560}
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
      {/* 实体类型 */}
      <div style={{ marginBottom: 16 }}>
        <div
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: '#0b2b5c',
            marginBottom: 8,
          }}
        >
          {t('domainKnowledge.entityType')} <span style={{ color: '#ef4444' }}>*</span>
        </div>
        <Select
          value={entityType || undefined}
          onChange={setEntityType}
          options={ontologyOptions}
          placeholder={t('compile.ontologyDefPlaceholder')}
          style={{ width: '100%' }}
          size="middle"
        />
      </div>

      {/* 实例名称 */}
      <div style={{ marginBottom: 16 }}>
        <div
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: '#0b2b5c',
            marginBottom: 8,
          }}
        >
          {t('compile.instanceName')} <span style={{ color: '#ef4444' }}>*</span>
        </div>
        <Input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={t('compile.instanceNamePlaceholder')}
          size="middle"
        />
      </div>

      {/* 别名 */}
      <div style={{ marginBottom: 16 }}>
        <div
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: '#0b2b5c',
            marginBottom: 8,
          }}
        >
          {t('domainKnowledge.alias')}
        </div>
        <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
          <Input
            placeholder={t('compile.aliasPlaceholder')}
            value={aliasInput}
            onChange={(e) => setAliasInput(e.target.value)}
            onPressEnter={(e) => {
              e.preventDefault();
              addAlias();
            }}
            style={{ flex: 1 }}
            size="middle"
          />
          <Button onClick={addAlias}>{t('common.add')}</Button>
        </div>
        {aliases.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {aliases.map((alias) => (
              <span
                key={alias}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 4,
                  padding: '2px 8px',
                  borderRadius: 6,
                  background: '#eff6ff',
                  color: '#3b82f6',
                  fontSize: 12,
                }}
              >
                {alias}
                <CloseOutlined style={{ fontSize: 10, cursor: 'pointer' }} onClick={() => removeAlias(alias)} />
              </span>
            ))}
          </div>
        )}
      </div>

      {/* 描述 */}
      <div style={{ marginBottom: 16 }}>
        <div
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: '#0b2b5c',
            marginBottom: 8,
          }}
        >
          {t('common.description')}
        </div>
        <Input.TextArea
          rows={2}
          placeholder={t('compile.createInstanceDescPlaceholder')}
          value={desc}
          onChange={(e) => setDesc(e.target.value)}
        />
      </div>

      {/* 自定义属性 */}
      <div>
        <div
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: '#0b2b5c',
            marginBottom: 8,
          }}
        >
          {t('compile.customAttributes')}
        </div>
        <div
          style={{
            background: '#f8fafc',
            borderRadius: 12,
            padding: 16,
            border: '1px solid #eef2f6',
          }}
        >
          <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
            <Input
              placeholder={t('compile.attrKeyPlaceholder')}
              value={attrKey}
              onChange={(e) => setAttrKey(e.target.value)}
              style={{ width: 160 }}
              size="middle"
            />
            <Input
              placeholder={t('compile.attrValuePlaceholder')}
              value={attrValue}
              onChange={(e) => setAttrValue(e.target.value)}
              onPressEnter={(e) => {
                e.preventDefault();
                addAttributeItem();
              }}
              style={{ flex: 1 }}
              size="middle"
            />
            <Button onClick={addAttributeItem}>{t('common.add')}</Button>
          </div>
          {Object.keys(attributes).length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {Object.entries(attributes).map(([k, v]) => (
                <div
                  key={k}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '4px 10px',
                    borderRadius: 6,
                    background: '#fff',
                    border: '1px solid #e2e8f0',
                    fontSize: 13,
                  }}
                >
                  <span style={{ fontWeight: 500, color: '#0b2b5c' }}>{k}</span>
                  <span
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                    }}
                  >
                    <span style={{ color: '#64748b' }}>{v}</span>
                    <CloseOutlined
                      style={{
                        fontSize: 10,
                        cursor: 'pointer',
                        color: '#94a3b8',
                      }}
                      onClick={() => removeAttributeItem(k)}
                    />
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
}
