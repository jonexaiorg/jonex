import React from 'react';
import { useTranslation } from 'react-i18next';
import { Table, Typography, Select, Input, Button } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { MOCK_DOMAIN_PERMISSIONS } from '../../data/mock';
import { colors, radius } from '@jonex/platform-theme/tokens';
import type { ColumnsType } from 'antd/es/table';
import type { DomainPermission } from '../../data/mock';

const { Title, Text } = Typography;

export default function DomainPermissionPage() {
  const { t } = useTranslation();

  const ROLE_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
    admin: { label: t('domainPermission.roleAdmin'), color: '#3b82f6', bg: '#eff6ff' },
    editor: { label: t('domainPermission.roleEditor'), color: '#059669', bg: '#ecfdf5' },
    viewer: { label: t('domainPermission.roleViewer'), color: '#94a3b8', bg: '#f8fafc' },
  };

  const columns: ColumnsType<DomainPermission> = [
    {
      title: t('domainPermission.columnUser'),
      dataIndex: 'displayName',
      key: 'displayName',
      width: 200,
      render: (name: string, record: DomainPermission) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: `linear-gradient(135deg, ${colors.accentSoft}, ${colors.accent})`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontSize: 13,
              fontWeight: 600,
            }}
          >
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
      title: t('domainPermission.columnUsername'),
      dataIndex: 'username',
      key: 'username',
      render: (u: string) => (
        <code style={{ fontSize: 12, background: colors.rowBorder, padding: '2px 8px', borderRadius: 4 }}>{u}</code>
      ),
    },
    {
      title: t('domainPermission.columnRole'),
      dataIndex: 'role',
      key: 'role',
      width: 200,
      render: (role: string) => {
        const config = ROLE_CONFIG[role];
        return (
          <Select
            className="filter-select"
            defaultValue={role}
            style={{ width: 120 }}
            options={[
              { value: 'admin', label: t('domainPermission.roleAdmin') },
              { value: 'editor', label: t('domainPermission.roleEditor') },
              { value: 'viewer', label: t('domainPermission.roleViewer') },
            ]}
          />
        );
      },
    },
    {
      title: t('domainPermission.columnActions'),
      key: 'actions',
      width: 80,
      render: () => (
        <a className="yx-table-action" style={{ color: colors.errorText }}>
          {t('domainPermission.removeMember')}
        </a>
      ),
    },
  ];

  return (
    <div>
      <div className="page-title" style={{ marginBottom: 24 }}>
        <Title level={1} style={{ fontSize: 24, fontWeight: 700, color: colors.brandDark, marginBottom: 4 }}>
          {t('domainPermission.pageTitle')}
        </Title>
        <Text type="secondary" style={{ fontSize: 14 }}>
          {t('domainPermission.pageSubtitle')}
        </Text>
      </div>

      <div className="yx-toolbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Input
            prefix={<SearchOutlined style={{ color: colors.textMuted, fontSize: 14 }} />}
            placeholder={t('domainPermission.searchMember')}
          />
        </div>
        <Button
          type="primary"
          style={{
            borderRadius: radius.btn,
            background: colors.accent,
            padding: '7px 16px',
            fontSize: 13,
            fontWeight: 500,
          }}
        >
          {t('domainPermission.addMemberBtn')}
        </Button>
      </div>

      <div
        style={{
          background: colors.white,
          borderRadius: radius.card,
          padding: 0,
          border: `1px solid ${colors.borderLight}`,
          boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
        }}
      >
        <Table columns={columns} dataSource={MOCK_DOMAIN_PERMISSIONS} rowKey="id" pagination={false} />
      </div>
    </div>
  );
}
