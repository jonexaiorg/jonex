# Ecosystem Management Frontend Guide

`@jonex/ecosystem-management` 是生态管理子应用，负责生态接入、外部集成、合作方能力和相关运营界面。开发前先阅读根目录 [frontend-development-standard.md](../../frontend-development-standard.md)。

## 应用契约

| 项 | 值 |
|---|---|
| App id | `ecosystem-management` |
| Package | `@jonex/ecosystem-management` |
| Hosted path | `/apps/ecosystem-management` |
| Standalone path | `/ecosystem-management/` |
| Remote entry | `/remotes/ecosystem-management/assets/remoteEntry.js` |
| Remote scope | `ecosystemManagement` |
| Dev port | `5176` |

## 开发规则

- Shell 负责登录、导航、权限守卫和应用挂载。
- 本应用只负责生态管理相关页面、services、features 和状态。
- 主题必须使用 `@jonex/platform-theme`。
- 认证、跳转和 ShellContext 必须使用 `@jonex/shell-sdk`。
- API 只调用 `/api/v1/**`。
- 业务请求 body 不传 `tenant_id`。
- 页面必须覆盖 loading、empty、error、success、refresh 状态。

## 命令

```bash
pnpm --filter @jonex/ecosystem-management dev
pnpm --filter @jonex/ecosystem-management typecheck
pnpm --filter @jonex/ecosystem-management build
```
