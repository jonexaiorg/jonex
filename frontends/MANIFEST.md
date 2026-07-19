# Frontend Application Manifest

This document records the runtime conventions for current frontend applications. The production application manifest is sourced from the platform backend registry, output by `GET /api/v1/platform/frontend/apps`; `frontends/shell/public/app-manifest.json` serves only as a local development fallback when the backend is unavailable.

New frontend sub-applications must follow the root-level [frontend-development-standard.md](../frontend-development-standard.md).

## Shell

| Item | Value |
|---|---|
| Package name | `@jonex/shell` |
| Responsibility | Login, global navigation, app manifest loading, permission guard, sub-app mounting |
| Access path | `/` |
| Dev port | `5173` |
| Production container | `shell-frontend` |

## Sub-applications

| App | Package name | Hosted path | Standalone path | Remote entry | Scope | Port |
|---|---|---|---|---|---|---|
| Core Business | `@jonex/core-business` | `/apps/core-business` | `/core-business/` | `/remotes/core-business/assets/remoteEntry.js` | `coreBusiness` | `5175` |
| Platform Management | `@jonex/platform-management` | `/apps/platform-management` | `/platform-management/` | `/remotes/platform-management/assets/remoteEntry.js` | `platformManagement` | `5177` |
| Ecosystem Management | `@jonex/ecosystem-management` | `/apps/ecosystem-management` | `/ecosystem-management/` | `/remotes/ecosystem-management/assets/remoteEntry.js` | `ecosystemManagement` | `5176` |

## API Convention

- Frontend may only call `/api/v1/**`.
- No new business API compatibility prefixes are allowed.
- Frontend must not directly connect to Sidecar, capability service container names, or host debug ports.

## Change Process

1. Register the application, menus, permissions, and remote metadata in the platform backend.
2. Update `frontends/shell/public/app-manifest.json` as a local fallback.
3. Configure standalone paths and remote asset reverse proxy in `deploy/nginx/frontend-gateway.conf`.
4. Add or adjust the sub-app's own `Dockerfile`, `nginx/default.conf`, and `vite.config.ts`.
5. Run `pnpm run typecheck` and `pnpm run build` from the `frontends/` root directory, then use `pnpm --filter <package> typecheck` to isolate individual sub-app issues if needed.
