import React from 'react'
import { Table, Typography } from 'antd'
import { useTranslation } from 'react-i18next'
import { MOCK_DOMAIN_PERMISSIONS } from '../../data/mock'
import { colors, radius } from '@jonex/platform-theme/tokens'
import type { ColumnsType } from 'antd/es/table'
import type { DomainPermission } from '../../data/mock'

const { Title, Text } = Typography
const ROLES = ['admin', 'editor', 'viewer'] as const

export default function DomainPermissionPage() {
  const { t } = useTranslation('business')
  const columns: ColumnsType<DomainPermission> = [
    {
      title: t('domainService.user'),
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
      title: t('domainService.username'),
      dataIndex: 'username',
      key: 'username',
      render: (username: string) => <code style={{ fontSize: 12, background: colors.rowBorder, padding: '2px 8px', borderRadius: 4 }}>{username}</code>,
    },
    {
      title: t('domainService.role'),
      dataIndex: 'role',
      key: 'role',
      width: 200,
      render: (role: string) => (
        <select
          className="filter-select"
          defaultValue={role}
          aria-label={t('domainService.role')}
          style={{
            padding: '6px 12px', border: `1px solid ${colors.border}`,
            borderRadius: radius.btn, fontSize: 13, color: colors.textPrimary,
            background: colors.white, cursor: 'pointer',
          }}
        >
          {ROLES.map((value) => (
            <option key={value} value={value}>{t(`domainService.roles.${value}`)}</option>
          ))}
        </select>
      ),
    },
    {
      title: t('knowledgeSearch.actions'),
      key: 'actions',
      width: 80,
      render: () => (
        <a className="yx-table-action" style={{ color: colors.errorText }}>{t('domainService.remove')}</a>
      ),
    },
  ]

  return (
    <div>
      <div className="page-title" style={{ marginBottom: 24 }}>
        <Title level={1} style={{ fontSize: 24, fontWeight: 700, color: colors.brandDark, marginBottom: 4 }}>
          {t('domainSpace.permission')}
        </Title>
        <Text type="secondary" style={{ fontSize: 14 }}>{t('domainService.permissionPageDescription')}</Text>
      </div>

      <div className="yx-toolbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div className="yx-search-box">
            <i className="fas fa-search" style={{ color: colors.textMuted, fontSize: 14 }} />
            <input type="text" placeholder={t('domainService.searchMembers')} />
          </div>
        </div>
        <button className="btn btn-primary" style={{ padding: '7px 16px', borderRadius: radius.btn, background: colors.accent, color: '#fff', border: 'none', fontSize: 13, fontWeight: 500, cursor: 'pointer' }}>
          <i className="fas fa-plus" style={{ marginRight: 6 }} />{t('domainKnowledge.addMember')}
        </button>
      </div>

      <div style={{ background: colors.white, borderRadius: radius.card, padding: 0, border: `1px solid ${colors.borderLight}`, boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
        <Table
          columns={columns}
          dataSource={MOCK_DOMAIN_PERMISSIONS}
          rowKey="id"
          pagination={false}
        />
      </div>
    </div>
  )
}
