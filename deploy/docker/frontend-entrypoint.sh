#!/bin/sh
# ============================================================
# 悦溪平台前端 — 运行时配置注入
# 替换 index.html 中的 __JONEX_CONFIG_PLACEHOLDER__ 为实际环境变量
# ============================================================

set -e

API_BASE_URL="${API_BASE_URL:-/api}"
ENV="${ENV:-production}"
APP_TITLE="${APP_TITLE:-悦溪平台}"

CONFIG="{\"API_BASE_URL\": \"${API_BASE_URL}\", \"ENV\": \"${ENV}\", \"APP_TITLE\": \"${APP_TITLE}\"}"

INDEX_FILE="${INDEX_FILE:-/usr/share/nginx/html/index.html}"

if [ -f "$INDEX_FILE" ]; then
    sed -i "s|__JONEX_CONFIG_PLACEHOLDER__|${CONFIG}|g" "$INDEX_FILE"
    echo "[OK] Config injected into ${INDEX_FILE}"
else
    echo "[WARN] ${INDEX_FILE} not found, skipping config injection"
fi

exec nginx -g "daemon off;"
