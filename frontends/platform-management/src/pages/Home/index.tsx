import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Row, Col, Card } from 'antd'
import { useTranslation } from 'react-i18next'
import { RobotOutlined, TeamOutlined, UserOutlined, SafetyOutlined, ScheduleOutlined, FileTextOutlined, SettingOutlined } from '@ant-design/icons'

export default function Home() {
  const navigate = useNavigate()
  const { t } = useTranslation()

  const actions = [
    { label: t('home.manageUsers'), desc: t('home.manageUsers'), path: '/model-adapter', icon: <RobotOutlined />, color: '#10b981' },
    { label: t('home.manageTenants'), desc: t('home.manageTenants'), path: '/tenant-management', icon: <TeamOutlined />, color: '#3b82f6' },
    { label: t('userManagement.title'), desc: t('userManagement.title'), path: '/user-management', icon: <UserOutlined />, color: '#8b5cf6' },
    { label: t('rolePermission.title'), desc: t('rolePermission.title'), path: '/role-permission', icon: <SafetyOutlined />, color: '#f59e0b' },
    { label: t('taskSchedule.title'), desc: t('taskSchedule.title'), path: '/task-schedule', icon: <ScheduleOutlined />, color: '#ec4899' },
    { label: t('systemConfig.title'), desc: t('systemConfig.title'), path: '/system-config', icon: <SettingOutlined />, color: '#64748b' },
    { label: t('operationLog.title'), desc: t('operationLog.title'), path: '/operation-log', icon: <FileTextOutlined />, color: '#ef4444' },
  ]

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('home.title')}</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 14 }}>{t('home.welcome')}</p>
      </div>
      <Row gutter={[16, 16]}>
        {actions.map((a) => (
          <Col xs={24} sm={12} md={8} key={a.label}>
            <a onClick={() => navigate(a.path)} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '18px 20px', background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', textDecoration: 'none', cursor: 'pointer', transition: 'all 0.2s' }}>
              <span style={{ fontSize: 22, color: a.color, background: `${a.color}15`, width: 44, height: 44, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{a.icon}</span>
              <div><div style={{ fontSize: 14, fontWeight: 500, color: '#1e293b' }}>{a.label}</div><div style={{ fontSize: 12, color: '#94a3b8' }}>{a.desc}</div></div>
            </a>
          </Col>
        ))}
      </Row>
    </div>
  )
}
