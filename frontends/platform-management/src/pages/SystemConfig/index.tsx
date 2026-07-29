import React, { useState, useEffect, useCallback } from 'react';
import { Input, Select, Switch, Button, message, Card, Spin, Result } from 'antd';
import {
  SaveOutlined,
  UndoOutlined,
  InfoCircleOutlined,
  SafetyOutlined,
  HddOutlined,
  MailOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { listSystemConfigs, updateSystemConfig, type SystemConfigItem } from '../../api/systemConfig';

interface ConfigMap {
  [key: string]: string;
}

const DEFAULTS: ConfigMap = {
  platform_name: 'Jonex',
  logo_url: '/assets/logo.png',
  default_language: 'zh',
  timezone: 'shanghai',
  session_timeout: '30',
  password_min_length: '8',
  login_lock_threshold: '5',
  lock_duration: '15',
  two_factor: 'false',
  storage_path: '/data/jonex/storage',
  backup_path: '/data/jonex/backup',
  storage_limit: '500',
  storage_used: '127',
  auto_backup: 'true',
  smtp_server: 'smtp.example.com',
  smtp_port: '587',
  sender_email: 'noreply@jonex.ai',
  admin_email: 'admin@jonex.ai',
  webhook_url: 'https://hooks.example.com/jonex/notify',
};

export default function SystemConfig() {
  const { t } = useTranslation();
  const [configs, setConfigs] = useState<ConfigMap>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [changed, setChanged] = useState<Set<string>>(new Set());
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await listSystemConfigs();
      const map: ConfigMap = {};
      r.items.forEach((c) => {
        map[c.config_key] = c.config_value || '';
      });
      setConfigs({ ...DEFAULTS, ...map });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : t('common.loadFailed'));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    load();
  }, [load]);

  const get = (key: string) => configs[key] || DEFAULTS[key] || '';
  const set = (key: string, value: string) => {
    setConfigs((p) => ({ ...p, [key]: value }));
    setChanged((p) => new Set(p).add(key));
  };

  const getBool = (key: string) => get(key) === 'true';
  const setBool = (key: string, v: boolean) => set(key, v ? 'true' : 'false');

  const handleSave = async () => {
    if (changed.size === 0) {
      message.info(t('systemConfig.noChanges'));
      return;
    }
    setSaving(true);
    let done = 0;
    let fail = 0;
    for (const key of changed) {
      try {
        await updateSystemConfig(key, get(key));
        done++;
      } catch {
        fail++;
      }
    }
    setSaving(false);
    if (fail === 0) {
      message.success(t('systemConfig.changesSaved', { count: done }));
      setChanged(new Set());
    } else {
      message.warning(t('systemConfig.changesSavedWithFail', { done, fail }));
    }
  };

  const handleReset = () => {
    setConfigs({ ...DEFAULTS });
    setChanged(new Set(Object.keys(DEFAULTS)));
    message.info(t('systemConfig.resetToDefaultMsg'));
  };

  if (loading)
    return (
      <div style={{ display: 'flex', justifyContent: 'center', minHeight: 300, alignItems: 'center' }}>
        <Spin size="large" />
      </div>
    );
  if (error)
    return (
      <Result
        status="error"
        title={t('common.loadFailed')}
        subTitle={error}
        extra={
          <Button type="primary" onClick={load}>
            {t('common.retry')}
          </Button>
        }
      />
    );

  const changedStyle = { borderColor: '#f59e0b', boxShadow: '0 0 0 2px rgba(245,158,11,0.15)' };

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('systemConfig.title')}</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 14 }}>{t('systemConfig.description')}</p>
      </div>

      <Card
        style={{ borderRadius: 12, border: '1px solid #e2e8f0', marginBottom: 20 }}
        styles={{ body: { padding: 24 } }}
      >
        <h3
          style={{
            margin: '0 0 16px',
            fontSize: 16,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            paddingBottom: 12,
            borderBottom: '1px solid #e2e8f0',
          }}
        >
          <InfoCircleOutlined style={{ color: '#3b82f6' }} /> {t('systemConfig.basicSettings')}
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="yx-form-row">
            <label>{t('systemConfig.platformName')}</label>
            <Input
              value={get('platform_name')}
              onChange={(e) => set('platform_name', e.target.value)}
              style={changed.has('platform_name') ? changedStyle : undefined}
            />
          </div>
          <div className="yx-form-row">
            <label>{t('systemConfig.logoUrl')}</label>
            <Input
              value={get('logo_url')}
              onChange={(e) => set('logo_url', e.target.value)}
              style={changed.has('logo_url') ? changedStyle : undefined}
            />
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 14 }}>
          <div className="yx-form-row">
            <label>{t('systemConfig.defaultLanguage')}</label>
            <Select
              value={get('default_language')}
              onChange={(v) => set('default_language', v)}
              style={{ width: '100%', ...(changed.has('default_language') ? changedStyle : {}) }}
              options={[
                { value: 'zh', label: t('systemConfig.chinese') },
                { value: 'en', label: t('systemConfig.english') },
              ]}
            />
          </div>
          <div className="yx-form-row">
            <label>{t('systemConfig.timezone')}</label>
            <Select
              value={get('timezone')}
              onChange={(v) => set('timezone', v)}
              style={{ width: '100%', ...(changed.has('timezone') ? changedStyle : {}) }}
              options={[
                { value: 'shanghai', label: 'Asia/Shanghai (UTC+8)' },
                { value: 'utc', label: 'UTC' },
              ]}
            />
          </div>
        </div>
      </Card>

      <Card
        style={{ borderRadius: 12, border: '1px solid #e2e8f0', marginBottom: 20 }}
        styles={{ body: { padding: 24 } }}
      >
        <h3
          style={{
            margin: '0 0 16px',
            fontSize: 16,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            paddingBottom: 12,
            borderBottom: '1px solid #e2e8f0',
          }}
        >
          <SafetyOutlined style={{ color: '#3b82f6' }} /> {t('systemConfig.securitySettings')}
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="yx-form-row">
            <label>{t('systemConfig.sessionTimeout')}</label>
            <Input
              value={get('session_timeout')}
              onChange={(e) => set('session_timeout', e.target.value)}
              style={changed.has('session_timeout') ? changedStyle : undefined}
            />
          </div>
          <div className="yx-form-row">
            <label>{t('systemConfig.passwordMinLength')}</label>
            <Input
              value={get('password_min_length')}
              onChange={(e) => set('password_min_length', e.target.value)}
              style={changed.has('password_min_length') ? changedStyle : undefined}
            />
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 14 }}>
          <div className="yx-form-row">
            <label>{t('systemConfig.loginLockThreshold')}</label>
            <Select
              value={get('login_lock_threshold')}
              onChange={(v) => set('login_lock_threshold', v)}
              style={{ width: '100%', ...(changed.has('login_lock_threshold') ? changedStyle : {}) }}
              options={[
                { value: '5', label: t('systemConfig.lockAfter5') },
                { value: '3', label: t('systemConfig.lockAfter3') },
                { value: '0', label: t('systemConfig.noLock') },
              ]}
            />
          </div>
          <div className="yx-form-row">
            <label>{t('systemConfig.lockDuration')}</label>
            <Input
              value={get('lock_duration')}
              onChange={(e) => set('lock_duration', e.target.value)}
              style={changed.has('lock_duration') ? changedStyle : undefined}
            />
          </div>
        </div>
        <div style={{ marginTop: 14 }}>
          <Switch checked={getBool('two_factor')} onChange={(v) => setBool('two_factor', v)} />{' '}
          <span style={{ marginLeft: 8 }}>{t('systemConfig.twoFactorAuth')}</span>
        </div>
      </Card>

      <Card
        style={{ borderRadius: 12, border: '1px solid #e2e8f0', marginBottom: 20 }}
        styles={{ body: { padding: 24 } }}
      >
        <h3
          style={{
            margin: '0 0 16px',
            fontSize: 16,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            paddingBottom: 12,
            borderBottom: '1px solid #e2e8f0',
          }}
        >
          <HddOutlined style={{ color: '#3b82f6' }} /> {t('systemConfig.storageSettings')}
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="yx-form-row">
            <label>{t('systemConfig.storagePath')}</label>
            <Input
              value={get('storage_path')}
              onChange={(e) => set('storage_path', e.target.value)}
              style={changed.has('storage_path') ? changedStyle : undefined}
            />
          </div>
          <div className="yx-form-row">
            <label>{t('systemConfig.backupPath')}</label>
            <Input
              value={get('backup_path')}
              onChange={(e) => set('backup_path', e.target.value)}
              style={changed.has('backup_path') ? changedStyle : undefined}
            />
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 14 }}>
          <div className="yx-form-row">
            <label>{t('systemConfig.storageLimit')}</label>
            <Input
              value={get('storage_limit')}
              onChange={(e) => set('storage_limit', e.target.value)}
              style={changed.has('storage_limit') ? changedStyle : undefined}
            />
          </div>
          <div className="yx-form-row">
            <label>{t('systemConfig.storageUsed')}</label>
            <Input value={get('storage_used') + ' GB (25.4%)'} disabled />
          </div>
        </div>
        <div style={{ marginTop: 14 }}>
          <Switch checked={getBool('auto_backup')} onChange={(v) => setBool('auto_backup', v)} />{' '}
          <span style={{ marginLeft: 8 }}>{t('systemConfig.autoBackup')}</span>
        </div>
      </Card>

      <Card
        style={{ borderRadius: 12, border: '1px solid #e2e8f0', marginBottom: 20 }}
        styles={{ body: { padding: 24 } }}
      >
        <h3
          style={{
            margin: '0 0 16px',
            fontSize: 16,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            paddingBottom: 12,
            borderBottom: '1px solid #e2e8f0',
          }}
        >
          <MailOutlined style={{ color: '#3b82f6' }} /> {t('systemConfig.notificationSettings')}
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="yx-form-row">
            <label>{t('systemConfig.smtpServer')}</label>
            <Input
              value={get('smtp_server')}
              onChange={(e) => set('smtp_server', e.target.value)}
              style={changed.has('smtp_server') ? changedStyle : undefined}
            />
          </div>
          <div className="yx-form-row">
            <label>{t('systemConfig.smtpPort')}</label>
            <Input
              value={get('smtp_port')}
              onChange={(e) => set('smtp_port', e.target.value)}
              style={changed.has('smtp_port') ? changedStyle : undefined}
            />
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 14 }}>
          <div className="yx-form-row">
            <label>{t('systemConfig.senderEmail')}</label>
            <Input
              value={get('sender_email')}
              onChange={(e) => set('sender_email', e.target.value)}
              style={changed.has('sender_email') ? changedStyle : undefined}
            />
          </div>
          <div className="yx-form-row">
            <label>{t('systemConfig.adminEmail')}</label>
            <Input
              value={get('admin_email')}
              onChange={(e) => set('admin_email', e.target.value)}
              style={changed.has('admin_email') ? changedStyle : undefined}
            />
          </div>
        </div>
        <div className="yx-form-row" style={{ marginTop: 14 }}>
          <label>{t('systemConfig.webhookUrl')}</label>
          <Input
            value={get('webhook_url')}
            onChange={(e) => set('webhook_url', e.target.value)}
            style={changed.has('webhook_url') ? changedStyle : undefined}
          />
        </div>
      </Card>

      <div style={{ display: 'flex', gap: 12 }}>
        <Button type="primary" icon={<SaveOutlined />} loading={saving} onClick={handleSave}>
          {t('systemConfig.saveAll')}
        </Button>
        <Button icon={<UndoOutlined />} onClick={handleReset}>
          {t('systemConfig.resetToDefault')}
        </Button>
        {changed.size > 0 && (
          <span style={{ color: '#f59e0b', fontSize: 13, alignSelf: 'center' }}>
            {t('systemConfig.changedItems', { count: changed.size })}
          </span>
        )}
      </div>
    </div>
  );
}
