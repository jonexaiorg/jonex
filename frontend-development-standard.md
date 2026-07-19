# Jonex Platform Frontend Development Standard

> This standard is the default creation standard for new frontend sub-applications, new pages, and new features. The current codebase evolves toward the final ideal state without retaining backward-compatible designs; legacy implementations should be gradually migrated to the structures and contracts defined here.

## 1. General Principles

- **Single Entry**: The browser always enters through `frontend-gateway`; the production environment only exposes port 80/443. The frontend must not directly connect to capability services, Sidecar, or container ports.
- **Shell Owns the Platform Experience**: `frontends/shell` handles login, workspace, navigation, application loading, permission guards, context injection, and cross-application events.
- **Sub-applications Own Business Logic**: Each business sub-application only maintains its own pages, routes, service encapsulation, state, and business components.
- **Application Registry is the Source of Truth**: Frontend applications, routes, remote entries, menu visibility, health checks, and version metadata are provided by the platform service; static manifests may only be used as a local development bootstrap, not as a production standard.
- **API Uniformly Uses `/api/v1/**`**: All new interfaces and refactored legacy interfaces must go through the Gateway standard path, e.g., `/api/v1/knowledge-base/**`, `/api/v1/platform/**`.
- **Tenant Comes from Authentication Context**: Regular business forms, URLs, and request bodies should not declare `tenant_id`; the tenant is resolved uniformly by the authentication state, Sidecar, and backend services.
- **Shared Capabilities Come First**: Theme, auth storage, ShellContext, navigation, events, and shared types go into `frontends/shared` and must not be duplicated across sub-applications.
- **Type First**: New code defaults to TypeScript; API input/output parameters, route metadata, page state, and component props must all have explicit types.
- **Complete States**: Remote data pages must cover loading, empty, error, success, and refresh states; blank screens or silent failures must not be the default experience.

## 2. Frontend Workspace Standards

`frontends/` is a pnpm workspace monorepo:

```text
frontends/
  shell/                         # Shell application, unified entry and application host
  core-business/                 # Core business sub-application
  platform-management/           # Platform management sub-application
  ecosystem-management/          # Ecosystem management sub-application
  dev-gateway/                   # Local unified entry and reverse proxy
  shared/
    platform-theme/              # Platform tokens, Ant Design theme, layout styles
    shell-sdk/                   # Auth storage, ShellContext, navigation, events, shared types
  _template/                     # New TypeScript sub-application template
```

Unified commands are executed from the `frontends/` root directory:

```bash
pnpm install
pnpm run typecheck
pnpm run build
pnpm run dev:gateway
pnpm run dev:shell
pnpm run dev:core-business
```

Adding or refactoring modules follows these rules:

- Business sub-applications go in `frontends/{app-id}`, using kebab-case for `app-id`.
- Shared libraries go in `frontends/shared/{package-name}`, only carrying capabilities reused by two or more applications.
- Workspace package names uniformly use `@jonex/{app-id}` or `@jonex/{package-name}`.
- The workspace root `frontends/package.json` is the unified script entry point for the frontend; sub-applications no longer define cross-application orchestration commands on their own.
- Sub-applications must declare `engines.node >= 20.18.0`, `engines.pnpm >= 9.0.0`.
- Sub-application required scripts: `dev`, `build`, `preview`, `typecheck`, `lint`.
- Shared library required scripts: `typecheck`; if the output is consumed by a build, `build` should be provided.

### 2.1 Environment Variables

Each sub-application root directory contains two environment files:

| File | Purpose | Git |
|---|---|---|
| `.env` | Actual environment variables used for local development | Not committed (ignored via `.gitignore`) |
| `.env.example` | Environment variable template: variable names match `.env`, values use only safe defaults or placeholders | Committed to repository |

**Must copy before starting local development**:

```bash
cd frontends/{app-id}
cp .env.example .env
```

`.env.example` includes default values needed for local development: `VITE_APP_ID` (application identifier), `VITE_STANDALONE_BASE` (standalone route prefix), `VITE_LOGIN` (Shell login page URL), `VITE_AUTH_ME` / `VITE_AUTH_EXCHANGE_TICKET` (authentication interface paths). Some sub-applications' `.env.example` also includes `VITE_USE_MOCK=true`, enabling mock data when no backend is available locally.

`.env.example` must not contain real tokens, passwords, intranet addresses, or production domain names. Production builds must disable mock data and inject public runtime configuration through the deployment environment or Gateway.

