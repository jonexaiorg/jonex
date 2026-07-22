import React from 'react'
import { Button, Tag } from 'antd'
import { EditOutlined, TeamOutlined } from '@ant-design/icons'

const roles = [
  { name: '系统管理员', count: 3, perms: ['平台配置', '用户管理', '租户管理', '模型管理', '全部权限'], admin: true },
  { name: '领域服务管理员', count: 5, perms: ['领域服务管理', '知识库管理', '数据源管理', '服务管理'], admin: false },
  { name: '知识编辑者', count: 12, perms: ['知识编辑', '知识查看', '数据上传'], admin: false },
  { name: '观察者', count: 8, perms: ['知识查看', '检索使用'], admin: false },
]

export default function RolePermission() {
  return (
    <div>
      <div className="yx-page-title">
        <h1>角色权限</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 14 }}>管理系统角色及其权限配置</p>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 20 }}>
        {roles.map((r, i) => (
          <div key={i} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 12, padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <span style={{ fontSize: 16, fontWeight: 600 }}>{r.name}</span>
              <span style={{ fontSize: 13, color: '#64748b' }}><TeamOutlined /> {r.count} 人</span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
              {r.perms.map((p) => (
                <Tag key={p} style={{ background: r.admin ? '#eff6ff' : '#f1f5f9', color: r.admin ? '#3b82f6' : '#475569', border: 'none', borderRadius: 6, padding: '4px 12px' }}>{p}</Tag>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <Button type="primary" size="small" icon={<EditOutlined />}>编辑权限</Button>
              <Button size="small" icon={<TeamOutlined />}>查看成员</Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
