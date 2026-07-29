#!/usr/bin/env bash
# =============================================================================
# 优化版 compose 构建入口（*nix / CI）
#
# 对应 spec: docker-build-optimization / 任务 7.1
# 验证需求: 5.1（并发上限）/ 5.4（秒级总耗时）/ 5.5（失败非零退出）
#
# 职责：
#   1) 构建共享基础镜像 jonex/python-base:local 并 --load 进本地镜像库；
#   2) COMPOSE_BAKE=1 docker compose build 并行构建（委托 buildx bake），
#      产出 docker compose up 实际运行的 deploy-* 镜像；7 个后端服务通过
#      additional_contexts 复用 python-base（Dockerfile 内 FROM ${PYTHON_BASE}）。
#
#   并发上限 NPROC = min(max(逻辑核,1),8)，经 BUILDKIT_MAX_PARALLELISM 注入。
#   任一服务构建失败 -> 非零退出码。
#
# 用法：
#   bash deploy/scripts/build_all.sh            # 构建全部 deploy-* 镜像
#   bash deploy/scripts/build_all.sh gateway    # 仅构建指定 compose 服务（透传）
# =============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="deploy/docker-compose.yml"
PYTHON_BASE_TAG="jonex/python-base:local"
BUILD_TARGET="${1:-}"   # 可选：仅构建某个 compose 服务

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
  export COMPOSE_BAKE=1                                  # compose build 委托 bake（并行 + 缓存）
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
    # 步骤 1：构建共享基础镜像并 --load 进本地镜像库（供 additional_contexts 引用）
    log "步骤 1/2：构建共享基础镜像 ${PYTHON_BASE_TAG} ..."
    docker buildx build --load -t "${PYTHON_BASE_TAG}" \
      -f deploy/docker/python-base.Dockerfile . || exit 1
    # 步骤 2：并行 compose 构建，产出 deploy-* 运行镜像
    log "步骤 2/2：并行 compose 构建（deploy-* 镜像）..."
    # shellcheck disable=SC2086
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
