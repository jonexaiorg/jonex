# Jonex Frontend Template Guidance

Use this directory only as the starting point for a new Jonex micro frontend. The source of truth is the root [frontend-development-standard.md](../../frontend-development-standard.md).

## Required Replacements

| Placeholder | Example | Meaning |
|---|---|---|
| `{{APP_NAME}}` | `@jonex/my-app` | npm package name |
| `{{APP_TITLE}}` | `My App` | display title |
| `{{APP_SCOPE}}` | `myApp` | Module Federation scope, camelCase |
| `{{APP_ID}}` / `__APP_ID__` | `my-app` | platform app id |
| `{{STANDALONE_BASE}}` | `/my-app/` | standalone base path |
| `{{DEV_PORT}}` | `5179` | Vite dev port |
| `{{API_PREFIX}}` | `/api` | Vite dev proxy prefix |

## Rules

- Keep React 18, TypeScript, Vite, Ant Design 6, `@jonex/shell-sdk`, and `@jonex/platform-theme`.
- Hosted path must be `/apps/<app-id>`.
- Standalone path must be `/<app-id>/`.
- Remote assets must be `/remotes/<app-id>/**`.
- Frontend API calls must use `/api/v1/**`.
- Register the final app in the platform backend registry and update Shell fallback manifest.
