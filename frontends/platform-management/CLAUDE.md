# Platform Management Frontend Guide

`@jonex/platform-management` 是平台管理子应用，负责用户、角色、权限、菜单、应用注册、审计、任务等管理界面。开发前先阅读根目录 [frontend-development-standard.md](../../frontend-development-standard.md)。

## 应用契约

| 项 | 值 |
|---|---|
| App id | `platform-management` |
| Package | `@jonex/platform-management` |
| Hosted path | `/apps/platform-management` |
| Standalone path | `/platform-management/` |
| Remote entry | `/remotes/platform-management/assets/remoteEntry.js` |
| Remote scope | `platformManagement` |
| Dev port | `5177` |

## 开发规则

- Shell 负责登录、导航、权限守卫和应用挂载。
- 本应用可以展示租户和跨租户管理入口，但必须调用明确的平台管理 API。
- 普通业务请求 body 不传 `tenant_id`；跨租户管理字段应使用明确名称，例如 `target_tenant_id`。
- 主题必须使用 `@jonex/platform-theme`。
- 认证、跳转和 ShellContext 必须使用 `@jonex/shell-sdk`。
- API 只调用 `/api/v1/platform/**` 或其他标准 `/api/v1/**` 管理接口。
- 页面必须覆盖 loading、empty、error、success、refresh 状态。

## 命令

```bash
pnpm --filter @jonex/platform-management dev
pnpm --filter @jonex/platform-management typecheck
pnpm --filter @jonex/platform-management build
```