When adding a new sub-application, both `.env` and `.env.example` must be created simultaneously, and `frontends/.gitignore` must be verified to ignore `.env` while not ignoring `.env.example`.

## 3. Sub-application Directory Standards

New sub-applications are created from `frontends/_template` by default and organized into the following structure:

```text
src/
  app/                           # Application-level Provider, bootstrap configuration, error boundaries
  router/                        # Routes, menus, page metadata
  remote/                        # Module Federation mount entry
  pages/                         # Route pages, responsible only for page orchestration
  features/                      # Complex business feature modules
  components/                    # Reusable components within the current application
  services/                      # API client, business request functions, DTO mapping
  stores/                        # Cross-page client state
  hooks/                         # Composition logic
  types/                         # Type definitions for the current application
  utils/                         # Pure function utilities
  locales/                       # i18n resources
  styles/                        # Application-level style entry
```

Responsibility boundaries:

- `pages/` is responsible for page layout, data hook composition, and modal toggles; it should not contain scattered `fetch`, `axios`, or complex business rules.
- `services/` is responsible for request encapsulation, DTO naming, response envelope parsing, and error normalization.
- `features/` hosts cross-component business processes such as wizards, batch operations, complex editors, and long-running task panels.
- `components/` should not read global login state or directly call business APIs; data is injected via props or feature hooks when needed.
- `stores/` only contains cross-page, cross-component lifecycle client state; single-page form state stays within the page or hook.
- `utils/` must be side-effect-free pure functions, not relying on React, routing, browser storage, or business APIs.

## 4. Shell Integration Standards

All business sub-applications must support both hosted and standalone modes:

| Mode | Standard URL | Route Owner | Login State Source | Purpose |
|---|---|---|---|---|
| hosted | `/apps/{app-id}` | Shell + Sub-application MemoryRouter | ShellContext injection | User enters from the platform workspace |
| standalone | `/{app-id}/` | Sub-application BrowserRouter | `shell-sdk` reads local login state | Standalone run, direct access, independent deployment |

Shell integration requirements:

- Sub-applications must expose a Module Federation remote: `remote.type = "module-federation"`, `remote.module = "./Mount"`.
- Remote entry path is uniformly `/remotes/{app-id}/assets/remoteEntry.js`.
- Hosted route prefix is uniformly `/apps/{app-id}`, standalone route prefix is uniformly `/{app-id}/`.
- Sub-application `src/remote/RemoteApp.tsx` must export a default `mount(container, shellContext)` and return an idempotent cleanup function.
- In hosted mode, `token`, `user`, `locale`, and `basePath` must be received from `shellContext`; the sub-application must not redirect to the login page on its own.
- In standalone mode, when login state is missing, use the navigation tool from `@jonex/shell-sdk` to return to the Shell login page.
- Login state storage uniformly uses `@jonex/shell-sdk`; the access token key is `jonex_access_token`.

## 5. Application Registry Standards

In production, Shell must read the application registry from the platform backend. The recommended interface is:

```text
GET /api/v1/platform/frontend/apps
```

The response structure is based on the `AppManifestV2` type in `@jonex/shell-sdk` and must include at least:

- `id`, `name`, `description`, `enabled`, `order`, `category`, `icon`.
- `routes.hostedBase`, `routes.standaloneBase`.
- `remote.type`, `remote.scope`, `remote.module`, `remote.entry`.
- `permissions.visibleRoles` and optional `permissions.requiredFeatures`.
- `health.url`, `version.source`, `fallback`.

Governance rules:

- The platform service's application registry is the single source of truth for production.
- `frontends/shell/public/app-manifest.json` is only allowed as a local development bootstrap or explicit development fallback when the backend is unavailable.
- Adding, disabling, reordering sub-applications, menu visibility, remote addresses, and version metadata should be managed through platform management capabilities.
- Shell only consumes the application registry and must not hardcode business application lists in code.
- Sub-applications must not maintain their own role enumeration copies; menu and entry visibility comes from the registry or backend permission interfaces.

## 6. Route and Menu Standards

- Route paths use English kebab-case, not Chinese, spaces, display text, or database IDs.
- Page URLs must be stable and must not change due to menu name, display name, or enumeration text changes.
- Sub-application internal home page uses `/home`, unauthorized access uses a unified 403 page, unmatched routes use `/404`.
- Route metadata goes in `routes.config.ts`, menu visibility goes in `menu.config.ts` or the platform application registry.
- In hosted mode, sub-application internal routes only process paths relative to the stripped `/apps/{app-id}` prefix.
- In standalone mode, `createBrowserRouter` must set `basename = VITE_STANDALONE_BASE`.
- In hosted mode, `createMemoryRouter` does not set a basename; the initial path is derived from the current browser URL.
- Menu permissions only control "whether to show/whether to allow entry"; real permissions must be enforced by backend authorization.

