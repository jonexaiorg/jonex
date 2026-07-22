# Jonex平台前端子应用接入指南

本文档用于指导在当前Jonex平台前端架构中新增 TypeScript 子应用，并保证新子应用同时满足：

- Shell 主应用统一入口、统一登录、统一导航。
- 子应用可被 Shell 以 hosted 模式加载。
- 子应用也可 standalone 独立访问、独立部署、独立容器运行。
- 新子应用和 Shell 统一使用平台主题与样式。

> 当前对齐时间：2026-05-27。本文档以当前四个 TypeScript 子应用的真实实现为准：`core-business`、`

## 当前状态结论

这份接入指南需要和当前代码保持以下认知一致：

| 关注点 | 当前真实文件 | 结论 |
|---|---|---|
| Shell 主应用 | `frontends/shell` | 唯一主入口，负责登录、导航、manifest 加载和 remote 挂载 |
| 应用清单 | `frontends/shell/public/app-manifest.json` | 已是 `schemaVersion: 2`，新增应用必须按 v2 结构注册 |
| 前端总网关 | `deploy/nginx/frontend-gateway.conf` | 只在这里聚合 Shell、standalone、remote assets |
| 子应用 Nginx | `frontends/{app}/nginx/default.conf` | 新 TS 子应用使用应用内 nginx 配置，不再新增 `deploy/nginx/{app}.conf` |
| 子应用 Dockerfile | `frontends/{app}/Dockerfile` | 新 TS 子应用使用多阶段 Docker 构建，不依赖本地 `dist` 被拷进构建上下文 |
| 登录态存储 | `frontends/shared/shell-sdk/src/authStorage.ts` | access token 统一 key 是 `jonex_access_token` |
| 平台主题 | `frontends/shared/platform-theme` | Shell 和新 TS 子应用都应引入该主题包 |
| 运行时环境变量 | `frontends/{app}/.env` | 三个新 TS 子应用都有 `VITE_APP_ID`、`VITE_STANDALONE_BASE`、`VITE_LOGIN` 等配置 |
| 模板应用 | `frontends/_template` | 目前 TS 运行骨架可用，但 Dockerfile/nginx/theme/.env/模板说明还要参考四个真实 TS 子应用补齐 |

旧流程里“创建 `deploy/nginx/{app}.conf`”、“Dockerfile 直接 `COPY dist`”、“给 `.dockerignore` 添加 dist 例外”、“Module Federation scope 使用 `my_app` 下划线命名”都不再作为新子应用接入标准。

## 架构概览

```txt
浏览器
  |
  v
frontend-gateway (nginx:80)
  |
  |-- /                         -> shell-frontend
  |-- /apps/<app>               -> shell-frontend 兜底路由
  |                                  Shell AppHost 读取 app-manifest.json
  |                                  再加载 /remotes/<app>/assets/remoteEntry.js
  |
  |-- /remotes/<app>/           -> <app>-frontend remote assets
  |-- /<app>/                   -> <app>-frontend standalone SPA
  |
  |-- /api/                     -> gateway:8000
```

子应用有两种运行模式：

| 模式 | 访问地址 | 路由所有者 | 登录态来源 | 典型用途 |
|---|---|---|---|---|
| hosted | `/apps/<app>` | Shell BrowserRouter + 子应用 MemoryRouter | Shell 通过 `shellContext` 传入 | 用户从 Shell 左侧栏进入 |
| standalone | `/<app>/` | 子应用 BrowserRouter | 子应用自己从 `jonex_access_token` 读取 | 独立运行、独立部署、直接访问 |

注意：`http://localhost/apps/core-business` 是 Shell hosted 地址，不是 standalone 地址；`http://localhost/core-business/` 才是核心业务子应用的 standalone 地址。

## 当前子应用清单

