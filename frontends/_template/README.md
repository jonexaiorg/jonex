# Jonex Frontend App Template

This template is used to create new Jonex platform frontend sub-applications. New apps must follow the root-level [frontend-development-standard.md](../../frontend-development-standard.md).

## 1. Creating an App

After copying the template, replace the following placeholders:

| Placeholder | Example |
|---|---|
| `{{APP_NAME}}` | `@jonex/my-app` |
| `{{APP_ID}}` | `my-app` |
| `{{APP_TITLE}}` | `My App` |
| `{{REMOTE_SCOPE}}` | `myApp` |
| `{{DEV_PORT}}` | `5180` |

Standard paths:

```text
hosted:      /apps/{app-id}
standalone:  /{app-id}/
remote:      /remotes/{app-id}/assets/remoteEntry.js
api:         /api/v1/{capability}/**
```

## 2. Directory Structure

```text
src/
├── app/                 # App-level Provider, error boundary, startup config
├── router/              # Routes and page meta info
├── remote/              # Module Federation mount entry
├── pages/               # Page orchestration
├── features/            # Complex business workflows
├── components/          # Reusable components within the app
├── services/            # API client and business request functions
├── stores/              # Cross-page client state
├── hooks/               # Composition logic
├── types/               # App-specific type definitions
├── utils/               # Pure utility functions
└── styles/              # App-level styles
```

## 3. Shell Integration

Sub-applications must support two modes:

| Mode | URL | Router | Auth State |
|---|---|---|---|
| hosted | `/apps/{app-id}` | MemoryRouter | Injected via ShellContext |
| standalone | `/{app-id}/` | BrowserRouter | Read via `@jonex/shell-sdk` |

`src/remote/RemoteApp.tsx` should export a mount function and return an idempotent cleanup function. In hosted mode, if auth state is missing, do not redirect to the login page — Shell handles this.

## 4. Shared Dependencies

The template uses by default:

- `@jonex/platform-theme`: Platform CSS tokens, Ant Design theme, layout styles.
- `@jonex/shell-sdk`: Auth storage, navigation utilities, ShellContext, shared manifest types.

Sub-applications must not define their own brand colors, global resets, auth storage, or app manifest types.

## 5. API Rules

- Pages and components must not directly use `fetch` or `axios`.
- All API calls must go through `services/`.
- Frontend only calls `/api/v1/**`.
- Business request bodies must not include `tenant_id`.
- Do not directly connect to Sidecar, capability services, container names, or host debug ports.

## 6. Integration Checklist

When adding a new application, update the following simultaneously:

1. `frontends/pnpm-workspace.yaml`.
2. Platform backend app registry.
3. `frontends/shell/public/app-manifest.json` local fallback.
4. `deploy/nginx/frontend-gateway.conf`.
5. Sub-app `Dockerfile` and `nginx/default.conf`.
6. `frontends/MANIFEST.md`.

## 7. Verification

```bash
pnpm --filter @jonex/{app-id} typecheck
pnpm --filter @jonex/{app-id} build
```

If the app has a lint script, it must also be run:

```bash
pnpm --filter @jonex/{app-id} lint
```