## 7. API Call Standards

Frontend call chain:

```text
Page / Feature
  -> Hook
    -> Service Function
      -> API Client
        -> frontend-gateway /api/v1/**
```

Hard rules:

- Page components must not directly write `fetch` or `axios` calls.
- API client defaults to `baseURL: "/"` or `baseURL: "/api/v1"`; specific paths are concatenated by the service layer.
- Request authentication headers are uniformly written by the API client after reading the token from `@jonex/shell-sdk` as `Authorization: Bearer ...`.
- New business interfaces uniformly call `/api/v1/{capability}/...`.
- Must not request Sidecar `/invoke` from the frontend, nor directly connect to container names or ports such as `gateway:8000`, `sidecar:8001`, `knowledge-base:8003`.
- Business request bodies must not include `tenant_id`. If a platform management page needs to select a tenant, the field should be explicitly named for the management target, e.g., `target_tenant_id`, and permission verification should be performed by the backend service layer.
- List interfaces default to server-side pagination, filtering, and sorting; loading all business data at once for table convenience is not allowed.
- File uploads, SSE, and long-running task polling must all encapsulate timeout, cancellation, error handling, and cleanup logic through the service layer.

API type naming:

```text
CreateWidgetRequest
UpdateWidgetRequest
WidgetResponse
WidgetListQuery
WidgetListResponse
```

Error handling:

- The API client uniformly identifies HTTP status, backend error codes, authentication expiration, and network timeouts.
- 401/login expiration uniformly clears login state and redirects to the login page; in hosted mode, prefer calling `logout()` from ShellContext.
- The UI only displays understandable business errors, not Python stacks, SQL, internal container names, or sensitive headers.
- If the response includes a request ID, it should be retained in the error details or troubleshooting information.

## 8. Tenant and Permission Standards

The frontend's responsibility regarding tenants is "display context, carry login state, prevent tenant forgery," not to determine the tenant on behalf of the backend.

- Regular user interfaces do not provide a `tenant_id` input field.
- Regular business create, edit, and delete requests must not include `tenant_id`.
- Current tenant display comes from user information or the backend profile interface, not assembled from localStorage.
- API Key does not represent a business tenant. Pages involving API Key management can only display and manage keys; they must not assume the key carries the current tenant.
- Platform administrator cross-tenant operations must use explicit management interfaces and target tenant fields, and the page copy must inform the user that this is a cross-tenant management action.
- Frontend permission checks are only for experience optimization; when backend authorization fails, the 403/unauthorized state must be correctly displayed.

## 9. State Management Standards

- Remote data should be encapsulated as service + hook; hooks expose stable structures such as `data`, `loading`, `error`, `refresh`, and `pagination`.
- Data refresh between tables, details, and edit modals must have clear trigger points and must not depend on full page reload.
- MobX is only used for cross-page, cross-component lifecycle client state, such as global configuration, current application context, and complex editor sessions.
- Single form, filter bar, and modal toggle states do not go into the global store.
- State that affects page shareability should be retained in the URL, such as pagination, search keywords, filter conditions, and current tab.
- Large objects, file content, rich text drafts, and temporary computation results must not be written to localStorage unless there is a clear recovery requirement and expiration strategy.

## 10. UI and Interaction Standards

Basic requirements:

- Default to using Ant Design components and `@jonex/platform-theme` tokens, `antdTheme`, `theme.css`, `layout.css`.
- Sub-applications must not define their own brand colors, border radii, shadows, fonts, or global resets.
- Pages are business workspaces, not marketing heroes, decorative large images, flashy gradients, or non-functional card stacks.
- Icon buttons should prioritize using the existing icon library; custom icons should only be added when no suitable icon exists.
- Tables, forms, filter bars, detail drawers, and confirmation modals maintain consistent density and interaction within the platform.
- Do not use card-within-card as the main layout; cards are for list items, statistics blocks, detail areas, or standalone tool panels.
- Text must not overflow, be obscured, or be truncated by buttons on both mobile and desktop.
- Page titles, group titles, and card title font sizes should match the container scale, avoiding hero-level large fonts in backend interfaces.

