import React from 'react'
import { Table, Typography, Select } from 'antd'
import type { DomainPermission } from '../../types/viewModels'
import { colors, radius } from '@jonex/platform-theme/tokens'
import type { ColumnsType } from 'antd/es/table'

const { Title, Text } = Typography

const domainPermissions: DomainPermission[] = []

const ROLE_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  admin: { label: '管理员', color: '#3b82f6', bg: '#eff6ff' },
  editor: { label: '编辑者', color: '#059669', bg: '#ecfdf5' },
  viewer: { label: '观察者', color: '#94a3b8', bg: '#f8fafc' },
}

export default function DomainPermissionPage() {
  const columns: ColumnsType<DomainPermission> = [
    {
      title: '用户',
      dataIndex: 'displayName',
      key: 'displayName',
      width: 200,
      render: (name: string, record: DomainPermission) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: `linear-gradient(135deg, ${colors.accentSoft}, ${colors.accent})`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontSize: 13, fontWeight: 600,
          }}>
            {name.charAt(0)}
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 500, color: colors.textPrimary }}>{name}</div>
            <div style={{ fontSize: 12, color: colors.textMuted }}>@{record.username}</div>
          </div>
        </div>
      ),
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      render: (u: string) => <code style={{ fontSize: 12, background: colors.rowBorder, padding: '2px 8px', borderRadius: 4 }}>{u}</code>,
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      width: 200,
      render: (role: string) => {
        const config = ROLE_CONFIG[role]
        return (
          <select
            className="filter-select"
            defaultValue={role}
            style={{
              padding: '6px 12px', border: `1px solid ${colors.border}`,
              borderRadius: radius.btn, fontSize: 13, color: colors.textPrimary,
              background: colors.white, cursor: 'pointer',
            }}
          >
            <option value="admin">管理员</option>
            <option value="editor">编辑者</option>
            <option value="viewer">观察者</option>
          </select>
        )
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 80,
      render: () => (
        <a className="yx-table-action" style={{ color: colors.errorText }}>移除</a>
      ),
    },
  ]

  return (
    <div>
      <div className="page-title" style={{ marginBottom: 24 }}>
        <Title level={1} style={{ fontSize: 24, fontWeight: 700, color: colors.brandDark, marginBottom: 4 }}>
          领域权限
        </Title>
        <Text type="secondary" style={{ fontSize: 14 }}>管理领域空间的成员权限</Text>
      </div>

      <div className="yx-toolbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div className="yx-search-box">
            <i className="fas fa-search" style={{ color: colors.textMuted, fontSize: 14 }} />
            <input type="text" placeholder="搜索成员..." />
          </div>
        </div>
        <button className="btn btn-primary" style={{ padding: '7px 16px', borderRadius: radius.btn, background: colors.accent, color: '#fff', border: 'none', fontSize: 13, fontWeight: 500, cursor: 'pointer' }}>
          <i className="fas fa-plus" style={{ marginRight: 6 }} />添加成员
        </button>
      </div>

      <div style={{ background: colors.white, borderRadius: radius.card, padding: 0, border: `1px solid ${colors.borderLight}`, boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
        <Table
          columns={columns}
          dataSource={domainPermissions}
          rowKey="id"
          pagination={false}
        />
      </div>
    </div>
  )
}
