import React from 'react';
import { Button, Table, Select, message } from 'antd';
import { TeamOutlined, PlusOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { DomainKnowledgePermissionMember } from '@/types/domainKnowledge';

interface PermissionTabProps {
  members: DomainKnowledgePermissionMember[];
  loading: boolean;
  saving: boolean;
  memberName: (member: DomainKnowledgePermissionMember) => string;
  onRoleChange: (userId: string, role: 'view' | 'manage') => void;
  onRemove: (userId: string) => void;
  onSave: () => void;
}

export default function PermissionTab({
  members,
  loading,
  saving,
  memberName,
  onRoleChange,
  onRemove,
  onSave,
}: PermissionTabProps) {
  const { t } = useTranslation();

  return (
    <div className="config-section yx-kb-section-card">
      <div className="yx-kb-flex-header">
        <h3 className="yx-kb-section-title">
          <TeamOutlined className="yx-kb-icon-blue" /> {t('domainKnowledge.permissionSettings')}
        </h3>
        <Button
          className="yx-kb-section-add-btn"
          icon={<PlusOutlined />}
          onClick={() => message.info(t('domainKnowledge.addMemberComingSoon'))}
        >
          {t('domainKnowledge.addMember')}
        </Button>
      </div>
      <p className="yx-kb-section-desc">{t('domainKnowledge.permissionDesc')}</p>
      <Table
        columns={[
          {
            title: t('domainKnowledge.user'),
            dataIndex: 'userId',
            key: 'user',
            width: 200,
            render: (_: unknown, record: DomainKnowledgePermissionMember) => (
              <div style={{ fontWeight: 500, color: '#0b2b5c' }}>{memberName(record)}</div>
            ),
          },
          {
            title: t('domainKnowledge.role'),
            dataIndex: 'role',
            key: 'role',
            width: 160,
            render: (role: string, record: DomainKnowledgePermissionMember) => (
              <Select
                value={role}
                onChange={(value) => onRoleChange(record.userId, value as 'view' | 'manage')}
                style={{ width: 120 }}
                options={[
                  { value: 'manage', label: t('permission.admin') },
                  { value: 'view', label: t('permission.viewer') },
                ]}
              />
            ),
          },
          {
            title: t('common.actions'),
            key: 'actions',
            width: 100,
            render: (_: unknown, record: DomainKnowledgePermissionMember) => (
              <a className="yx-table-action" style={{ cursor: 'pointer' }} onClick={() => onRemove(record.userId)}>
                {t('domainKnowledge.remove')}
              </a>
            ),
          },
        ]}
        dataSource={members}
        rowKey="userId"
        pagination={false}
        size="middle"
        loading={loading}
        locale={{ emptyText: t('domainKnowledge.noMembers') }}
      />
      <div className="yx-kb-save-bar">
        <Button type="primary" loading={saving} onClick={onSave}>
          {t('domainKnowledge.savePermission')}
        </Button>
      </div>
    </div>
  );
}