Page states:

- First load: Display skeleton screens, Spin, or local loading indicators.
- No data: Display actionable empty states, such as create, retry, or clear filter.
- Error: Display error reason and retry entry point; permission errors show 403; not found shows 404.
- Submitting: Button enters loading state to prevent duplicate submission.
- After success: Refresh related data, provide lightweight feedback when necessary.

Tables:

- Default to server-side pagination; pagination fields must be consistent with the backend contract.
- Filter and sort changes must reset the page number or have a clear retention strategy.
- Row actions exceeding three should use a "more" menu.
- Destructive actions require a second confirmation and must show the scope of impact.
- Batch operations must include selected count, permission verification, and result feedback.

Forms:

- Frontend validation is for immediate feedback; backend validation is the final authority.
- Edit forms must differentiate between create, edit, and read-only modes.
- Default values and backend enumerations must be loaded through services or configuration, not hardcoded and scattered across components.
- On save failure, retain user input and do not close the modal or navigate away from the page.
- Time fields uniformly use dayjs for handling; display timezone clearly or use a unified platform format.

## 11. Internationalization Standards

### 11.1 Architecture Overview

Shell is the single entry point for language switching, driving all sub-applications through `ShellContext.locale` + the custom event `jonex:locale-change`.

```text
Shell (unified i18n initialization + language switching event-driven)
  ├── @jonex/shell-sdk (shared i18n instance + ShellContext.locale driven)
  │     └── @jonex/i18n-resources (shared common translation resource pack)
  ├── core-business (integrates Shell i18n, retains business-specific translations)
  ├── platform-management (same as above)
  └── ecosystem-management (same as above)
```

### 11.2 Namespace Allocation Rules

Common namespaces are uniformly owned by `@jonex/i18n-resources`; sub-applications only retain business-specific namespaces.

| Namespace | Owner | Description |
|-----------|-------|-------------|
| `translation` (default) | `@jonex/i18n-resources` | Common buttons, form labels, login, error prompts, navigation, status enums, language selection |
| `business` | Each sub-application | Business-specific translations (domain management, platform management, ecosystem management) |

When using `useTranslation()`, the `translation` namespace is loaded by default. Business-specific translations are accessed via `useTranslation('business')`.

### 11.3 Translation Resource Management

- Common translation resources are stored in `frontends/shared/i18n-resources/src/locales/{zh,en}.json`.
- Sub-application business translations remain in `frontends/{app}/src/locales/{zh,en}.json` (business-specific keys only).
- The key structures of `zh.json` and `en.json` must be fully aligned, differing only in values.
- Translation key naming follows the `namespace.key.subkey` pattern, e.g., `common.save`, `error.networkError`.

### 11.4 Language Switching Mechanism

1. **Shell-driven switching**: Shell's `AppHost.tsx` maintains the `locale` state, calls `i18n.changeLanguage()`, and dispatches `window.dispatchEvent(new CustomEvent('jonex:locale-change', { detail: locale }))`.
2. **Sub-application listening**: Sub-applications synchronize the language via `window.addEventListener('jonex:locale-change', handler)`.
3. **Language preference persistence**: `localStorage` uses the key `jonex_locale` (the `LANGUAGE_STORAGE_KEY` constant).

### 11.5 Creating an i18n Instance

Use the `createI18nInstance()` factory function provided by `@jonex/i18n-resources`:

```typescript
// standalone mode
import { createI18nInstance } from '@jonex/i18n-resources'
import zhBusiness from './locales/zh.json'
import enBusiness from './locales/en.json'

const instance = createI18nInstance({
  resources: {
    zh: { business: zhBusiness },
    en: { business: enBusiness },
  },
})

// hosted mode: listen for Shell events
window.addEventListener('jonex:locale-change', ((e: CustomEvent) => {
  instance.changeLanguage(e.detail)
}) as EventListener)
```

### 11.6 Ant Design Locale Synchronization

Shell's `App.tsx` dynamically selects the Ant Design locale based on the current language:

```typescript
import zhCN from 'antd/locale/zh_CN'
import enUS from 'antd/locale/en_US'

// i18n.language === 'en' ? enUS : zhCN
<ConfigProvider locale={antdLocale}>
```

### 11.7 General Rules

