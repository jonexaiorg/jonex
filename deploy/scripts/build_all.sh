




















set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="deploy/docker-compose.yml"
PYTHON_BASE_TAG="jonex/python-base:local"
BUILD_TARGET="${1:-}"

if [ -t 1 ]; then C_OK=$'\033[32m'; C_ERR=$'\033[31m'; C_INFO=$'\033[36m'; C_RST=$'\033[0m'
else C_OK=""; C_ERR=""; C_INFO=""; C_RST=""; fi
log() { echo "${C_INFO}[$(date +%H:%M:%S)] $*${C_RST}"; }
err() { echo "${C_ERR}  x $*${C_RST}" >&2; }

detect_logical_cpus() {
  local n=""
  command -v nproc >/dev/null 2>&1 && n="$(nproc 2>/dev/null)"
  [ -z "${n}" ] && command -v getconf >/dev/null 2>&1 && n="$(getconf _NPROCESSORS_ONLN 2>/dev/null)"
  printf '%s' "${n}" | grep -Eq '^[0-9]+$' || n=1
  echo "${n}"
}
compute_nproc() { local n="$1"; [ "${n}" -lt 1 ] && n=1; [ "${n}" -gt 8 ] && n=8; echo "${n}"; }

preflight() {
  command -v docker >/dev/null 2>&1 || { err "未找到 docker"; exit 2; }
  docker buildx version >/dev/null 2>&1 || { err "未找到 docker buildx"; exit 2; }
  [ -f "${REPO_ROOT}/${COMPOSE_FILE}" ] || { err "未找到 ${COMPOSE_FILE}"; exit 2; }
  export DOCKER_BUILDKIT=1
  export COMPOSE_BAKE=1
  export BUILDX_BAKE_ENTITLEMENTS_FS="${BUILDX_BAKE_ENTITLEMENTS_FS:-0}"
}

main() {
  preflight
  local cpus nproc start_ns end_ns elapsed rc=0
  cpus="$(detect_logical_cpus)"; nproc="$(compute_nproc "${cpus}")"
  export BUILDKIT_MAX_PARALLELISM="${nproc}"

  log "仓库根         : ${REPO_ROOT}"
  log "并发上限 NPROC : ${nproc}（min(max(逻辑核,1),8)）"
  start_ns="$(date +%s.%N)"

  (
    cd "${REPO_ROOT}" || exit 2

    log "步骤 1/2：构建共享基础镜像 ${PYTHON_BASE_TAG} ..."
    docker buildx build --load -t "${PYTHON_BASE_TAG}" \
      -f deploy/docker/python-base.Dockerfile . || exit 1

    log "步骤 2/2：并行 compose 构建（deploy-* 镜像）..."

    docker compose -f "${COMPOSE_FILE}" build ${BUILD_TARGET} || exit 1
  )
  rc=$?

  end_ns="$(date +%s.%N)"
  elapsed="$(awk -v s="${start_ns}" -v e="${end_ns}" 'BEGIN { printf "%.2f", (e - s) }')"
  echo
  if [ "${rc}" -eq 0 ]; then
    log "${C_OK}构建完成，总耗时: ${elapsed} 秒${C_RST}"
    log "启动: docker compose -f ${COMPOSE_FILE} up -d"
    exit 0
  fi
  err "构建失败（见上方输出）；总耗时: ${elapsed} 秒"
  exit "${rc}"
}

main "$@"