| 应用 | 类型 | hosted 地址 | standalone 地址 | remote entry | scope |
|---|---|---|---|---|---|
| 核心业务 | 新 TS 子应用 | `/apps/core-business` | `/core-business/` | `/remotes/core-business/assets/remoteEntry.js` | `coreBusiness` |
| 智能引擎 | 新 TS 子应用 | `/apps/
| 平台管理 | 新 TS 子应用 | `/apps/platform-management` | `/platform-management/` | `/remotes/platform-management/assets/remoteEntry.js` | `platformManagement` |
| 生态管理 | 新 TS 子应用 | `/apps/ecosystem-management` | `/ecosystem-management/` | `/remotes/ecosystem-management/assets/remoteEntry.js` | `ecosystemManagement` |

## 命名约定

新增应用先确定以下命名，后续所有文件保持一致。下面以 `my-app` 为例：

| 变量 | 示例 | 说明 |
|---|---|---|
| `APP_ID` | `my-app` | manifest id、URL 路径、Docker service 前缀，使用 kebab-case |
| `PACKAGE_NAME` | `@jonex/my-app` | npm workspace 包名 |
| `APP_TITLE` | `My App` | 页面标题和菜单名称 |
| `APP_SCOPE` | `myApp` | Module Federation scope，使用 camelCase，不能和现有 scope 重复 |
| `STANDALONE_BASE` | `/my-app/` | Vite base，必须以 `/` 开头和结尾 |
| `STANDALONE_BASE_DIR` | `my-app` | Nginx 静态目录名，不带 `/` |
| `DEV_PORT` | `5179` | 本地 Vite 端口，不能和现有应用冲突 |
| `DOCKER_SERVICE` | `my-app-frontend` | docker compose service 名 |
| `DOCKER_CONTAINER` | `jonex-my-app-frontend` | 容器名 |
| `NGINX_UPSTREAM_VAR` | `my_app_upstream` | gateway nginx 变量名，不能含 `-` |

`APP_SCOPE` 不再使用 `my_app` 这种下划线风格；当前三个 TS 子应用都使用 `coreBusiness` 这种 camelCase。

## 步骤 1：复制 TypeScript 模板

```bash
cp -r frontends/_template frontends/my-app
```

模板应用是 TypeScript 骨架，新增应用必须保留 `.ts` / `.tsx` 结构，不要改回 JS/JSX。

复制后替换占位符：

```bash
cd frontends/my-app

find . -type f \( -name '*.tsx' -o -name '*.ts' -o -name '*.json' -o -name '*.html' -o -name '*.css' -o -name '*.scss' -o -name '*.md' -o -name 'Dockerfile' \) \
  -exec sed -i '' \
    -e 's/{{APP_NAME}}/@jonex\/my-app/g' \
    -e 's/{{APP_TITLE}}/My App/g' \
    -e 's/{{APP_SCOPE}}/myApp/g' \
    -e "s|'\/{{STANDALONE_BASE}}'|'\/'|g" \
    -e 's/{{STANDALONE_BASE}}/\/my-app\//g' \
    -e 's/{{STANDALONE_BASE_DIR}}/my-app/g' \
    -e 's/{{API_PREFIX}}/\/api/g' \
    -e 's/{{DEV_PORT}}/5179/g' \
    -e 's/{{APP_ID}}/my-app/g' \
    -e 's/__APP_ID__/my-app/g' {} +
```

这里额外处理了模板当前 `src/main.tsx` 里的 `'/{{STANDALONE_BASE}}'`。如果只做 `{{STANDALONE_BASE}} -> /my-app/`，会生成 `//my-app/`，后续 standalone 登录回跳和路由 basename 都可能异常。

检查占位符和双斜杠风险是否清空：

```bash
rg -n "\{\{|__APP_ID__|//my-app/" . --glob '!node_modules/**'
```

该命令应该没有输出。

复制模板后需要新增 `.env`。当前四个真实 TS 子应用都有该文件，模板目录当前没有：

```dotenv
VITE_APP_ID=my-app
VITE_STANDALONE_BASE=/my-app/
VITE_LOGIN=http://localhost:5173/login
VITE_AUTH_ME=/api/v1/auth/me
VITE_AUTH_EXCHANGE_TICKET=/api/v1/auth/exchange-ticket
```

再核对两个入口 fallback，保持和当前四个真实 TS 子应用一致：

