# ============================================================
# Jonex Dev Gateway
#
# A Node.js development gateway that replaces the production
# Nginx frontend-gateway. Provides a unified HTTP entry point
# for local development, routing requests to individual
# Vite dev servers and the backend API gateway.
# ============================================================

## Motivation

In production, `deploy/docker/frontend-gateway.Dockerfile` + `deploy/nginx/frontend-gateway.conf`
use Nginx as the sole frontend entry point. Development requires the same routing
capability without depending on Docker/Nginx, so a lightweight Node.js http-proxy
alternative is used instead.

## Architecture

```
                        ┌──────────────────┐
                        │  Dev Gateway      │
                        │  :8080            │
                        └──────┬───────────┘
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
    ┌─────▼──────┐   ┌─────────▼──────────┐   ┌──────▼──────┐
    │  /api/*     │   │  /* (catch-all)    │   │  /<app>/*   │
    │             │   │  /remotes/<app>/*  │   │  standalone │
    └─────┬──────┘   └─────────┬──────────┘   └──────┬──────┘
          │                    │                      │
    ┌─────▼──────┐   ┌─────────▼──────────┐   ┌──────▼──────────┐
    │  API GW    │   │  Shell Vite Dev    │   │  Sub-app Vite   │
    │  :8000     │   │  :5173             │   │  :5175-5177     │
    └────────────┘   └───────────────────┘   └─────────────────┘
```

## Starting

```bash
# 1. Install dependencies
pnpm install

# 2. Optional: copy environment configuration
cp .env.example .env
# Edit target addresses in .env

# 3. Start all frontend dev servers (new terminals)
pnpm --filter @jonex/shell dev
pnpm --filter @jonex/core-business dev
pnpm --filter @jonex/platform-management dev
pnpm --filter @jonex/ecosystem-management dev

# 4. Start the development gateway
pnpm dev     # auto-restart
# or
pnpm start   # single run

# 5. Open http://localhost:8080 in browser
```

## Login Configuration

When using the unified entry point, frontend login configuration must also switch to unified entry mode, otherwise:

- Accessing from `http://localhost:8080/<app>/...` redirects to `http://localhost:5173/login`
- After successful login, Shell refuses to redirect back to `8080`, showing a failure message

Local development should satisfy the following conditions:

- Each sub-app `VITE_LOGIN` points to `http://localhost:8080/login`
- Shell's `VITE_ALLOWED_REDIRECT_ORIGINS` includes `http://localhost:8080`
- Backend `AUTH_ALLOWED_REDIRECT_URIS` adds `http://localhost:8080/<app>/` prefix for each appId

## Route Table

| Path | Upstream |
|------|----------|
| `/health` | Returns `200 OK` |
| `/api/*` | `API_TARGET` (default :8000) |
| `/remotes/core-business/*` | Strip `/remotes` → Core Business dev server (:5175) |
| `/remotes/ecosystem-management/*` | Strip `/remotes` → Eco Management dev server (:5176) |
| `/remotes/platform-management/*` | Strip `/remotes` → Platform Mgmt dev server (:5177) |
| `/core-business/*` | Core Business dev server (:5175) |
| `/ecosystem-management/*` | Eco Management dev server (:5176) |
| `/platform-management/*` | Platform Mgmt dev server (:5177) |
| `/*` (catch-all) | Shell dev server (:5173) |

## Environment Variables

See [`.env.example`](./.env.example).

## Relationship to Nginx Configuration

The routing rules in the Nginx `frontend-gateway.conf` are mapped directly to this
gateway, with the only differences being:

- Development connects to localhost Vite dev servers instead of Docker containers
- `/remotes/<app>/` paths strip the `/remotes` prefix before forwarding to sub-apps,
  because Vite dev server `base` is `/<app>/` (e.g. `core-business/`)
- Added WebSocket upgrade support for proper Vite HMR operation
- Some security response headers are retained (X-Frame-Options, etc.)
