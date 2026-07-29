import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Spin, Result, Button } from 'antd';
import { CloudOutlined, FolderOpenOutlined, UploadOutlined, WifiOutlined, ApiOutlined } from '@ant-design/icons';
import { colors } from '@jonex/platform-theme/tokens';
import { listDataAccessMethods, type DataAccessItem } from '../../api/dataAccess';
import './index.css';

const BUILT_IN_ACCESS_METHOD_IDS = new Set([
  'dam_demo_api',
  'dam_api_push_demo',
  'dam_demo_storage',
  'dam_demo_file',
  'dam_demo_mqtt',
]);

function getTypeIcons(
  t: (key: string, options?: Record<string, unknown>) => string,
): Record<string, { icon: React.ReactNode; label: string; desc: string }> {
  return {
    api: { icon: <CloudOutlined />, label: t('dataSource.apiAccess'), desc: t('dataSource.apiAccessDesc') },
    api_push: { icon: <ApiOutlined />, label: t('dataSource.apiPushAccess'), desc: t('dataSource.apiPushAccessDesc') },
    storage: {
      icon: <FolderOpenOutlined />,
      label: t('dataSource.storageAccess'),
      desc: t('dataSource.storageAccessDesc'),
    },
    file: {
      icon: <UploadOutlined />,
      label: t('dataSource.fileUploadAccess'),
      desc: t('dataSource.fileUploadAccessDesc'),
    },
    mqtt: { icon: <WifiOutlined />, label: t('dataSource.mqttAccess'), desc: t('dataSource.mqttAccessDesc') },
  };
}

export default function DataAccess() {
  const { t } = useTranslation();
  const [items, setItems] = useState<DataAccessItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const typeIcons = React.useMemo(() => getTypeIcons(t), [t]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listDataAccessMethods(0, 100);
      setItems(result.items);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('dataSource.loadFailed'));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
        <Spin size="large" />
      </div>
    );
  }
  if (error) {
    return (
      <Result
        status="error"
        title={t('dataSource.loadFailed')}
        subTitle={error}
        extra={
          <Button type="primary" onClick={load}>
            {t('common.retry')}
          </Button>
        }
      />
    );
  }

  return (
    <div>
      <div className="yx-page-title">
        <h1 style={{ fontSize: 22, fontWeight: 700, color: colors.brandDark, margin: 0 }}>
          {t('dataSource.pageTitle')}
        </h1>
      </div>
      <div className="access-grid">
        {items.map((item) => {
          const cfg = typeIcons[item.access_type] || { icon: <CloudOutlined />, label: item.access_type, desc: '' };
          const isActive = item.status === 'active';
          const isBuiltIn = BUILT_IN_ACCESS_METHOD_IDS.has(item.id);

          return (
            <div key={item.id} className={`access-card${isActive ? ' active' : ' grey'}`}>
              <div className="icon-big">{cfg.icon}</div>
              <h3>{isBuiltIn ? cfg.label : item.name}</h3>
              <p>{isBuiltIn ? cfg.desc : item.description || cfg.desc}</p>
              <span className="status-tag">
                {isActive ? (
                  <>
                    <span className="dot-green" /> {t('dataSource.enabled')}
                  </>
                ) : (
                  t('dataSource.comingSoon')
                )}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
