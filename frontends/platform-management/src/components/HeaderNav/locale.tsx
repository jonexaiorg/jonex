import React from 'react'
import { Button, Dropdown } from 'antd'
import { GlobalOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { useStore } from '@/store'

export default function HeaderNav() {
  const { global } = useStore()
  const { i18n } = useTranslation()

  const handleUpdateLocale = async (locale: string) => {
    global.setLocale(locale)
    i18n.changeLanguage(locale)
  }

  const items = [
    { key: 'zh', label: 'cn 中文' },
    { key: 'en', label: 'us English' },
  ]

  return (
    <Dropdown
      menu={{
        items,
        selectedKeys: [global.locale],
        onClick: ({ key }) => handleUpdateLocale(key),
      }}
      placement="bottomRight"
      trigger={['click']}
    >
      <Button icon={<GlobalOutlined />}>
        {global.locale === 'zh' ? 'cn 中文' : 'us English'}
      </Button>
    </Dropdown>
  )
}
