FROM node:20.18-alpine AS builder
WORKDIR /app

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone
RUN npm config set registry https://registry.npmmirror.com && \
    npm config set fund false && npm config set audit false
RUN npm install -g pnpm@9

# Workspace metadata — only the 3 packages needed for shell
COPY frontends/pnpm-workspace.yaml ./
COPY frontends/pnpm-lock.yaml ./
RUN echo '{"name":"jonex-frontend","private":true}' > package.json

COPY frontends/shared/shell-sdk/package.json ./shared/shell-sdk/
COPY frontends/shared/platform-theme/package.json ./shared/platform-theme/
COPY frontends/shell/package.json ./shell/

RUN pnpm install

# Source for build — only the 3 packages needed
COPY frontends/shared/shell-sdk/ ./shared/shell-sdk/
COPY frontends/shared/platform-theme/ ./shared/platform-theme/
COPY frontends/shell/ ./shell/

RUN pnpm --filter @jonex/shell build

FROM nginx:1.20.1-alpine
WORKDIR /usr/share/nginx/html
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone

COPY --from=builder /app/shell/dist ./
COPY deploy/nginx/shell.conf /etc/nginx/conf.d/default.conf
COPY deploy/docker/frontend-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV API_BASE_URL=http://gateway:8000
ENV ENV=production
ENV APP_TITLE=Jonex平台

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
