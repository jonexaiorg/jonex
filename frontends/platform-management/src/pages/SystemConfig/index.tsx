import React from 'react'
import { Input, Select, Switch, Button, message, Card } from 'antd'
import { SaveOutlined, UndoOutlined, InfoCircleOutlined, SafetyOutlined, HddOutlined, MailOutlined } from '@ant-design/icons'

export default function SystemConfig() {
  return (
    <div>
      <div className="yx-page-title">
        <h1>系统配置</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 14 }}>配置平台基本参数、安全策略、存储和通知</p>
      </div>

      <Card style={{ borderRadius: 12, border: '1px solid #e2e8f0', marginBottom: 20 }} styles={{ body: { padding: 24 } }}>
        <h3 style={{ margin: '0 0 16px', fontSize: 16, display: 'flex', alignItems: 'center', gap: 8, paddingBottom: 12, borderBottom: '1px solid #e2e8f0' }}>
          <InfoCircleOutlined style={{ color: '#3b82f6' }} /> 基本设置
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="yx-form-row"><label>平台名称</label><Input defaultValue="Jonex知识平台" /></div>
          <div className="yx-form-row"><label>Logo URL</label><Input defaultValue="/assets/logo.png" /></div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 14 }}>
          <div className="yx-form-row"><label>默认语言</label><Select defaultValue="zh" style={{ width: '100%' }} options={[{ value: 'zh', label: '简体中文' }, { value: 'en', label: 'English' }]} /></div>
          <div className="yx-form-row"><label>时区</label><Select defaultValue="shanghai" style={{ width: '100%' }} options={[{ value: 'shanghai', label: 'Asia/Shanghai (UTC+8)' }, { value: 'utc', label: 'UTC' }]} /></div>
        </div>
      </Card>

      <Card style={{ borderRadius: 12, border: '1px solid #e2e8f0', marginBottom: 20 }} styles={{ body: { padding: 24 } }}>
        <h3 style={{ margin: '0 0 16px', fontSize: 16, display: 'flex', alignItems: 'center', gap: 8, paddingBottom: 12, borderBottom: '1px solid #e2e8f0' }}>
          <SafetyOutlined style={{ color: '#3b82f6' }} /> 安全设置
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="yx-form-row"><label>会话超时时间</label><Input defaultValue="30 分钟" /></div>
          <div className="yx-form-row"><label>密码最小长度</label><Input defaultValue="8 位" /></div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 14 }}>
          <div className="yx-form-row"><label>登录失败锁定</label><Select defaultValue="5" style={{ width: '100%' }} options={[{ value: '5', label: '5 次后锁定' }, { value: '3', label: '3 次后锁定' }, { value: '0', label: '不锁定' }]} /></div>
          <div className="yx-form-row"><label>锁定时间</label><Input defaultValue="15 分钟" /></div>
        </div>
        <div style={{ marginTop: 14 }}><Switch defaultChecked /> <span style={{ marginLeft: 8 }}>启用两步验证</span></div>
      </Card>

      <Card style={{ borderRadius: 12, border: '1px solid #e2e8f0', marginBottom: 20 }} styles={{ body: { padding: 24 } }}>
        <h3 style={{ margin: '0 0 16px', fontSize: 16, display: 'flex', alignItems: 'center', gap: 8, paddingBottom: 12, borderBottom: '1px solid #e2e8f0' }}>
          <HddOutlined style={{ color: '#3b82f6' }} /> 存储设置
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="yx-form-row"><label>数据存储路径</label><Input defaultValue="/data/jonex/storage" /></div>
          <div className="yx-form-row"><label>备份路径</label><Input defaultValue="/data/jonex/backup" /></div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 14 }}>
          <div className="yx-form-row"><label>存储容量上限</label><Input defaultValue="500 GB" /></div>
          <div className="yx-form-row"><label>已用容量</label><Input defaultValue="127 GB (25.4%)" disabled /></div>
        </div>
        <div style={{ marginTop: 14 }}><Switch defaultChecked /> <span style={{ marginLeft: 8 }}>启用自动备份（每天 04:00）</span></div>
      </Card>

      <Card style={{ borderRadius: 12, border: '1px solid #e2e8f0', marginBottom: 20 }} styles={{ body: { padding: 24 } }}>
        <h3 style={{ margin: '0 0 16px', fontSize: 16, display: 'flex', alignItems: 'center', gap: 8, paddingBottom: 12, borderBottom: '1px solid #e2e8f0' }}>
          <MailOutlined style={{ color: '#3b82f6' }} /> 通知设置
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="yx-form-row"><label>SMTP 服务器</label><Input defaultValue="smtp.example.com" /></div>
          <div className="yx-form-row"><label>SMTP 端口</label><Input defaultValue="587" /></div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 14 }}>
          <div className="yx-form-row"><label>发件人邮箱</label><Input defaultValue="noreply@jonex.com" /></div>
          <div className="yx-form-row"><label>管理员邮箱</label><Input defaultValue="admin@jonex.com" /></div>
        </div>
        <div className="yx-form-row" style={{ marginTop: 14 }}><label>Webhook URL</label><Input defaultValue="https://hooks.example.com/jonex/notify" /></div>
      </Card>

      <div style={{ display: 'flex', gap: 12 }}>
        <Button type="primary" icon={<SaveOutlined />} onClick={() => message.success('全部配置已保存')}>保存全部配置</Button>
        <Button icon={<UndoOutlined />} onClick={() => message.info('已恢复默认配置')}>恢复默认</Button>
      </div>
    </div>
  )
}
