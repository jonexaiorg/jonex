import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Row, Col, Card } from 'antd'
import { RobotOutlined, TeamOutlined, UserOutlined, SafetyOutlined, ScheduleOutlined, FileTextOutlined, SettingOutlined } from '@ant-design/icons'

const actions = [
  { label: '模型适配', desc: '管理 AI 模型与适配器', path: '/model-adapter', icon: <RobotOutlined />, color: '#10b981' },
  { label: '租户管理', desc: '管理平台租户与配额', path: '/tenant-management', icon: <TeamOutlined />, color: '#3b82f6' },
  { label: '用户管理', desc: '用户账号与权限管理', path: '/user-management', icon: <UserOutlined />, color: '#8b5cf6' },
  { label: '角色权限', desc: '角色定义与权限配置', path: '/role-permission', icon: <SafetyOutlined />, color: '#f59e0b' },
  { label: '任务调度', desc: '定时任务与调度管理', path: '/task-schedule', icon: <ScheduleOutlined />, color: '#ec4899' },
  { label: '系统配置', desc: '平台全局参数配置', path: '/system-config', icon: <SettingOutlined />, color: '#64748b' },
  { label: '日志管理', desc: '操作日志与审计追踪', path: '/operation-log', icon: <FileTextOutlined />, color: '#ef4444' },
]

export default function Home() {
  const navigate = useNavigate()
  return (
    <div>
      <div className="yx-page-title">
        <h1>平台管理</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 14 }}>平台基础配置与管理</p>
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
