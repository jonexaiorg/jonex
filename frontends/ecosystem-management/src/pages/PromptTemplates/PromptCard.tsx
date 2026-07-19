import React, { useCallback } from 'react'
import { message, Tooltip } from 'antd'
import { useTranslation } from 'react-i18next'
import { CopyOutlined, DeleteOutlined, EditOutlined, EyeOutlined, BranchesOutlined } from '@ant-design/icons'
import type { PromptTemplateItem } from '../../api/promptTemplates'
import { CATEGORY_ICON_MAP } from '../../api/promptTemplates'

interface PromptCardProps {
  template: PromptTemplateItem
  onEdit: (id: string) => void
  onView: (id: string) => void
  onDelete: (id: string) => void
  onVersion: (id: string) => void
  onCopy: (id: string) => void
}

function getCurrentContent(t: PromptTemplateItem): string {
  const versions = t.versions_json || []
  return versions.length > 0 ? versions[0].content : ''
}

function escapeHtml(s: string | null | undefined): string {
  if (!s) return ''
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

const PromptCard: React.FC<PromptCardProps> = ({
  template, onEdit, onView, onDelete, onVersion, onCopy,
}) => {
  const { t } = useTranslation()
  const categoryInfo = CATEGORY_ICON_MAP[template.category] || CATEGORY_ICON_MAP['promptTemplate.categories.other']
  const isSystem = template.scope === 'system'
  const content = getCurrentContent(template)
  const previewHtml = escapeHtml(content).replace(/\n/g, '<br>')

  const handleCopyContent = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    navigator.clipboard.writeText(content).then(
      () => message.success(t('promptTemplate.copySuccess')),
      () => message.error(t('common.operationFailed')),
    )
  }, [content, t])

  const handleCopyTemplate = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    onCopy(template.id)
  }, [template.id, onCopy])

  return (
    <div className="pt-card">
      { }
      {!isSystem && (
        <span className={`pt-status ${template.status === '启用' ? 'on' : 'off'}`}>
          {template.status}
        </span>
      )}

      { }
      <div className="pt-card-top">
        <div className="pt-icon" style={{ background: categoryInfo.bg }}>
          {categoryInfo.icon}
        </div>
        <div className="pt-meta">
          <h3 className="pt-name">{template.name}</h3>
          <div className="pt-desc">{template.description || t('common.noDescription')}</div>
        </div>
      </div>

      { }
      <div className="pt-preview">
        <div dangerouslySetInnerHTML={{ __html: previewHtml }} />
      </div>

      { }
      <div className="pt-tags">
        <span className={`pt-scope-badge ${isSystem ? 'system' : 'domain'}`}>
          {isSystem ? `🌐 ${t('promptTemplate.systemScope')}` : `📦 ${t('promptTemplate.domainScope')}`}
        </span>
        <span className="pt-tag-cat">{t(template.category)}</span>
        <span className="pt-ver-badge">🔀 v{template.current_version || '1.0'}</span>
      </div>

      { }
      <div className="pt-actions">
        {isSystem ? (
          <>
            <Tooltip title={t('promptTemplate.viewInfo')}>
              <button className="pt-btn-view" onClick={() => onView(template.id)}>
                <EyeOutlined /> {t('promptTemplate.view')}
              </button>
            </Tooltip>
            <Tooltip title={t('promptTemplate.copyToTenant')}>
              <button className="pt-btn-copy" onClick={handleCopyTemplate}>
                <CopyOutlined /> {t('promptTemplate.copy')}
              </button>
            </Tooltip>
            <Tooltip title={t('promptTemplate.copyText')}>
              <button className="pt-btn-copy-text" onClick={handleCopyContent}>
                <CopyOutlined /> {t('promptTemplate.copyText')}
              </button>
            </Tooltip>
          </>
        ) : (
          <>
            <Tooltip title={t('promptTemplate.edit')}>
              <button className="pt-btn-edit" onClick={() => onEdit(template.id)}>
                <EditOutlined /> {t('promptTemplate.edit')}
              </button>
            </Tooltip>
            <Tooltip title={t('promptTemplate.copyToTenant')}>
              <button className="pt-btn-copy" onClick={handleCopyTemplate}>
                <CopyOutlined /> {t('promptTemplate.copy')}
              </button>
            </Tooltip>
            <Tooltip title={t('promptTemplate.version')}>
              <button className="pt-btn-ver" onClick={() => onVersion(template.id)}>
                <BranchesOutlined /> {t('promptTemplate.version')}
              </button>
            </Tooltip>
            <Tooltip title={t('promptTemplate.delete')}>
              <button className="pt-btn-del" onClick={() => onDelete(template.id)}>
                <DeleteOutlined /> {t('promptTemplate.delete')}
              </button>
            </Tooltip>
          </>
        )}
      </div>
    </div>
  )
}

export default React.memo(PromptCard)
