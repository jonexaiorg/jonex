import React, { useEffect, useState } from 'react';
import { I18nextProvider, useTranslation } from 'react-i18next';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import { antdTheme } from '@jonex/platform-theme';
import i18n from '@/locales/i18n';
import AppRoute from '@/router';

/** 位于 I18nextProvider 内，响应语言变化更新 Ant Design locale */
function AntdGate({ children }: { children: React.ReactNode }) {
  const { i18n: appI18n } = useTranslation();
  const antdLocale = appI18n.language === 'zh' ? zhCN : enUS;
  // cssVar 关闭：antd v5 cssVar 模式下 popup 的 z-index 走 CSS 变量下发
  // (--ant-*-z-index-popup)，懒加载 chunk 挂载会打乱 cssinjs 变量插入顺序、
  // 导致变量丢失 → z-index 解析为 auto、弹层被内容盖住。关掉后 antd 把
  // z-index 等 token 直接编成静态值，永不丢失（各 popup 层叠仍由 antd 算对）。
  return (
    <ConfigProvider locale={antdLocale} theme={{ ...antdTheme }}>
      {children}
    </ConfigProvider>
  );
}

/**
 * 监听来自 Shell 的语言切换事件：
 * - `jonex:locale-change` CustomEvent（Module Federation 同 window 模式）
 * - `message` postMessage（iframe standalone fallback 模式）
 * 确保 iframe 内的子应用也能实时切换语言。
 */
function GlobalLocaleListener() {
  const { i18n: appI18n } = useTranslation();
  const [, forceRender] = useState(0);

  useEffect(() => {
    // CustomEvent（同 window）
    const onCustomEvent = (e: CustomEvent<string>) => {
      appI18n.changeLanguage(e.detail);
      forceRender((n) => n + 1);
    };
    // postMessage（iframe 跨域/跨窗口）
    const onMessage = (e: MessageEvent) => {
      if (e.data?.type === 'jonex:locale-change') {
        appI18n.changeLanguage(e.data.locale);
        forceRender((n) => n + 1);
      }
    };
    window.addEventListener('jonex:locale-change', onCustomEvent as EventListener);
    window.addEventListener('message', onMessage);
    return () => {
      window.removeEventListener('jonex:locale-change', onCustomEvent as EventListener);
      window.removeEventListener('message', onMessage);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return null;
}

export default function App() {
  return (
    <I18nextProvider i18n={i18n}>
      <GlobalLocaleListener />
      <AntdGate>
        <AppRoute mode="standalone" />
      </AntdGate>
    </I18nextProvider>
  );
}