- User-facing menus, buttons, errors, empty states, and form validation messages should all go into i18n resources.
- Route paths, API fields, permission codes, and enumeration values are not internationalized.
- In hosted mode, prefer using the `locale` and `setLocale` provided by ShellContext.
- New pages can start with Chinese, but Chinese copy must not be hardcoded in reusable components or the service layer.
- Sub-applications do not maintain their own `HeaderNav/locale.tsx` language selectors; these are uniformly provided by Shell.

## 12. Build and Deployment Standards

- Sub-applications use Vite for building; Module Federation plugin uniformly uses `@originjs/vite-plugin-federation`.
- Federation `name` uses camelCase scope, e.g., `coreBusiness`, `platformManagement`.
- Federation `filename` is fixed as `remoteEntry.js`; `exposes` is fixed to expose `./Mount`.
- Build artifacts go into the sub-application's independent static directory, e.g., `/usr/share/nginx/html/core-business/`.
- Sub-application Nginx must support both standalone SPA fallback and `/remotes/{app-id}/` remote assets.
- `frontend-gateway` is the sole external entry point for production; new sub-applications must register both standalone and remote route types in the gateway Nginx configuration.
- Dockerfile uses multi-stage builds; `pnpm --filter @jonex/{app-id} build` is executed inside the image, and must not depend on a pre-existing local `dist`.
- Runtime backend addresses are configured through gateway or environment injection; do not hardcode local IPs, container IPs, or temporary domain names into source code.
- Static resource filenames must include hashes to prevent caching issues after release.

## 13. Quality Gates

Run the following at minimum before committing:

```bash
cd frontends
pnpm --filter @jonex/{app-id} typecheck
pnpm --filter @jonex/{app-id} build
pnpm --filter @jonex/{app-id} lint
```

High-risk pages require tests or manual verification records:

- Login expiration, unauthorized access, no menu permission.
- Both hosted and standalone access modes.
- Detail page refresh, deep linking, 404.
- Table pagination, filtering, sorting, batch operations.
- Form create, edit, validation failure, save failure, duplicate submission.
- File upload, download, SSE, long-running task polling and cancellation.
- Tenant switching or platform administrator cross-tenant management.

## 14. New Sub-application Creation Checklist

When creating a new sub-application, confirm each item:

- `APP_ID` uses kebab-case and does not conflict with existing applications.
- `PACKAGE_NAME` uses `@jonex/{app-id}`.
- `APP_SCOPE` uses camelCase and does not conflict with existing Module Federation scopes.
- `STANDALONE_BASE` uses `/{app-id}/`, with leading and trailing `/`.
- TypeScript sub-application has been created from `frontends/_template`.
- `.env` and `.env.example` have been created, and `.env.example` includes default values for local development.
- `@jonex/shell-sdk` and `@jonex/platform-theme` have been integrated.
- `src/remote/RemoteApp.tsx` has implemented `mount(container, shellContext)`.
- Both hosted `/apps/{app-id}` and standalone `/{app-id}/` have been configured.
- Remote, routes, permissions, version, and health check metadata have been registered in the platform application registry.
- Shell local development remote proxy has been configured.
- `deploy/nginx/frontend-gateway.conf` has been configured.
- Has been added to `deploy/docker-compose.yml`.
- APIs have been confirmed to only use `/api/v1/**`.
- Regular business requests have been confirmed to not include `tenant_id`.
- typecheck, lint, and build have been verified as passing.

## 15. New Page / New Feature Checklist

Before committing new pages or features, confirm:

- Page logic, business logic, and request logic have been properly layered.
- API types, form types, and list query types are clearly defined.
- Page has loading, empty, error, and success states.
- 401, 403, 404, and 500 each have reasonable UI representations.
- Tables use server-side pagination and do not load all business data at once.
- Form failures do not lose user input.
- Destructive actions have a second confirmation and scope of impact indication.
- Page copy is in i18n resources.
- UI uses platform theme tokens; no arbitrary colors or shadows are added.
- Both hosted and standalone paths are accessible.
- Tenant field does not appear in regular business request bodies.

## 16. Relationship with Backend Standards

The frontend standard and `backend-development-standard.md` are two sides of the same system constraints:

- The backend is responsible for authentication, tenants, permissions, entities, service layer, and repository layer consistency.
- The frontend is responsible for entry, routing, state, interaction, request encapsulation, and user experience consistency.
- Tenant isolation is based on the backend; the frontend must not forge tenants using hidden fields, localStorage, or URL parameters.
- Permission determination is based on the backend; the frontend only handles menu visibility, button availability, and error experience optimization.
- API contract changes must simultaneously update service types, page state handling, and necessary i18n copy.
