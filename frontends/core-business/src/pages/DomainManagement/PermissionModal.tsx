import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Modal, Button, Input, Spin } from 'antd';
import { TeamOutlined, UserAddOutlined, SearchOutlined, CloseOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { DomainServiceItem, PermMember } from '../../types/domainService';
import { userToPermMember } from '../../types/domainService';
import { listUsers, type PlatformUser } from '../../api/user';

interface PermissionModalProps {
  open: boolean;
  permTarget: DomainServiceItem | null;
  permMembers: PermMember[];
  permSearch: string;
  permLoading: boolean;
  permSaving: boolean;
  onPermSearchChange: (val: string) => void;
  onRoleChange: (userId: string, role: 'viewer' | 'manager') => void;
  onRemoveMember: (userId: string) => void;
  onAddMember: (user: PlatformUser) => void;
  onSave: () => void;
  onCancel: () => void;
}

export default function PermissionModal({
  open,
  permTarget,
  permMembers,
  permSearch,
  permLoading,
  permSaving,
  onPermSearchChange,
  onRoleChange,
  onRemoveMember,
  onAddMember,
  onSave,
  onCancel,
}: PermissionModalProps) {
  const { t } = useTranslation();

  // ── User selector internal state ──
  const [userSelectOpen, setUserSelectOpen] = useState(false);
  const [userSearchText, setUserSearchText] = useState('');
  const [availableUsers, setAvailableUsers] = useState<PlatformUser[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const userSelectRef = useRef<HTMLDivElement>(null);

  const loadAvailableUsers = useCallback(async () => {
    setUsersLoading(true);
    try {
      const result = await listUsers(1, 100);
      setAvailableUsers(result.items);
    } catch {
      setAvailableUsers([]);
    } finally {
      setUsersLoading(false);
    }
  }, []);

  // 关闭用户选择器（外部点击）
  useEffect(() => {
    if (!userSelectOpen) return;
    const handler = (e: MouseEvent) => {
      if (userSelectRef.current && !userSelectRef.current.contains(e.target as Node)) {
        setUserSelectOpen(false);
        setUserSearchText('');
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [userSelectOpen]);

  // 可用用户列表中排除已添加的成员
  const addedUserIds = new Set(permMembers.map((m) => m.id));
  const filteredAvailableUsers = availableUsers.filter((u) => {
    if (!userSearchText) return !addedUserIds.has(String(u.id));
    const q = userSearchText.toLowerCase();
    return (
      !addedUserIds.has(String(u.id)) &&
      ((u.display_name || '').toLowerCase().includes(q) ||
        u.username.toLowerCase().includes(q) ||
        (u.email || '').toLowerCase().includes(q))
    );
  });

  // 过滤后的权限成员
  const filteredPermMembers = permMembers.filter((m) => {
    if (!permSearch) return true;
    return m.name.includes(permSearch) || m.department.includes(permSearch);
  });

  const handleCancel = () => {
    onCancel();
    setUserSelectOpen(false);
  };

  return (
    <Modal
      wrapClassName="yx-domain-space-modal"
      title={
        <span>
          <TeamOutlined style={{ color: '#3b82f6', marginRight: 8 }} />
          {t('domainManagement.permTitle')}
        </span>
      }
      open={open}
      onCancel={handleCancel}
      onOk={onSave}
      confirmLoading={permSaving}
      okText={t('domainManagement.savePermission')}
      cancelText={t('common.cancel')}
      width={600}
    >
      <p style={{ fontSize: 14, color: '#475569', marginBottom: 12 }}>
        {t('domainManagement.permDesc', { name: permTarget?.name || '' })}
      </p>

      {/* 添加成员区域 */}
      <div ref={userSelectRef} style={{ position: 'relative', marginBottom: 12 }}>
        <Button
          icon={<UserAddOutlined />}
          onClick={() => {
            const willOpen = !userSelectOpen;
            setUserSelectOpen(willOpen);
            setUserSearchText('');
            if (willOpen && availableUsers.length === 0) loadAvailableUsers();
          }}
          style={{ marginBottom: userSelectOpen ? 8 : 0 }}
        >
          {t('domainManagement.addMember')}
        </Button>
        {userSelectOpen && (
          <div
            style={{
              position: 'absolute',
              top: 38,
              left: 0,
              zIndex: 10,
              width: 320,
              background: '#fff',
              borderRadius: 8,
              boxShadow: '0 4px 20px rgba(0,0,0,.12)',
              border: '1px solid #e2e8f0',
              overflow: 'hidden',
            }}
          >
            <div style={{ padding: '8px 12px', borderBottom: '1px solid #e2e8f0' }}>
              <Input
                size="small"
                placeholder={t('domainManagement.searchUser')}
                prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
                value={userSearchText}
                onChange={(e) => setUserSearchText(e.target.value)}
                allowClear
              />
            </div>
            <div style={{ maxHeight: 220, overflowY: 'auto' }}>
              {usersLoading ? (
                <div style={{ textAlign: 'center', padding: 20 }}>
                  <Spin size="small" />
                </div>
              ) : filteredAvailableUsers.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 20, color: '#94a3b8', fontSize: 13 }}>
                  {userSearchText ? t('domainManagement.noMatchUser') : t('domainManagement.noAvailableUser')}
                </div>
              ) : (
                filteredAvailableUsers.slice(0, 30).map((user) => (
                  <div
                    key={user.id}
                    className="yx-perm-user-row"
                    style={{ cursor: 'pointer', padding: '8px 12px' }}
                    onClick={() => {
                      onAddMember(user);
                      setUserSearchText('');
                    }}
                  >
                    <div className="yx-perm-avatar" style={{ background: userToPermMember(user).avatarColor }}>
                      {userToPermMember(user).avatar}
                    </div>
                    <div className="yx-perm-user-info" style={{ flex: 1 }}>
                      <div className="yx-perm-user-name">{user.display_name || user.username}</div>
                      <div className="yx-perm-user-dept">{user.email || user.role || ''}</div>
                    </div>
                    <span style={{ fontSize: 20, color: '#3b82f6', lineHeight: 1 }}>+</span>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      {/* 已有成员搜索 */}
      <Input
        prefix={<SearchOutlined style={{ color: '#94a3b8', fontSize: 14 }} />}
        placeholder={t('domainManagement.searchMember')}
        value={permSearch}
        onChange={(e) => onPermSearchChange(e.target.value)}
        style={{ width: '100%', marginBottom: 12 }}
      />

      {/* 成员列表 */}
      <div style={{ maxHeight: 280, overflowY: 'auto' }}>
        {permLoading ? (
          <div style={{ textAlign: 'center', padding: 24 }}>
            <Spin />
          </div>
        ) : filteredPermMembers.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 24, color: '#94a3b8', fontSize: 13 }}>
            {permSearch ? t('domainManagement.noMatchMember') : t('domainManagement.noMembers')}
          </div>
        ) : (
          filteredPermMembers.map((member) => (
            <div key={member.id} className="yx-perm-user-row">
              <div className="yx-perm-avatar" style={{ background: member.avatarColor }}>
                {member.avatar}
              </div>
              <div className="yx-perm-user-info" style={{ flex: 1 }}>
                <div className="yx-perm-user-name">{member.name}</div>
                <div className="yx-perm-user-dept">{member.department || `ID: ${member.id.slice(0, 8)}`}</div>
              </div>
              <div className="yx-perm-radio">
                <label className={`yx-perm-radio-label${member.role === 'viewer' ? ' is-checked' : ''}`}>
                  <input
                    type="radio"
                    name={`perm-${member.id}`}
                    value="viewer"
                    checked={member.role === 'viewer'}
                    onChange={() => onRoleChange(member.id, 'viewer')}
                  />
                  {t('permission.view')}
                </label>
                <label className={`yx-perm-radio-label${member.role === 'manager' ? ' is-checked' : ''}`}>
                  <input
                    type="radio"
                    name={`perm-${member.id}`}
                    value="manager"
                    checked={member.role === 'manager'}
                    onChange={() => onRoleChange(member.id, 'manager')}
                  />
                  {t('permission.manage')}
                </label>
              </div>
              <Button
                type="text"
                className="yx-perm-remove-btn"
                onClick={() => onRemoveMember(member.id)}
                title={t('domainManagement.removeMember')}
                style={{
                  color: '#94a3b8',
                  fontSize: 16,
                  padding: '0 0 0 8px',
                  lineHeight: 1,
                }}
              >
                <CloseOutlined />
              </Button>
            </div>
          ))
        )}
      </div>
    </Modal>
  );
}
