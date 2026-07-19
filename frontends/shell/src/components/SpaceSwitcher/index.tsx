import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Dropdown, Spin } from 'antd'
import {
  DownOutlined,
  SettingOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import {
  readPersistedSpaceId,
  broadcastSpaceChange,
  onSpaceChanged,
  onSpacesInvalidated,
} from '@jonex/shell-sdk'
import { fetchSpaces, type ShellSpaceItem } from '../../api/spaces'

const S: Record<string, React.CSSProperties> = {
  switcher: {
    display: 'flex', alignItems: 'center', padding: '8px 12px',
    margin: '0 8px 8px', background: '#f1f5f9',
    borderRadius: 8, gap: 6,
  },
  trigger: {
    flex: 1, display: 'flex', alignItems: 'center', gap: 6,
    cursor: 'pointer', minWidth: 0,
  },
  name: {
    flex: 1, fontSize: 13, fontWeight: 500, color: '#475569',
    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const,
  },
  arrow: { fontSize: 10, color: '#94a3b8', flexShrink: 0 },
  gear: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    width: 24, height: 24, borderRadius: 4, cursor: 'pointer',
    color: '#94a3b8', fontSize: 13, flexShrink: 0,
  },
  collapsed: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    padding: '8px 0', margin: '0 8px 8px', cursor: 'pointer',
  },
  collapsedChar: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    width: 32, height: 32, borderRadius: 8,
    background: '#f1f5f9', color: '#475569',
    fontSize: 16, fontWeight: 600,
  },
  activeItem: { color: '#3b82f6', fontWeight: 500 },
  addItem: { color: '#3b82f6' },
}

interface SpaceSwitcherProps {
  collapsed?: boolean
}

const SpaceSwitcher: React.FC<SpaceSwitcherProps> = ({ collapsed }) => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [spaces, setSpaces] = useState<ShellSpaceItem[]>([])
  const [currentId, setCurrentId] = useState<string | null>(
    readPersistedSpaceId,
  )
  const [loading, setLoading] = useState(true)
  const [dropdownOpen, setDropdownOpen] = useState(false)

  const reloadSpaces = useCallback(async () => {
    try {
      const list = await fetchSpaces()
      setSpaces(list)
      const persisted = readPersistedSpaceId()
      setCurrentId((prev) =>
        persisted
          ? list.some((s: ShellSpaceItem) => s.id === persisted)
            ? persisted
            : list[0]?.id ?? null
          : prev,
      )
    } catch {

    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    reloadSpaces()

    const unsubChanged = onSpaceChanged((spaceId: string | null) => {
      setCurrentId(spaceId)
      if (spaceId && !spaces.some((s: ShellSpaceItem) => s.id === spaceId)) {
        reloadSpaces()
      }
    })
    const unsubInvalidated = onSpacesInvalidated(() => reloadSpaces())

    return () => {
      unsubChanged()
      unsubInvalidated()
    }
  }, [reloadSpaces])

  const currentName =
    spaces.find((s: ShellSpaceItem) => s.id === currentId)?.name || t('space.select')

  const handleSelect = (spaceId: string) => {
    setCurrentId(spaceId)
    broadcastSpaceChange(spaceId)
    setDropdownOpen(false)
  }

  const handleGear = () => {
    setDropdownOpen(false)
    navigate(
      currentId
        ? `/apps/core-business/domain-space/${currentId}/settings`
        : '/apps/core-business/domain-space',
    )
  }

  const handleAddSpace = () => {
    setDropdownOpen(false)
    navigate('/apps/core-business/domain-space/new')
  }

  if (collapsed) {
    return (
      <div style={S.collapsed} title={currentName}>
        <span style={S.collapsedChar}>
          {currentName.charAt(0).toUpperCase()}
        </span>
      </div>
    )
  }

  const items = [
    ...spaces.map((s: ShellSpaceItem) => ({
      key: s.id,
      label: (
        <span style={s.id === currentId ? S.activeItem : undefined}>
          {s.name}
        </span>
      ),
      onClick: () => handleSelect(s.id),
    })),
    { type: 'divider' as const },
    {
      key: 'add-space',
      label: (
        <span style={S.addItem}>
          <PlusOutlined style={{ marginRight: 6 }} />
          {t('space.add')}
        </span>
      ),
      onClick: handleAddSpace,
    },
  ]

  return (
    <div style={S.switcher}>
      <Dropdown
        menu={{ items }}
        open={dropdownOpen}
        onOpenChange={setDropdownOpen}
        trigger={['click']}
        placement="bottomLeft"
        styles={{ root: { minWidth: 200 } }}
      >
        <div style={S.trigger} onClick={() => setDropdownOpen(!dropdownOpen)}>
          {loading ? (
            <Spin size="small" />
          ) : (
            <>
              <span style={S.name}>{currentName}</span>
              <DownOutlined style={S.arrow} />
            </>
          )}
        </div>
      </Dropdown>
      <span style={S.gear} onClick={handleGear}>
        <SettingOutlined />
      </span>
    </div>
  )
}

export default SpaceSwitcher
