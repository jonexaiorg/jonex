import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Dropdown, Spin } from 'antd';
import { DownOutlined, SettingOutlined, PlusOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useStore } from '@/store';
import styles from './index.module.scss';

interface SpaceSwitcherProps {
  collapsed?: boolean;
}

const SpaceSwitcher = ({ collapsed }: SpaceSwitcherProps) => {
  const { global } = useStore();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const currentName = global.currentSpace?.name || t('domainSpace.selectSpace');

  const handleSelect = (spaceId: string) => {
    global.setCurrentSpaceId(spaceId, { persist: true, broadcast: true });
    setDropdownOpen(false);
  };

  const handleAddSpace = () => {
    setDropdownOpen(false);
    // 跳转到独立新建页面，创建成功后跳转设置页
    navigate('/domain-space/new');
  };

  const handleGear = () => {
    setDropdownOpen(false);
    navigate(global.currentSpaceId ? `/domain-space/${global.currentSpaceId}/settings` : '/domain-space');
  };

  // 折叠态只显示首个字母
  if (collapsed) {
    return (
      <div className={styles['switcher-collapsed']} title={currentName}>
        <span className={styles['collapsed-char']}>{currentName.charAt(0).toUpperCase()}</span>
      </div>
    );
  }

  const items = [
    ...(global.spacesLoaded
      ? global.spaces.map((s) => ({
          key: s.id,
          label: <span className={s.id === global.currentSpaceId ? styles['dropdown-item-active'] : ''}>{s.name}</span>,
          onClick: () => handleSelect(s.id),
        }))
      : []),
    { type: 'divider' as const },
    {
      key: 'add-space',
      label: (
        <span style={{ color: '#3b82f6' }}>
          <PlusOutlined style={{ marginRight: 6 }} />
          {t('domainSpace.addSpace')}
        </span>
      ),
      onClick: handleAddSpace,
    },
  ];

  return (
    <div className={styles.switcher}>
      <Dropdown
        menu={{ items }}
        open={dropdownOpen}
        onOpenChange={setDropdownOpen}
        trigger={['click']}
        placement="bottomLeft"
        styles={{ root: { minWidth: 200 } }}
      >
        <div className={styles['switcher-trigger']} onClick={() => setDropdownOpen(!dropdownOpen)}>
          {global.spacesLoading && !global.spacesLoaded ? (
            <Spin size="small" />
          ) : (
            <>
              <span className={styles['switcher-name']}>{currentName}</span>
              <DownOutlined className={styles['switcher-arrow']} />
            </>
          )}
        </div>
      </Dropdown>
      <span className={styles['switcher-gear']} onClick={handleGear}>
        <SettingOutlined />
      </span>
    </div>
  );
};

export default SpaceSwitcher;
