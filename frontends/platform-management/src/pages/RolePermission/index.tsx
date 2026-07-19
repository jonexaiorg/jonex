import React, { useState, useEffect, useCallback } from 'react'
import { Button, Tag, Modal, Input, message, Spin, Result, Checkbox } from 'antd'
import { useTranslation } from 'react-i18next'
import { EditOutlined, TeamOutlined, PlusOutlined } from '@ant-design/icons'
import {
  listRoles, createRole, updateRole, deleteRole,
  listPermissions, getRolePermissions, setRolePermissions,
  type RoleItem, type PermissionItem,
} from '../../api/roles'

export default function RolePermission() {
  const { t } = useTranslation()
  const [roles, setRoles] = useState<RoleItem[]>([])
  const [perms, setPerms] = useState<PermissionItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [permModal, setPermModal] = useState<{ role: RoleItem; checked: number[] } | null>(null)
  const [newRoleModal, setNewRoleModal] = useState(false)
  const [newRoleName, setNewRoleName] = useState('')

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const [r, p] = await Promise.all([listRoles(), listPermissions()])
      setRoles(r.items); setPerms(p.items)
    } catch (e: unknown) { setError(e instanceof Error ? e.message : t('common.loadFailed')) }
    finally { setLoading(false) }
  }, [t])

  const loadPerms = useCallback(async (role: RoleItem) => {
    try {
      const ids = await getRolePermissions(role.id)
      setPermModal({ role, checked: ids })
    } catch (e) { message.error(t('rolePermission.permissionSaveFailed')) }
  }, [t])

  useEffect(() => { load() }, [load])

  const handleSavePerms = async () => {
    if (!permModal) return
    try { await setRolePermissions(permModal.role.id, permModal.checked); message.success(t('rolePermission.permissionSaved')); setPermModal(null) }
    catch { message.error(t('common.saveFailed')) }
  }

  const handleCreateRole = async () => {
    if (!newRoleName) { message.warning(t('rolePermission.nameRequired')); return }
    try { await createRole({ name: newRoleName }); setNewRoleModal(false); setNewRoleName(''); await load(); message.success(t('rolePermission.createSuccess')) }
    catch (e: unknown) { message.error(e instanceof Error ? e.message : t('common.saveFailed')) }
  }

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', minHeight: 300, alignItems: 'center' }}><Spin size="large" /></div>
  if (error) return <Result status="error" title={t('common.loadFailed')} subTitle={error} extra={<Button type="primary" onClick={load}>{t('common.retry', '重试')}</Button>} />

  return (
    <div>
      <div className="yx-page-title">
        <h1>{t('rolePermission.title')}</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0', fontSize: 14 }}>{t('rolePermission.manageDesc', '管理系统角色及其权限配置')}</p>
      </div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setNewRoleName(''); setNewRoleModal(true) }}>{t('rolePermission.create')}</Button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 20 }}>
        {roles.map((r) => {
          const isAdmin = r.is_system === 1
          return (
            <div key={r.id} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 12, padding: 24 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <span style={{ fontSize: 16, fontWeight: 600 }}>{r.name}{isAdmin ? t('rolePermission.systemSuffix', ' (系统)') : ''}</span>
                <span style={{ fontSize: 13, color: '#64748b' }}><TeamOutlined /> {r.description || t('common.noDescription')}</span>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16, minHeight: 32 }}>
                {isAdmin ? <Tag style={{ background: '#eff6ff', color: '#3b82f6', border: 'none', borderRadius: 6, padding: '4px 12px' }}>{t('rolePermission.allPermissions', '全部权限')}</Tag> : <Tag style={{ background: '#f1f5f9', color: '#475569', border: 'none' }}>{t('rolePermission.clickToEdit', '点击编辑配置权限')}</Tag>}
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <Button type="primary" size="small" icon={<EditOutlined />} onClick={() => loadPerms(r)}>{t('rolePermission.assignPermission')}</Button>
              </div>
            </div>
          )
        })}
      </div>

      <Modal title={`${t('rolePermission.assignPermission')} - ${permModal?.role.name}`} open={!!permModal} onCancel={() => setPermModal(null)} onOk={handleSavePerms} okText={t('common.save')} cancelText={t('common.cancel')} width={600}>
        <Checkbox.Group value={permModal?.checked} onChange={v => setPermModal(p => p ? { ...p, checked: v as number[] } : null)} style={{ width: '100%' }}>
          {perms.map(p => (
            <div key={p.id} style={{ marginBottom: 8 }}>
              <Checkbox value={p.id}>
                <strong>{p.name}</strong>
                <span style={{ color: '#94a3b8', marginLeft: 8, fontSize: 12 }}>{p.resource}:{p.action}</span>
              </Checkbox>
            </div>
          ))}
        </Checkbox.Group>
      </Modal>

      <Modal title={t('rolePermission.create')} open={newRoleModal} onCancel={() => setNewRoleModal(false)} onOk={handleCreateRole} okText={t('rolePermission.create')} cancelText={t('common.cancel')}>
        <Input placeholder={t('rolePermission.roleName')} value={newRoleName} onChange={e => setNewRoleName(e.target.value)} />
      </Modal>
    </div>
  )
}