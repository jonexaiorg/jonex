import React, { useState, useEffect, useCallback } from 'react'
import { Input, Select, Switch, Button, message, Card, Spin, Result } from 'antd'
import { useTranslation } from 'react-i18next'
import { SaveOutlined, UndoOutlined, InfoCircleOutlined, SafetyOutlined, HddOutlined, MailOutlined } from '@ant-design/icons'
import { listSystemConfigs, updateSystemConfig, type SystemConfigItem } from '../../api/systemConfig'

interface ConfigMap { [key: string]: string }

const DEFAULTS: ConfigMap = {
  platform_name: 'Jonex Knowledge Platform', logo_url: '/assets/logo.png',
  default_language: 'en', timezone: 'shanghai',
  session_timeout: '30', password_min_length: '8',
  login_lock_threshold: '5', lock_duration: '15',
  two_factor: 'false',
  storage_path: '/data/jonex/storage', backup_path: '/data/jonex/backup',
  storage_limit: '500', storage_used: '127',
  auto_backup: 'true',
  smtp_server: 'smtp.example.com', smtp_port: '587',
  sender_email: 'noreply@jonex.com', admin_email: 'admin@jonex.com',
  webhook_url: 'https://hooks.example.com/jonex/notify',
}

export default function SystemConfig() {
  const { t } = useTranslation()
  const [configs, setConfigs] = useState<ConfigMap>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [changed, setChanged] = useState<Set<string>>(new Set())
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const r = await listSystemConfigs()
      const map: ConfigMap = {}
      r.items.forEach(c => { map[c.config_key] = c.config_value || '' })
      setConfigs({ ...DEFAULTS, ...map })
    } catch (e: unknown) { setError(e instanceof Error ? e.message : t('common.loadFailed')) }
    finally { setLoading(false) }
  }, [t])

  useEffect(() => { load() }, [load])

  const get = (key: string) => configs[key] || DEFAULTS[key] || ''
  const set = (key: string, value: string) => {
    setConfigs(p => ({ ...p, [key]: value }))
    setChanged(p => new Set(p).add(key))
  }

  const getBool = (key: string) => get(key) === 'true'
  const setBool = (key: string, v: boolean) => set(key, v ? 'true' : 'false')

  const handleSave = async () => {
    if (changed.size === 0) { message.info(t('common.noChanges')); return }
    setSaving(true)
    let done = 0; let fail = 0
    for (const key of changed) {
      try { await updateSystemConfig(key, get(key)); done++ } catch { fail++ }
    }
    setSaving(false)
    if (fail === 0) { message.success(t('systemConfig.saveSuccess', { count: done })); setChanged(new Set()) }
    else { message.warning(t('systemConfig.savePartial', { done, fail })) }
  }

  const handleReset = () => { setConfigs((prev) => ({ ...DEFAULTS, storage_used: prev.storage_used || DEFAULTS.storage_used })); setChanged(new Set(Object.keys(DEFAULTS).filter((key) => key !== 'storage_used'))); message.info(t('systemConfig.resetToDefault')) }

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', minHeight: 300, alignItems: 'center' }}><Spin size="large" /></div>
  if (error) return <Result status="error" title={t('common.loadFailed')} subTitle={error} extra={<Button type="primary" onClick={load}>{t('common.retry', '重试')}</Button>} />

  const changedStyle = { borderColor: '#f59e0b', boxShadow: '0 0 0 2px rgba(245,158,11,0.15)' }

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('systemConfig.title')}</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 14 }}>{t('systemConfig.description', '配置平台基本参数、安全策略、存储和通知')}</p>
      </div>

      <Card style={{ borderRadius: 12, border: '1px solid #e2e8f0', marginBottom: 20 }} styles={{ body: { padding: 24 } }}>
        <h3 style={{ margin: '0 0 16px', fontSize: 16, display: 'flex', alignItems: 'center', gap: 8, paddingBottom: 12, borderBottom: '1px solid #e2e8f0' }}>
          <InfoCircleOutlined style={{ color: '#3b82f6' }} /> {t('systemConfig.basicSettings', '基本设置')}
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="yx-form-row"><label>{t('systemConfig.platformName', '平台名称')}</label><Input value={get('platform_name')} onChange={e => set('platform_name', e.target.value)} style={changed.has('platform_name') ? changedStyle : undefined} /></div>
          <div className="yx-form-row"><label>Logo URL</label><Input value={get('logo_url')} onChange={e => set('logo_url', e.target.value)} style={changed.has('logo_url') ? changedStyle : undefined} /></div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 14 }}>
          <div className="yx-form-row"><label>{t('systemConfig.defaultLanguage', '默认语言')}</label><Select value={get('default_language')} onChange={v => set('default_language', v)} style={{ width: '100%', ...(changed.has('default_language') ? changedStyle : {}) }} options={[{ value: 'zh', label: t('systemConfig.languageZh') }, { value: 'en', label: 'English' }]} /></div>
          <div className="yx-form-row"><label>{t('systemConfig.timezone', '时区')}</label><Select value={get('timezone')} onChange={v => set('timezone', v)} style={{ width: '100%', ...(changed.has('timezone') ? changedStyle : {}) }} options={[{ value: 'shanghai', label: 'Asia/Shanghai (UTC+8)' }, { value: 'utc', label: 'UTC' }]} /></div>
        </div>
      </Card>

      <Card style={{ borderRadius: 12, border: '1px solid #e2e8f0', marginBottom: 20 }} styles={{ body: { padding: 24 } }}>
        <h3 style={{ margin: '0 0 16px', fontSize: 16, display: 'flex', alignItems: 'center', gap: 8, paddingBottom: 12, borderBottom: '1px solid #e2e8f0' }}>
          <SafetyOutlined style={{ color: '#3b82f6' }} /> {t('systemConfig.securitySettings', '安全设置')}
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="yx-form-row"><label>{t('systemConfig.sessionTimeout', '会话超时（分钟）')}</label><Input value={get('session_timeout')} onChange={e => set('session_timeout', e.target.value)} style={changed.has('session_timeout') ? changedStyle : undefined} /></div>
          <div className="yx-form-row"><label>{t('systemConfig.passwordMinLength', '密码最小长度（位）')}</label><Input value={get('password_min_length')} onChange={e => set('password_min_length', e.target.value)} style={changed.has('password_min_length') ? changedStyle : undefined} /></div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 14 }}>
          <div className="yx-form-row"><label>{t('systemConfig.loginLockThreshold', '登录失败锁定')}</label><Select value={get('login_lock_threshold')} onChange={v => set('login_lock_threshold', v)} style={{ width: '100%', ...(changed.has('login_lock_threshold') ? changedStyle : {}) }} options={[{ value: '5', label: t('systemConfig.lockAfter5') }, { value: '3', label: t('systemConfig.lockAfter3') }, { value: '0', label: t('systemConfig.neverLock') }]} /></div>
          <div className="yx-form-row"><label>{t('systemConfig.lockDuration', '锁定时间（分钟）')}</label><Input value={get('lock_duration')} onChange={e => set('lock_duration', e.target.value)} style={changed.has('lock_duration') ? changedStyle : undefined} /></div>
        </div>
        <div style={{ marginTop: 14 }}><Switch checked={getBool('two_factor')} onChange={v => setBool('two_factor', v)} /> <span style={{ marginLeft: 8 }}>{t('systemConfig.enableTwoFactor', '启用两步验证')}</span></div>
      </Card>

      <Card style={{ borderRadius: 12, border: '1px solid #e2e8f0', marginBottom: 20 }} styles={{ body: { padding: 24 } }}>
        <h3 style={{ margin: '0 0 16px', fontSize: 16, display: 'flex', alignItems: 'center', gap: 8, paddingBottom: 12, borderBottom: '1px solid #e2e8f0' }}>
          <HddOutlined style={{ color: '#3b82f6' }} /> {t('systemConfig.storageSettings', '存储设置')}
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="yx-form-row"><label>{t('systemConfig.storagePath', '数据存储路径')}</label><Input value={get('storage_path')} onChange={e => set('storage_path', e.target.value)} style={changed.has('storage_path') ? changedStyle : undefined} /></div>
          <div className="yx-form-row"><label>{t('systemConfig.backupPath', '备份路径')}</label><Input value={get('backup_path')} onChange={e => set('backup_path', e.target.value)} style={changed.has('backup_path') ? changedStyle : undefined} /></div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 14 }}>
          <div className="yx-form-row"><label>{t('systemConfig.storageLimit', '存储容量上限（GB）')}</label><Input value={get('storage_limit')} onChange={e => set('storage_limit', e.target.value)} style={changed.has('storage_limit') ? changedStyle : undefined} /></div>
          <div className="yx-form-row"><label>{t('systemConfig.storageUsed', '已用容量')}</label><Input value={get('storage_used') + ' GB (25.4%)'} disabled /></div>
        </div>
        <div style={{ marginTop: 14 }}><Switch checked={getBool('auto_backup')} onChange={v => setBool('auto_backup', v)} /> <span style={{ marginLeft: 8 }}>{t('systemConfig.enableAutoBackup', '启用自动备份（每天 04:00）')}</span></div>
      </Card>

      <Card style={{ borderRadius: 12, border: '1px solid #e2e8f0', marginBottom: 20 }} styles={{ body: { padding: 24 } }}>
        <h3 style={{ margin: '0 0 16px', fontSize: 16, display: 'flex', alignItems: 'center', gap: 8, paddingBottom: 12, borderBottom: '1px solid #e2e8f0' }}>
          <MailOutlined style={{ color: '#3b82f6' }} /> {t('systemConfig.notificationSettings', '通知设置')}
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="yx-form-row"><label>SMTP {t('systemConfig.smtpServer', '服务器')}</label><Input value={get('smtp_server')} onChange={e => set('smtp_server', e.target.value)} style={changed.has('smtp_server') ? changedStyle : undefined} /></div>
          <div className="yx-form-row"><label>SMTP {t('systemConfig.smtpPort', '端口')}</label><Input value={get('smtp_port')} onChange={e => set('smtp_port', e.target.value)} style={changed.has('smtp_port') ? changedStyle : undefined} /></div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 14 }}>
          <div className="yx-form-row"><label>{t('systemConfig.senderEmail', '发件人邮箱')}</label><Input value={get('sender_email')} onChange={e => set('sender_email', e.target.value)} style={changed.has('sender_email') ? changedStyle : undefined} /></div>
          <div className="yx-form-row"><label>{t('systemConfig.adminEmail', '管理员邮箱')}</label><Input value={get('admin_email')} onChange={e => set('admin_email', e.target.value)} style={changed.has('admin_email') ? changedStyle : undefined} /></div>
        </div>
        <div className="yx-form-row" style={{ marginTop: 14 }}><label>Webhook URL</label><Input value={get('webhook_url')} onChange={e => set('webhook_url', e.target.value)} style={changed.has('webhook_url') ? changedStyle : undefined} /></div>
      </Card>

      <div style={{ display: 'flex', gap: 12 }}>
        <Button type="primary" icon={<SaveOutlined />} loading={saving} onClick={handleSave}>{t('systemConfig.saveAll', '保存全部配置')}</Button>
        <Button icon={<UndoOutlined />} onClick={handleReset}>{t('systemConfig.resetDefault', '恢复默认')}</Button>
        {changed.size > 0 && <span style={{ color: '#f59e0b', fontSize: 13, alignSelf: 'center' }}>{t('systemConfig.changedItems', { count: changed.size })}</span>}
      </div>
    </div>
  )
}