```ts
// src/main.tsx
const appId = (import.meta as any).env?.VITE_APP_ID || 'my-app'
const basePath = (import.meta as any).env?.VITE_STANDALONE_BASE || '/'

// src/router/index.tsx
const STANDALONE_BASENAME = (import.meta as any).env?.VITE_STANDALONE_BASE || '/'
const actualBasename = basename || (mode === 'hosted' ? '/apps/my-app' : STANDALONE_BASENAME)
```

## 步骤 2：补齐平台主题依赖

当前三个 TS 子应用都接入了 `@jonex/platform-theme`。如果模板复制后还没有该依赖，需要补齐。

`frontends/my-app/package.json`：

```json
{
  "dependencies": {
    "@jonex/shell-sdk": "workspace:*",
    "@jonex/platform-theme": "workspace:*"
  }
}
```

`frontends/my-app/vite.config.ts` 的 alias 也要包含：

```ts
resolve: {
  alias: {
    '@': `${pathSrc}`,
    '@jonex/shell-sdk': path.resolve(__dirname, '../shared/shell-sdk/src/index.ts'),
    '@jonex/platform-theme': path.resolve(__dirname, '../shared/platform-theme/src'),
  },
}
```

页面样式优先使用共享主题：

```ts
import { colors, radius } from '@jonex/platform-theme/tokens'
```

如果需要全局主题 CSS，可参考 Shell 的入口文件：

```ts
import '@jonex/platform-theme/theme.css'
import '@jonex/platform-theme/layout.css'
```

## 步骤 3：保留 hosted / standalone 路由边界

新子应用必须保留模板中的以下约定：

| 文件 | 必须保留的约定 |
|---|---|
| `src/remote/RemoteApp.tsx` | 默认导出 `mount(container, shellContext)` |
| `src/remote/RemoteApp.tsx` | hosted 模式收到 `token` / `user` 后写入 `@jonex/shell-sdk` |
| `src/remote/RemoteApp.tsx` | 返回幂等 cleanup，重复调用不能报错 |
| `src/main.tsx` | `appId` fallback 使用真实 `APP_ID`，`basePath` fallback 保持 `/` |
| `src/router/index.tsx` | standalone 使用 `createBrowserRouter(routes, { basename })` |
| `src/router/index.tsx` | standalone basename 优先读取 `VITE_STANDALONE_BASE`，fallback 保持 `/` |
| `src/router/index.tsx` | hosted 使用 `createMemoryRouter`，不要传 `basename` |
| `src/router/index.tsx` | hosted 初始路径通过 `getHostedInitialEntry(basePath)` 计算 |

路径转换规则：

```txt
Shell URL:        /apps/my-app
子应用内部路由:   /home

Shell URL:        /apps/my-app/domain-space
子应用内部路由:   /domain-space

Standalone URL:   /my-app/domain-space
子应用内部路由:   /domain-space
```

remote cleanup 推荐保持模板形态：

```tsx
let mounted = true
return () => {
  if (!mounted) return
  mounted = false
  root.unmount()
}
```

这部分是避免“直接输入 `/apps/<app>` 正常，但从 Shell 左侧栏点击切换卡死”的关键。

## 步骤 4：补齐子应用 Nginx 配置

当前新 TS 子应用的 Nginx 配置放在应用目录内：

```txt
frontends/my-app/nginx/default.conf
```

不要再新增 `deploy/nginx/my-app.conf`。

可以参考 `frontends/core-business/nginx/default.conf` 创建：

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;
    charset utf-8;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript application/json font/ttf font/otf font/woff font/woff2 application/font-woff application/font-woff2;

    location = /health {
        return 200 'ok';
        add_header Content-Type text/plain;
        access_log off;
    }

    location ^~ /remotes/my-app/ {
        rewrite ^/remotes/(.*)$ /$1 break;
        try_files $uri $uri/ =404;
    }

    location ^~ /my-app/ {
        try_files $uri $uri/ /my-app/index.html;
    }

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
```

## 步骤 5：使用多阶段 Dockerfile

当前新 TS 子应用在 Docker build 内部完成 pnpm install 和 Vite build，不依赖宿主机提前生成 `dist`。

`frontends/my-app/Dockerfile` 应参考四个真实 TS 子应用：

```dockerfile
FROM node:20.18-alpine AS builder
WORKDIR /app

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone
RUN npm config set registry https://registry.npmmirror.com && \
    npm config set fund false && npm config set audit false
