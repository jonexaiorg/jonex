# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Commands

```bash
pnpm install          # Install dependencies
pnpm dev              # Start dev server
pnpm build            # Production build
pnpm preview          # Preview production build
```

## Architecture

This is a **React 18 + Vite** starter scaffold for building micro-frontend sub-applications in the Jonex Platform. It supports two runtime modes:

- **standalone** — runs independently with its own header, navigation, and auth
- **hosted** — mounted by the shell via Module Federation, uses shell-provided auth and layout

### Tech Stack
- React 18, React Router v6 (BrowserRouter for standalone, MemoryRouter for hosted)
- Ant Design 6 with @ant-design/icons
- MobX for state management (mobx-react-lite)
- i18next + react-i18next (Chinese/English)
- Axios for HTTP requests
- Module Federation via @originjs/vite-plugin-federation

### Placeholder Variables

Files contain `{{PLACEHOLDER}}` variables that are replaced at onboarding time:

| Placeholder | Example | Description |
|---|---|---|
| `` | `@jonex/example-app` | npm package name |
| `` | `Example App` | Display title |
| `` | `exampleApp` | Module Federation scope |
| `` | `/example/` | Vite base path |
| `` | `example` | Nginx serve directory |
| `` | `/api/v1/example` | Backend API proxy prefix |
| `` | `5173` | Vite dev server port |
| `` | `example` | Shell manifest app ID |

### Directory Structure

- `src/api/` — API endpoint definitions
- `src/components/` — Reusable components (AppLayout, BasicLayout, HostedLayout, HeaderNav)
- `src/hooks/` — Custom hooks (useDocumentTitle, usePageMeta, useIsMobile)
- `src/locales/` — i18n translation files (zh.json, en.json)
- `src/pages/` — Page components (Home, NotFound)
- `src/remote/RemoteApp.jsx` — Module Federation mount entry
- `src/router/` — Route config, menu config, router with auth guard
- `src/store/` — MobX stores (global locale, userInfo)
- `src/styles/index.scss` — Global styles
- `src/utils/` — Utilities (loadable, storage, menu, safeMessage)
- `src/App.jsx` — Standalone entry point
- `src/main.jsx` — Dual-mode bootstrap (standalone vs hosted)

### Adding a New Page

1. Create page component in `src/pages/`
2. Add route in `src/router/routes.config.js`
3. Add menu item in `src/router/menu.config.js` (if standalone mode)
4. Add translations to `src/locales/zh.json` and `src/locales/en.json`
