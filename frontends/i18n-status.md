# Frontend i18n Status Tracking

> Project: jonex-platform
> Updated: 2026-07-15

---

## Architecture

```
@jonex/i18n-resources (shared translation resource package)
  ├── src/locales/zh.json      ← Shared Chinese dictionary
  ├── src/locales/en.json      ← Shared English dictionary
  └── src/index.ts             ← createI18nInstance() factory function

Shell (@jonex/shell)
  └── src/locales/i18n.ts      ← Directly references i18n-resources/locales/*.json

Sub-apps (core-business / platform-management / ecosystem-management)
  ├── src/locales/zh.json      ← Business-specific Chinese dictionary
  ├── src/locales/en.json      ← Business-specific English dictionary
  └── src/locales/i18n.ts      ← Calls createI18nInstance({ resources: business-specific dictionaries })
```

- Shell and sub-apps each have independent `i18next` instances (Module Federation sandbox isolation)
- Shell notifies sub-apps of language switching via `window.dispatchEvent(new CustomEvent('jonex:locale-change'))`
- Sub-apps listen for language switching via `window.addEventListener('jonex:locale-change', ...)`
- Route titles and menu labels are treated as i18n keys, resolved via `t()` / `i18next.t()` at render time

---

## Completed (✅)

### Shell Global Navigation

| File | Changes |
|---|---|
| `shared/i18n-resources/src/locales/zh.json` | Added `navigation.*` (20 keys) and `space.*` (2 keys) |
| `shared/i18n-resources/src/locales/en.json` | Corresponding English translations |
| `shell/src/navigation/prototypeNav.config.ts` | All `label` changed from Chinese to `'navigation.xxx'` key paths |
| `shell/src/components/AppShellLayout/index.tsx` | Navigation labels and breadcrumb titles all use `t()` |
| `shell/src/components/SpaceSwitcher/index.tsx` | `'选择领域空间'` / `'添加领域空间'` use `t()` |
| `shell/src/navigation/navUtils.ts` | `'首页'` → `'navigation.home'` |

### Shell Pages

| Page | Status |
|---|---|
| Login | ✅ Uses `useTranslation()` and `t()` |
| Dashboard | ✅ Uses `useTranslation()` and `t()` |

### Infrastructure

| File | Description |
|---|---|
| `Dockerfile` (all 4) | Added `i18n-resources` package COPY to fix Docker build failures |

### P4 — Clean up sub-app template legacy keys

Removed `auth`, `reset`, `language` and other template legacy blocks from all 3 sub-apps' `zh.json`/`en.json`.
`site.title` changed from `"React 起始脚手架"` to `""` (falls back to shared resource `"Jonex平台"`).

### P5 — HeaderNav locale.tsx

All sub-app `HeaderNav/locale.tsx` files have been deleted with no remaining references.

### Locale Files (P3 — All Complete)

All 3 sub-apps' `zh.json`/`en.json` have completed business translation keys:

| Sub-app | Translation Key Namespace | Status |
|---|---|---|
| `core-business` | `domainKnowledge.*`, `domainSpace.*`, `knowledgeSearch.*`, `domainService.*`, `dataSource.*`, `domainEngine.*`, `domainGraph.*`, `compile.*`, `synonym.*`, `ontology.*`, `permission.*`, `validation.*`, `knowledgeTracking.*`, `documentViewer.*`, `spaceSwitcher.*`, `home.*`, `sync.*`, `status.*` | ✅ |
| `platform-management` | `home.*`, `modelAdapter.*`, `tenantManagement.*`, `userManagement.*`, `rolePermission.*`, `taskSchedule.*`, `systemConfig.*`, `operationLog.*`, `dataAccess.*`, `parserManagement.*`, `knowledgeCompile.*`, `status.*` | ✅ |
| `ecosystem-management` | `adapter.*`, `skill.*`, `businessMarketplace.*`, `promptTemplate.*`, `templateDomain.*`, `templateScenario.*`, `templateObject.*`, `templateRelation.*`, `status.*` | ✅ |

### Route/Menu/Layout Refactoring

| Sub-app | routes.config.ts | menu.config.ts | BasicLayout t() | HeaderNav t() |
|---|---|---|---|---|
| `core-business` | ✅ | ✅ | ✅ | ✅ (completed earlier) |
| `platform-management` | ✅ | ✅ | ✅ | ✅ (completed earlier) |
| `ecosystem-management` | ✅ | ✅ | ✅ | ✅ (completed earlier) |

---

## In Progress (🔄)

### P1 — Component-level Hardcoded Chinese Replacement

Automated and semi-automated scripts have processed **113 source files** (4371 lines added / 1853 lines deleted).

Remaining hardcoded Chinese strings:

| Sub-app | Replaced | Remaining | Total |
|---|---|---|---|
| `core-business` | ~345 | ~422 (38 files) | 767 |
| `platform-management` | ~63 | ~143 (16 files) | 206 |
| `ecosystem-management` | ~190 | ~15 (3 files) | 205 |

Remaining work characteristics:
- **types/ type definitions**: `ValidationSeverity = '高' | '中' | '低'` etc. — TypeScript type literals cannot be replaced with `t()` directly; keep type definitions unchanged and use mapping tables at render time
- **Compile-related pages** (`compile/constants.ts`, `CompileTab.tsx` etc.): Many Chinese labels/enum values need systematic handling
- **domainKnowledge/api mapping tables**: Property types, cardinality, etc. Chinese↔English mappings
- **Batch operation messages**: `message.success(\`导入 ${v3} 条\`)` etc. — template strings containing JSX

---

## Modification Guide

### Adding New Translation Keys

```json
// i18n-resources (shared): shared/i18n-resources/src/locales/zh.json
// Sub-app specific: frontends/<app>/src/locales/zh.json
{
  "yourFeature": {
    "title": "Your Feature",
    "description": "Feature description"
  }
}
```

### Using in Components

```tsx
import { useTranslation } from 'react-i18next'

function MyComponent() {
  const { t } = useTranslation()
  return <h1>{t('yourFeature.title')}</h1>
}
```

### Using in Non-Component Modules

```typescript
import i18n from '@/locales/i18n'
// ...
new Error(i18n.t('common.loadFailed'))
```

### Language Switching Events

Shell notifies all sub-apps via CustomEvent; no manual handling required.

---

## Translation Key Naming Convention

| Prefix | Usage | Example |
|---|---|---|
| `common.*` | Generic CRUD operations, global prompts | `common.saveSuccess`, `common.loadFailed` |
| `status.*` | Status labels | `status.enabled`, `status.active` |
| `rules.*` | Form validation rules | `rules.required`, `rules.email` |
| `error.*` | Error pages and messages | `error.404`, `error.network` |
| `{module}.*` | Module-level business translations | `domainKnowledge.title`, `modelAdapter.list` |
