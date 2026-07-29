import React from 'react';
import { Button, Dropdown } from 'antd';
import { GlobalOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useStore } from '@/store';

export default function HeaderNav() {
  const { global } = useStore();
  const { i18n, t } = useTranslation();

  const handleUpdateLocale = async (locale: string) => {
    global.setLocale(locale);
    i18n.changeLanguage(locale);
  };

  const items = [
    { key: 'zh', label: t('language.chinese') },
    { key: 'en', label: t('language.english') },
  ];

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
        {global.locale === 'zh' ? t('language.chinese') : t('language.english')}
      </Button>
    </Dropdown>
  );
}
