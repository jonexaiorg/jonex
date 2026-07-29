import { createI18nInstance } from '@jonex/i18n-resources';
import zhLocales from '@/locales/zh.json';
import enLocales from '@/locales/en.json';

/**
 * 使用共享 i18n-resources 的 createI18nInstance 创建实例：
 * 1. 自动加载共享 locale 资源（common, auth, error, navigation 等）
 * 2. 通过 deepMergeTranslations 合并本项目特有资源
 * 3. 从正确的 storage key（jonex_locale）读取初始语言
 */
const i18n = createI18nInstance({
  resources: {
    zh: { translation: zhLocales },
    en: { translation: enLocales },
  },
});

export default i18n;
