import React from 'react'
import { Button, Dropdown } from 'antd'
import { GlobalOutlined, CaretDownOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { LANGUAGE_OPTIONS, LANGUAGE_STORAGE_KEY } from '@jonex/i18n-resources'

interface LocaleSwitcherProps {
  onLocaleChange?: (locale: string) => void
}

export default function LocaleSwitcher({ onLocaleChange }: LocaleSwitcherProps) {
  const { t, i18n } = useTranslation()

  const handleChange = (locale: string) => {
    if (locale === i18n.language) return
    i18n.changeLanguage(locale)
    localStorage.setItem(LANGUAGE_STORAGE_KEY, locale)

    // 通知同 window 的子应用（Module Federation 托管模式）
    window.dispatchEvent(new CustomEvent('jonex:locale-change', { detail: locale }))

    // 通知 iframe 中的子应用（standalone fallback 模式）
    const iframes = document.querySelectorAll('iframe')
    iframes.forEach((iframe) => {
      if (iframe.contentWindow) {
        iframe.contentWindow.postMessage(
          { type: 'jonex:locale-change', locale },
          '*',
        )
      }
    })

    onLocaleChange?.(locale)
  }

  const currentOption = LANGUAGE_OPTIONS.find((o) => o.value === i18n.language)
  const currentLabel = currentOption
    ? t(`language.${currentOption.value}`, { defaultValue: currentOption.label })
    : i18n.language

  const items = LANGUAGE_OPTIONS.filter((o) => o.value !== i18n.language).map((opt) => ({
    key: opt.value,
    label: t(`language.${opt.value}`, { defaultValue: opt.label }),
  }))

  return (
    <Dropdown
      menu={{
        items,
        onClick: ({ key }) => handleChange(key),
      }}
      placement="bottomRight"
      trigger={['click']}
    >
      <Button
        type="text"
        style={{
          height: 38, borderRadius: 10,
          display: 'flex', alignItems: 'center', gap: 4,
          fontSize: 14, color: 'inherit', padding: '0 10px',
        }}
      >
        <GlobalOutlined style={{ fontSize: 16 }} />
        <span>{currentLabel}</span>
        <CaretDownOutlined style={{ fontSize: 10, color: '#94a3b8' }} />
      </Button>
    </Dropdown>
  )
}
