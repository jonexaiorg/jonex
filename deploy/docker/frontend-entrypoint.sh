





set -e

API_BASE_URL="${API_BASE_URL:-/api}"
ENV="${ENV:-production}"
APP_TITLE="${APP_TITLE:-Jonex平台}"

CONFIG="{\"API_BASE_URL\": \"${API_BASE_URL}\", \"ENV\": \"${ENV}\", \"APP_TITLE\": \"${APP_TITLE}\"}"

INDEX_FILE="${INDEX_FILE:-/usr/share/nginx/html/index.html}"

if [ -f "$INDEX_FILE" ]; then
    sed -i "s|__JONEX_CONFIG_PLACEHOLDER__|${CONFIG}|g" "$INDEX_FILE"
    echo "[OK] Config injected into ${INDEX_FILE}"
else
    echo "[WARN] ${INDEX_FILE} not found, skipping config injection"
fi

exec nginx -g "daemon off;"