RUN npm install -g pnpm@9

COPY frontends/pnpm-workspace.yaml ./
COPY frontends/pnpm-lock.yaml ./
RUN echo '{"name":"jonex-frontend","private":true}' > package.json

COPY frontends/shared/shell-sdk/package.json ./shared/shell-sdk/
COPY frontends/shared/platform-theme/package.json ./shared/platform-theme/
COPY frontends/my-app/package.json ./my-app/

RUN pnpm install

COPY frontends/shared/shell-sdk/ ./shared/shell-sdk/
COPY frontends/shared/platform-theme/ ./shared/platform-theme/
COPY frontends/my-app/ ./my-app/

RUN pnpm --filter @jonex/my-app build

FROM nginx:1.20.1-alpine
WORKDIR /usr/share/nginx/html
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone

COPY --from=builder /app/my-app/dist ./my-app/
COPY frontends/my-app/nginx/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -sf http://127.0.0.1/health || exit 1
CMD ["nginx", "-g", "daemon off;"]
```

因此 `.dockerignore` 当前保持忽略 `frontends/**/dist` 是正确的，不需要为新子应用添加 dist 例外。

## 步骤 6：注册 docker-compose 服务

在 `deploy/docker-compose.yml` 中新增服务：

```yaml
  my-app-frontend:
    build:
      context: ..
      dockerfile: frontends/my-app/Dockerfile
    container_name: jonex-my-app-frontend
    hostname: my-app-frontend
    networks:
      - jonex-network
    expose:
      - "80"
    environment:
      TZ: Asia/Shanghai
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://127.0.0.1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    restart: unless-stopped
```

并在 `frontend-gateway.depends_on` 中添加：

```yaml
      my-app-frontend:
        condition: service_started
