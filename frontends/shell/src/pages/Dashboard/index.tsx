import React from 'react'
import { Typography } from 'antd'
import { useTranslation } from 'react-i18next'
import { getUser } from '../../api/auth'

const { Title, Text } = Typography

export default function Dashboard() {
  const { t } = useTranslation()
  const user = getUser()
  const displayName = user?.displayName || user?.username || ''

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100%',
        minHeight: 'calc(100vh - var(--yx-topbar-height, 64px) - 2 * var(--yx-content-padding-y, 28px))',
        textAlign: 'center',
      }}
    >
      <Title
        level={2}
        style={{
          fontSize: 28,
          fontWeight: 700,
          color: 'var(--yx-brand-dark, #0b2b5c)',
          marginBottom: 12,
        }}
      >
        {displayName}，{t('site.title')}
      </Title>
      <Text
        style={{
          fontSize: 16,
          color: 'var(--yx-text-secondary, #64748b)',
        }}
      >
        {t('site.subtitle')}
      </Text>
    </div>
  )
}