```

## 步骤 7：注册 gateway 路由

在 `deploy/nginx/frontend-gateway.conf` 中添加两段路由，位置放在其他子应用 route 之后、Shell 兜底 `location /` 之前。

```nginx
    # ============================================================
    # my-app remote assets（Module Federation）
    # ============================================================
    location ^~ /remotes/my-app/ {
        set $my_app_upstream my-app-frontend;
        proxy_pass http://$my_app_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # ============================================================
    # my-app standalone SPA
    # ============================================================
    location ^~ /my-app/ {
        set $my_app_upstream my-app-frontend;
        proxy_pass http://$my_app_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
```

`/apps/my-app` 不需要在 gateway 里单独配置，它应由 Shell 的兜底路由接住，再由 Shell 的 `AppHost` 根据 manifest 加载 remote。

## 步骤 8：注册 Shell manifest

在 `frontends/shell/public/app-manifest.json` 的 `apps` 数组中新增 v2 应用配置。

```json
{
  "id": "my-app",
  "name": "My App",
  "description": "新业务子应用",
  "enabled": true,
  "order": 600,
  "category": "core-business",
  "icon": "AppstoreOutlined",
  "basePath": "/apps/my-app",
  "standaloneUrl": "/my-app/",
  "entry": "/remotes/my-app/assets/remoteEntry.js",
  "scope": "myApp",
  "module": "./Mount",
  "apiPrefix": "/api/",
  "roles": ["admin", "user"],
  "routes": {
    "hostedBase": "/apps/my-app",
    "standaloneBase": "/my-app"
  },
  "remote": {
    "type": "module-federation",
    "scope": "myApp",
    "module": "./Mount",
    "entry": "/remotes/my-app/assets/remoteEntry.js"
  },
  "health": {
    "url": "/remotes/my-app/version.json",
    "timeoutMs": 3000
  },
  "permissions": {
    "visibleRoles": ["admin", "user"]
  },
  "fallback": {
    "mode": "standalone",
    "url": "/my-app/"
  },
  "version": {
    "expected": "1.x",
    "source": "/remotes/my-app/version.json"
  }
}
```

字段注意事项：

| 字段 | 要求 |
|---|---|
| `id` | 与 URL、Docker service、目录名保持一致 |
| `basePath` / `routes.hostedBase` | 必须是 `/apps/my-app` |
| `standaloneUrl` | 必须是 `/my-app/`，带末尾 `/` |
| `routes.standaloneBase` | 必须是 `/my-app`，不带末尾 `/` |
| `entry` / `remote.entry` | 必须指向 `/remotes/my-app/assets/remoteEntry.js` |
| `scope` / `remote.scope` | 必须和 Vite federation `name` 一致，即 `myApp` |
| `module` / `remote.module` | 固定 `./Mount` |
| `permissions.visibleRoles` | 控制 Shell 菜单可见性 |
| `fallback.url` | remote 加载失败时可跳到 standalone |

当前 Shell 兼容 manifest 中的旧扁平字段和 v2 嵌套字段，所以新增应用两套字段都要写，保持和现有三个 TS 子应用一致。

## 步骤 9：登录态与跨域约定

所有前端应用统一使用 `@jonex/shell-sdk` 读写登录态：

| 数据 | key |
|---|---|
| access token | `jonex_access_token` |
| refresh token | `jonex_refresh_token` |
| user | `jonex_user` |

standalone 模式：

```txt
子应用启动 -> auth loader 读取 jonex_access_token
  |-- 有 token：进入子应用
  |-- 无 token：清理本地登录态，跳转 VITE_LOGIN，并带 redirect=当前完整地址
```

hosted 模式：

```txt
Shell 完成登录校验 -> AppHost 加载 remote -> mount(container, shellContext)
子应用 RemoteApp 收到 token/user -> 写入 shell-sdk -> hosted auth loader 使用 shellContext.user
```

新子应用不要自行定义 token key，也不要在 hosted 模式自行跳登录页。hosted 模式登录入口由 Shell 统一负责。

如果未来子应用独立部署在不同域名，需要通过统一登录中心回跳并写入同名 key；跨顶级域名不能直接共享 localStorage，这部分要靠登录中心 redirect、后端 session/cookie 或 token exchange 方案处理。

## 步骤 10：本地开发验证

进入 workspace 安装依赖并验证：

```bash
cd frontends
pnpm install
pnpm --filter @jonex/my-app typecheck
pnpm --filter @jonex/my-app build
```

本地开发 standalone：

```bash
cd frontends/my-app
pnpm dev
```

访问：

```txt
http://localhost:5179/
```

## 步骤 11：Docker / Shell 集成验证

当前本地重跑流程：

```bash
make down
make build
make up
```

基础检查：

```bash
curl -s http://localhost/health
curl -s http://localhost/app-manifest.json
curl -s http://localhost/remotes/my-app/assets/remoteEntry.js | head -c 200
curl -s http://localhost/my-app/ | head -c 500
docker compose -f deploy/docker-compose.yml ps my-app-frontend frontend-gateway
```

浏览器检查：

```txt
http://localhost/                  # Shell 可打开
http://localhost/apps/my-app       # hosted 可打开
http://localhost/my-app/           # standalone 可打开
Shell 左侧栏连续切换多个子应用       # 不应卡 loading，不应白屏，不应 removeChild 报错
```

## 新增应用文件清单

| 文件 | 操作 | 说明 |
|---|---|---|
| `frontends/my-app/` | 新建 | 从 `_template` 复制，保留 TypeScript |
| `frontends/my-app/package.json` | 修改 | 包名、依赖、`@jonex/platform-theme` |
| `frontends/my-app/.env` | 新建 | `VITE_APP_ID`、`VITE_STANDALONE_BASE`、登录与 auth me 配置 |
| `frontends/my-app/vite.config.ts` | 修改 | base、scope、dev port、alias |
| `frontends/my-app/nginx/default.conf` | 新建 | 子应用容器内部 nginx 配置 |
| `frontends/my-app/Dockerfile` | 修改 | 多阶段构建，复制 shell-sdk、platform-theme、应用源码 |
| `deploy/docker-compose.yml` | 修改 | 新增 frontend service，并加入 frontend-gateway depends_on |
| `deploy/nginx/frontend-gateway.conf` | 修改 | 新增 `/remotes/my-app/` 和 `/my-app/` 两段代理 |
| `frontends/shell/public/app-manifest.json` | 修改 | 新增 schema v2 app 配置 |
| `.dockerignore` | 不需要修改 | 当前多阶段 Docker 构建保持忽略 `frontends/**/dist` |
| `frontends/pnpm-workspace.yaml` | 通常不需要修改 | 当前 `packages: ['*', 'shared/*']` 会识别 `frontends/my-app` |

## 模板现状注意事项

`frontends/_template` 当前已经是 TypeScript 模板，并包含 hosted / standalone 路由骨架。但截至本次对齐，它和四个真实 TS 子应用仍有几处差异：

| 差异 | 当前建议 |
|---|---|
| `_template/Dockerfile` 仍是单阶段 `COPY dist` | 新应用 Dockerfile 先参考 `frontends/core-business/Dockerfile` |
| `_template` 目前没有 `nginx/default.conf` | 新应用需要创建 `frontends/my-app/nginx/default.conf` |
| `_template` 目前没有 `.env` | 新应用需要按四个真实 TS 子应用补齐 `.env` |
| `_template/package.json` 目前没有 `@jonex/platform-theme` | 新应用必须补上平台主题依赖 |
| `_template/vite.config.ts` 目前没有 platform-theme alias | 新应用必须补上 alias |
| `_template/src/main.tsx` 仍有 `__APP_ID__` 和 `'/{{STANDALONE_BASE}}'` | 复制后必须替换 `__APP_ID__`，并把 `basePath` fallback 校正为 `/` |
| `_template/src/router/index.tsx` 的 standalone fallback 仍是 `'/{{STANDALONE_BASE_DIR}}'` | 复制后按当前真实 TS 子应用校正为 `/`，实际路径由 `.env` 的 `VITE_STANDALONE_BASE` 提供 |

后续可以单独把 `_template` 修正到和本指南一致，这样新增应用时才可以真正“一键复制模板”。

## 常见问题排查

### 1. 直接输入 `/apps/my-app` 正常，点击 Shell 左侧栏后卡死

优先检查：

1. `src/remote/RemoteApp.tsx` 的 cleanup 是否幂等。
2. `src/router/index.tsx` hosted 模式是否使用 `createMemoryRouter`。
3. hosted 模式是否错误传入了 `basename`。
4. `getHostedInitialEntry(basePath)` 是否把 `/apps/my-app/...` 转成子应用内部路径。
5. Shell manifest 中 `scope` 是否和 Vite federation `name` 完全一致。

### 2. standalone 能打开，hosted 加载 remote 失败

检查：

```bash
curl -s http://localhost/remotes/my-app/assets/remoteEntry.js | head -c 200
```

如果 404，重点看：

- `deploy/nginx/frontend-gateway.conf` 是否有 `/remotes/my-app/`。
- `frontends/my-app/nginx/default.conf` 的 `/remotes/my-app/` rewrite 是否正确。
- Vite build 后 `remoteEntry.js` 是否在 `dist/assets/remoteEntry.js`。
- manifest 的 `entry` 和 `remote.entry` 是否写成 `/remotes/my-app/assets/remoteEntry.js`。

### 3. standalone 刷新子路由 404

检查子应用 nginx：

```nginx
location ^~ /my-app/ {
    try_files $uri $uri/ /my-app/index.html;
}
```

同时确认 Vite `base` 是 `/my-app/`，`.env` 中 `VITE_STANDALONE_BASE=/my-app/`，React Router standalone 优先读取该值；fallback 按当前四个真实 TS 子应用保持 `/`。

### 4. 未登录时跳转不一致

检查所有应用是否通过 `@jonex/shell-sdk` 使用统一 key `jonex_access_token`。

hosted 模式不要自行跳登录页；standalone 模式才由子应用 auth loader 检查 token 并跳登录中心。

### 5. 新应用主题和 Shell 不一致

检查：

- `package.json` 是否包含 `@jonex/platform-theme`。
- `vite.config.ts` 是否配置 `@jonex/platform-theme` alias。
- 页面是否使用 `@jonex/platform-theme/tokens`。
- 如需全局布局样式，入口是否引入 `theme.css` 和 `layout.css`。
