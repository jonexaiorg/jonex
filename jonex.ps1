


param(
    [Parameter(Position=0)]
    [string]$Command = "help",

    [Parameter(Position=1)]
    [string]$Service = "",

    [Parameter(Position=2)]
    [string]$N = "1"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSCommandPath
$DeployDir = Join-Path $RepoRoot "deploy"
$FrontendsDir = Join-Path $RepoRoot "frontends"

$MiddlewareServices = @("postgres", "redis", "etcd", "minio", "milvus")
$RagServices = @("lightrag", "atomic-rag")
$BackendServices = @("gateway", "sidecar", "knowledge-base-service", "business-domain-service", "platform-service")
$FrontendServices = @("frontend-gateway", "shell-frontend", "core-business-frontend", "platform-management-frontend", "ecosystem-management-frontend")

$ShellApp = "@jonex/shell"
$CoreApp = "@jonex/core-business"
$PlatformApp = "@jonex/platform-management"
$EcosystemApp = "@jonex/ecosystem-management"


$ServiceNameMap = @{
    "knowledge-base" = "knowledge-base-service"
    "business-domain" = "business-domain-service"
    "platform" = "platform-service"
    "lightrag" = "lightrag"
    "atomic-rag" = "atomic-rag"
    "frontend-gateway" = "frontend-gateway"
    "shell-frontend" = "shell-frontend"
    "core-business-frontend" = "core-business-frontend"
    "platform-management-frontend" = "platform-management-frontend"
    "ecosystem-management-frontend" = "ecosystem-management-frontend"
}

$MainFrontendFilters = @("--filter", $ShellApp, "--filter", $CoreApp, "--filter", $PlatformApp, "--filter", $EcosystemApp)

if ($Service -match "^SERVICE=(.+)$") {
    $Service = $Matches[1]
}
if ($N -match "^N=(.+)$") {
    $N = $Matches[1]
}

$ComposeBaseFiles = @("-f", "docker-compose.yml")
$ComposeGpuFiles = $ComposeBaseFiles + @("-f", "docker-compose.gpu.yml")
$ComposeLocalFiles = $ComposeBaseFiles
$ComposeDevFiles = $ComposeLocalFiles + @("-f", "docker-compose.override.yml")
$ComposeGpuDevFiles = $ComposeDevFiles + @("-f", "docker-compose.gpu.yml")

function Invoke-Compose {
    param(
        [ValidateSet("Base", "Dev", "Gpu", "GpuDev")]
        [string]$Mode,
        [string[]]$ComposeArgs
    )

    $files = switch ($Mode) {
        "Base" { $ComposeLocalFiles }
        "Dev" { $ComposeDevFiles }
        "Gpu" { $ComposeGpuFiles }
        "GpuDev" { $ComposeGpuDevFiles }
    }

    Push-Location $DeployDir
    try {
        & docker compose @files @ComposeArgs
    }
    finally {
        Pop-Location
    }
}

function Enable-ComposeBake {

    $env:DOCKER_BUILDKIT = "1"
    $env:COMPOSE_BAKE = "1"
    if (-not $env:BUILDX_BAKE_ENTITLEMENTS_FS) { $env:BUILDX_BAKE_ENTITLEMENTS_FS = "0" }
}

function Build-PythonBase {




    $existing = & docker images -q jonex/python-base:local 2>$null
    if ($existing) {
        Write-Host "=== 共享基础镜像 jonex/python-base:local 已存在，跳过构建 ===" -ForegroundColor Green
        return
    }
    Write-Host "=== 构建共享基础镜像 jonex/python-base:local ===" -ForegroundColor Cyan
    Push-Location $RepoRoot
    try {
        & docker buildx build --load -t jonex/python-base:local -f deploy/docker/python-base.Dockerfile .
        if ($LASTEXITCODE -ne 0) { throw "python-base 镜像构建失败（退出码 $LASTEXITCODE）" }
    }
    finally {
        Pop-Location
    }
}

function Invoke-Pnpm {
    param([string[]]$PnpmArgs)

    Push-Location $FrontendsDir
    try {
        & pnpm @PnpmArgs
    }
    finally {
        Pop-Location
    }
}

function Invoke-PerfLog {


    param(
        [string]$ServiceName,
        [string]$Pattern
    )

    $tail = "1000"
    if ($Service -match '^\d+$') { $tail = $Service }

    Push-Location $DeployDir
    try {
        & docker compose @ComposeDevFiles logs "--tail=$tail" $ServiceName | Select-String $Pattern
    }
    finally {
        Pop-Location
    }
}

function Require-Service {
    if ([string]::IsNullOrWhiteSpace($Service)) {
        Write-Host "请指定服务名，例如:" -ForegroundColor Yellow
        Write-Host "  .\jonex.ps1 rebuild gateway"
        Write-Host "  .\jonex.ps1 rebuild core-business-frontend"
        Write-Host "  .\jonex.ps1 restart-service gateway"
        Write-Host "  .\jonex.ps1 logs-service SERVICE=gateway"
        exit 1
    }
}

function Import-DotEnv {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return
    }

    foreach ($rawLine in Get-Content $Path) {
        $line = $rawLine.Trim()
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#")) {
            continue
        }
        $idx = $line.IndexOf("=")
        if ($idx -le 0) {
            continue
        }
        $key = $line.Substring(0, $idx).Trim()
        $value = $line.Substring($idx + 1).Trim()
        if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        [Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

function Set-LocalBackendServiceUrls {
    $env:ENV = "dev"
    $env:SIDECAR_URL = "http://127.0.0.1:8001"
    $env:KNOWLEDGE_BASE_URL = "http://127.0.0.1:8003"
    $env:BUSINESS_DOMAIN_URL = "http://127.0.0.1:8005"
    $env:ATOMIC_RAG_URL = "http://127.0.0.1:8004"
    $env:PLATFORM_URL = "http://127.0.0.1:8006"
}

function Set-LocalBackendEnv {
    Import-DotEnv (Join-Path $DeployDir ".env")

    if (-not $env:DB_PORT) { $env:DB_PORT = "5432" }
    if (-not $env:DB_USERNAME) { $env:DB_USERNAME = "jonex" }
    if (-not $env:DB_PASSWORD) { $env:DB_PASSWORD = "CHANGE_ME" }
    if (-not $env:DB_NAME) { $env:DB_NAME = "jonex" }

    $env:DB_HOST = "127.0.0.1"
    $env:REDIS_URL = "redis://127.0.0.1:6379/0"
    $env:MILVUS_HOST = "127.0.0.1"
    $env:MILVUS_PORT = "19530"
    Set-LocalBackendServiceUrls
}

function Get-ServerInfraEnvPath {
    $serverLocalPath = Join-Path $RepoRoot ".env.server-local"
    if (Test-Path $serverLocalPath) {
        return $serverLocalPath
    }

    throw "未找到 .env.server-local。请先执行: Copy-Item .env.server-local.example .env.server-local，并把其中的 SERVER_IP 改成实际服务器地址。"
}

function Set-ServerInfraBackendEnv {
    $envPath = Get-ServerInfraEnvPath
    Import-DotEnv $envPath

    if (-not $env:DB_HOST) { throw ".env.server-local 缺少 DB_HOST" }
    if (-not $env:REDIS_URL) { throw ".env.server-local 缺少 REDIS_URL" }
    if (-not $env:MILVUS_HOST) { throw ".env.server-local 缺少 MILVUS_HOST" }
    if (($env:DB_HOST -match "SERVER_IP") -or ($env:REDIS_URL -match "SERVER_IP") -or ($env:MILVUS_HOST -match "SERVER_IP")) {
        throw ".env.server-local 里仍然包含 SERVER_IP 占位符，请先替换成实际服务器地址。"
    }

    if (-not $env:DB_PORT) { $env:DB_PORT = "5432" }
    if (-not $env:DB_USERNAME) { $env:DB_USERNAME = "jonex" }
    if (-not $env:DB_PASSWORD) { $env:DB_PASSWORD = "CHANGE_ME" }
    if (-not $env:DB_NAME) { $env:DB_NAME = "jonex" }
    if (-not $env:MILVUS_PORT) { $env:MILVUS_PORT = "19530" }

    Set-LocalBackendServiceUrls
}

function Start-BackendService {
    param(
        [ValidateSet("gateway", "sidecar", "knowledge-base", "business-domain", "platform")]
        [string]$Name
    )

    Push-Location $RepoRoot
    try {
        switch ($Name) {
            "gateway" {
                Write-Host "=== 启动 API Gateway: http://localhost:8000 ===" -ForegroundColor Cyan
                & python run_gateway.py --reload
            }
            "sidecar" {
                Write-Host "=== 启动 Sidecar: http://localhost:8001 ===" -ForegroundColor Cyan
                & python main.py
            }
            "knowledge-base" {
                Write-Host "=== 启动知识库服务: http://localhost:8003 ===" -ForegroundColor Cyan
                $env:CAPABILITY_NAME = "knowledge_base"
                $env:SERVICE_PORT = "8003"
                & python deploy/start_capability.py
            }
            "business-domain" {
                Write-Host "=== 启动业务领域服务: http://localhost:8005 ===" -ForegroundColor Cyan
                $env:CAPABILITY_NAME = "business_domain"
                $env:SERVICE_PORT = "8005"
                & python deploy/start_capability.py
            }
            "platform" {
                Write-Host "=== 启动平台管理服务: http://localhost:8006 ===" -ForegroundColor Cyan
                $env:CAPABILITY_NAME = "platform"
                $env:SERVICE_PORT = "8006"
                & python deploy/start_capability.py
            }
        }
    }
    finally {
        Pop-Location
    }
}

function Invoke-Backend {
    param(
        [ValidateSet("gateway", "sidecar", "expert", "knowledge-base", "business-domain", "platform")]
        [string]$Name
    )

    Invoke-Compose -Mode Dev -ComposeArgs (@("up", "-d") + $MiddlewareServices + $RagServices)
    Set-LocalBackendEnv
    Start-BackendService $Name
}

function Invoke-BackendServerInfra {
    param(
        [ValidateSet("gateway", "sidecar", "expert", "knowledge-base", "business-domain", "platform")]
        [string]$Name
    )

    Set-ServerInfraBackendEnv
    Start-BackendService $Name
}

function Start-BackendProcess {
    param([string]$ChildCommand)

    $pwsh = (Get-Process -Id $PID).Path
    $args = @("-NoProfile", "-NoExit", "-File", $PSCommandPath, $ChildCommand)
    Start-Process -FilePath $pwsh -ArgumentList $args -WorkingDirectory $RepoRoot
}

$BuildServiceCommands = @{
    "build-sidecar" = "sidecar"
    "build-knowledge-base" = "knowledge-base-service"
    "build-business-domain" = "business-domain-service"
    "build-platform" = "platform-service"
}

$UpServiceCommands = @{
    "up-sidecar" = "sidecar"
    "up-knowledge-base" = "knowledge-base-service"
    "up-business-domain" = "business-domain-service"
    "up-platform" = "platform-service"
    "up-postgres" = "postgres"
    "up-redis" = "redis"
    "up-lightrag" = "lightrag"
}

$DownServiceCommands = @{
    "down-gateway" = "gateway"
    "down-sidecar" = "sidecar"
    "down-knowledge-base" = "knowledge-base-service"
    "down-business-domain" = "business-domain-service"
    "down-platform" = "platform-service"
}

$LogsServiceCommands = @{
    "logs-gateway" = "gateway"
    "logs-sidecar" = "sidecar"
    "logs-knowledge-base" = "knowledge-base-service"
    "logs-business-domain" = "business-domain-service"
    "logs-platform" = "platform-service"
    "logs-lightrag" = "lightrag"
    "logs-postgres" = "postgres"
    "logs-redis" = "redis"
    "logs-milvus" = "milvus"
    "logs-etcd" = "etcd"
    "logs-minio" = "minio"
}

$RebuildServiceCommands = @{
    "rebuild-gateway" = "gateway"
    "rebuild-sidecar" = "sidecar"
    "rebuild-knowledge-base" = "knowledge-base-service"
    "rebuild-business-domain" = "business-domain-service"
    "rebuild-platform" = "platform-service"
    "rebuild-frontend-gateway" = "frontend-gateway"
    "rebuild-shell-frontend" = "shell-frontend"
    "rebuild-core-business-frontend" = "core-business-frontend"
    "rebuild-platform-management-frontend" = "platform-management-frontend"
    "rebuild-ecosystem-management-frontend" = "ecosystem-management-frontend"
}

$RestartServiceCommands = @{
    "restart-gateway" = "gateway"
    "restart-sidecar" = "sidecar"
    "restart-knowledge-base" = "knowledge-base-service"
    "restart-business-domain" = "business-domain-service"
    "restart-platform" = "platform-service"
    "restart-frontend-gateway" = "frontend-gateway"
    "restart-shell-frontend" = "shell-frontend"
    "restart-core-business-frontend" = "core-business-frontend"
    "restart-platform-management-frontend" = "platform-management-frontend"
    "restart-ecosystem-management-frontend" = "ecosystem-management-frontend"
}

$ExecServiceCommands = @{
    "exec-gateway" = @("gateway", "bash")
    "exec-sidecar" = @("sidecar", "bash")
    "exec-knowledge-base" = @("knowledge-base-service", "bash")
    "exec-business-domain" = @("business-domain-service", "bash")
    "exec-platform" = @("platform-service", "bash")
    "exec-lightrag" = @("lightrag", "bash")
    "exec-shell-frontend" = @("shell-frontend", "sh")
    "shell-gateway" = @("gateway", "bash")
    "shell-sidecar" = @("sidecar", "bash")
    "shell-knowledge-base" = @("knowledge-base-service", "bash")
    "shell-business-domain" = @("business-domain-service", "bash")
    "shell-platform" = @("platform-service", "bash")
    "shell-lightrag" = @("lightrag", "bash")
    "shell-frontend" = @("shell-frontend", "sh")
}

if ($BuildServiceCommands.ContainsKey($Command)) {
    Build-PythonBase
    Enable-ComposeBake
    Invoke-Compose -Mode Base -ComposeArgs @("build", $BuildServiceCommands[$Command])
    exit $LASTEXITCODE
}
if ($UpServiceCommands.ContainsKey($Command)) {
    Invoke-Compose -Mode Dev -ComposeArgs @("up", "-d", $UpServiceCommands[$Command])
    exit $LASTEXITCODE
}
if ($DownServiceCommands.ContainsKey($Command)) {
    Invoke-Compose -Mode Dev -ComposeArgs @("stop", $DownServiceCommands[$Command])
    Invoke-Compose -Mode Dev -ComposeArgs @("rm", "-f", $DownServiceCommands[$Command])
    exit $LASTEXITCODE
}
if ($LogsServiceCommands.ContainsKey($Command)) {
    Invoke-Compose -Mode Dev -ComposeArgs @("logs", "-f", "--tail=100", $LogsServiceCommands[$Command])
    exit $LASTEXITCODE
}
if ($RebuildServiceCommands.ContainsKey($Command)) {
    Build-PythonBase
    Enable-ComposeBake
    Invoke-Compose -Mode Dev -ComposeArgs @("build", $RebuildServiceCommands[$Command])
    Invoke-Compose -Mode Dev -ComposeArgs @("up", "-d", $RebuildServiceCommands[$Command])
    exit $LASTEXITCODE
}
if ($RestartServiceCommands.ContainsKey($Command)) {
    Invoke-Compose -Mode Dev -ComposeArgs @("restart", $RestartServiceCommands[$Command])
    exit $LASTEXITCODE
}
if ($ExecServiceCommands.ContainsKey($Command)) {
    $execArgs = $ExecServiceCommands[$Command]
    Invoke-Compose -Mode Dev -ComposeArgs (@("exec", $execArgs[0]) + $execArgs[1])
    exit $LASTEXITCODE
}

switch ($Command) {
    "help" {
        Write-Host "=== Jonex Platform Commands ===" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "本地开发:"
        Write-Host "  .\jonex.ps1 dev                         启动中间件 + RAG，并提示下一步"
        Write-Host "  .\jonex.ps1 dev-deps-up                 启动 postgres/redis/etcd/minio/milvus/lightrag/atomic-rag"
        Write-Host "  .\jonex.ps1 dev-infra-up                只启动 postgres/redis/etcd/minio/milvus"
        Write-Host "  .\jonex.ps1 dev-rag-up                  只启动 lightrag/atomic-rag"
        Write-Host "  .\jonex.ps1 dev-deps-down               停止本地开发依赖"
        Write-Host "  .\jonex.ps1 dev-deps-logs               查看本地开发依赖日志"
        Write-Host ""
        Write-Host "本机后端:"
        Write-Host "  .\jonex.ps1 dev-backend                 分窗口启动 gateway/sidecar/各能力服务"
        Write-Host "  .\jonex.ps1 dev-backend-gateway         API Gateway: http://localhost:8000"
        Write-Host "  .\jonex.ps1 dev-backend-sidecar         Sidecar: http://localhost:8001"
        Write-Host "  .\jonex.ps1 dev-backend-knowledge-base  知识库服务: http://localhost:8003"
        Write-Host "  .\jonex.ps1 dev-backend-business-domain 业务领域服务: http://localhost:8005"
        Write-Host "  .\jonex.ps1 dev-backend-platform        平台管理服务: http://localhost:8006"
        Write-Host "  .\jonex.ps1 dev-backend-server          服务器基础设施 + 分窗口启动本机后端"
        Write-Host "  .\jonex.ps1 dev-backend-server-gateway  服务器基础设施 + API Gateway"
        Write-Host "  .\jonex.ps1 dev-backend-server-sidecar  服务器基础设施 + Sidecar"
        Write-Host "  .\jonex.ps1 dev-backend-server-knowledge-base 服务器基础设施 + 知识库服务"
        Write-Host "  .\jonex.ps1 dev-backend-server-business-domain 服务器基础设施 + 业务领域服务"
        Write-Host "  .\jonex.ps1 dev-backend-server-platform 服务器基础设施 + 平台管理服务"
        Write-Host "    需要先准备 .env.server-local（可由 .env.server-local.example 复制）"
        Write-Host ""
        Write-Host "本机前端:"
        Write-Host "  .\jonex.ps1 frontends-install           安装/同步 frontends workspace 依赖"
        Write-Host "  .\jonex.ps1 dev-gateway                 启动 Dev Gateway: http://localhost:8080"
        Write-Host "  .\jonex.ps1 dev-frontend                启动 shell + core/platform/ecosystem"
        Write-Host "  .\jonex.ps1 dev-frontend-all            启动全部当前前端"
        Write-Host "  .\jonex.ps1 dev-frontend-shell          Shell: http://localhost:5173"
        Write-Host "  .\jonex.ps1 dev-frontend-core           Core Business: http://localhost:5175"
        Write-Host "  .\jonex.ps1 dev-frontend-ecosystem      Ecosystem Management: http://localhost:5176"
        Write-Host "  .\jonex.ps1 dev-frontend-platform       Platform Management: http://localhost:5177"
        Write-Host ""
        Write-Host "本地 Docker 联调:"
        Write-Host "  .\jonex.ps1 init                        初始化 deploy/.env 与 deploy/.env.rag"
        Write-Host "  .\jonex.ps1 build-base                  强制重建 jonex/python-base 基础镜像"
        Write-Host "  .\jonex.ps1 docker-local-build           构建镜像"
        Write-Host "  .\jonex.ps1 docker-local-up              启动整套服务"
        Write-Host "  .\jonex.ps1 docker-local-down            停止并删除整套服务"
        Write-Host "  .\jonex.ps1 docker-local-ps              查看状态"
        Write-Host "  .\jonex.ps1 docker-local-logs            查看日志"
        Write-Host "  .\jonex.ps1 docker-local-restart         重启整套服务"
        Write-Host ""
        Write-Host "  # 以上命令也可省略 docker- 前缀，如:"
        Write-Host "  .\jonex.ps1 local-up / local-down / local-ps / local-logs"
        Write-Host ""
        Write-Host "GPU/服务器 Docker:"
        Write-Host "  .\jonex.ps1 docker-gpu-build             构建 GPU 镜像"
        Write-Host "  .\jonex.ps1 docker-gpu-up                启动 GPU 部署"
        Write-Host "  .\jonex.ps1 docker-gpu-down              停止 GPU 部署"
        Write-Host "  .\jonex.ps1 docker-gpu-ps                查看 GPU 部署状态"
        Write-Host "  .\jonex.ps1 docker-gpu-logs              查看 GPU 部署日志"
        Write-Host ""
        Write-Host "  # 以上命令也可省略 docker- 前缀，如:"
        Write-Host "  .\jonex.ps1 gpu-up / gpu-down / gpu-ps / gpu-logs / gpu-build"
        Write-Host ""
        Write-Host "单服务操作:"
        Write-Host "  .\jonex.ps1 rebuild gateway             删除旧镜像→--no-cache 构建→启动（源码调试）"
        Write-Host "  .\jonex.ps1 docker-local-restart-service gateway"
        Write-Host "  .\jonex.ps1 docker-local-logs-service knowledge-base-service"
        Write-Host ""
        Write-Host "性能耗时日志（摄入链路埋点）:"
        Write-Host "  .\jonex.ps1 perf                        汇总查看 ingest_timing + reconcile_timing"
        Write-Host "  .\jonex.ps1 perf-ingest                 worker 分阶段耗时 ingest_timing（atomic-rag）"
        Write-Host "  .\jonex.ps1 perf-reconcile              对账入图库耗时 reconcile_timing（knowledge-base-service）"
        Write-Host "  .\jonex.ps1 perf-chunk                  LightRAG 内部 chunk_timing（lightrag，拆 extract/merge/persist）"
        Write-Host "  .\jonex.ps1 perf-thinking               关思考注入 thinking.disabled（llm-gateway）"
        Write-Host "  .\jonex.ps1 perf-extract                抽取场景调用 lightrag_extract（llm-gateway，看 latency/token）"
        Write-Host "  .\jonex.ps1 perf-search                 本体检索 RAG 线路耗时 ontology_search_timing（多库检索/融合）"
        Write-Host "  .\jonex.ps1 perf-audit                  审计表耗时 audit_logs.duration_ms（postgres）"
        Write-Host "  # 默认查最近 1000 行历史，可传行数覆盖: .\jonex.ps1 perf-ingest 5000"
    }

    "init" {
        Write-Host "=== 初始化环境 ===" -ForegroundColor Cyan
        $envFile = Join-Path $DeployDir ".env"
        $envExample = Join-Path $DeployDir ".env.example"
        if (-not (Test-Path $envFile)) {
            Copy-Item $envExample $envFile
            Write-Host "已创建平台配置: deploy\.env" -ForegroundColor Green
        } else {
            Write-Host "平台配置已存在: deploy\.env" -ForegroundColor Yellow
        }

        $envRagFile = Join-Path $DeployDir ".env.rag"
        $envRagExample = Join-Path $DeployDir ".env.rag.example"
        if (-not (Test-Path $envRagFile)) {
            Copy-Item $envRagExample $envRagFile
            Write-Host "已创建 RAG 配置: deploy\.env.rag" -ForegroundColor Green
        } else {
            Write-Host "RAG 配置已存在: deploy\.env.rag" -ForegroundColor Yellow
        }
        Write-Host "下一步: 按需修改 deploy\.env 和 deploy\.env.rag" -ForegroundColor Yellow
    }

    "version" {
        & docker --version
        Push-Location $DeployDir
        try {
            & docker compose version
        }
        finally {
            Pop-Location
        }
    }

    { $_ -in "build", "build-local", "local-build", "docker-local-build", "build-prod", "build-server" } {
        Build-PythonBase
        Enable-ComposeBake
        Invoke-Compose -Mode Base -ComposeArgs @("build")
    }

    "build-gpu" { Build-PythonBase; Invoke-Compose -Mode Base -ComposeArgs @("build") }
    "docker-gpu-build" { Build-PythonBase; Invoke-Compose -Mode Base -ComposeArgs @("build") }
    "gpu-build" { Build-PythonBase; Invoke-Compose -Mode Base -ComposeArgs @("build") }

    "build-base" {
        Write-Host "=== 强制重建共享基础镜像 jonex/python-base:local ===" -ForegroundColor Cyan
        Push-Location $RepoRoot
        try {
            & docker buildx build --load --no-cache -t jonex/python-base:local -f deploy/docker/python-base.Dockerfile .
            if ($LASTEXITCODE -ne 0) { throw "python-base 镜像构建失败（退出码 $LASTEXITCODE）" }
        }
        finally {
            Pop-Location
        }
    }
    "build-infra" { Invoke-Compose -Mode Base -ComposeArgs (@("build") + $MiddlewareServices) }
    "build-rag" { Enable-ComposeBake; Invoke-Compose -Mode Base -ComposeArgs (@("build") + $RagServices) }
    "build-backend" { Build-PythonBase; Enable-ComposeBake; Invoke-Compose -Mode Base -ComposeArgs (@("build") + $BackendServices) }
    "build-frontend" { Enable-ComposeBake; Invoke-Compose -Mode Base -ComposeArgs (@("build") + $FrontendServices) }

    "build-service" {
        Require-Service
        Build-PythonBase
        Enable-ComposeBake
        Invoke-Compose -Mode Base -ComposeArgs @("build", $Service)
    }

    { $_ -in "up", "up-local", "local-up", "up-detached", "docker-local-up" } {
        Write-Host "=== 本地 Docker 部署 ===" -ForegroundColor Cyan
        Invoke-Compose -Mode Dev -ComposeArgs @("up", "-d")
        Write-Host "服务启动中: .\jonex.ps1 docker-local-ps / .\jonex.ps1 docker-local-logs"
    }

    { $_ -in "up-gpu", "gpu-up", "docker-gpu-up" } {
        Write-Host "=== GPU Docker 部署 ===" -ForegroundColor Cyan
        Invoke-Compose -Mode GpuDev -ComposeArgs @("up", "-d")
    }

    { $_ -in "up-server", "up-prod" } {
        Write-Host "=== 生产 Docker 部署 ===" -ForegroundColor Cyan
        Invoke-Compose -Mode Base -ComposeArgs @("up", "-d")
    }

    { $_ -in "up-infra", "dev-infra-up" } {
        Invoke-Compose -Mode Dev -ComposeArgs (@("up", "-d") + $MiddlewareServices)
    }

    { $_ -in "up-rag", "dev-rag-up" } {
        Invoke-Compose -Mode Dev -ComposeArgs (@("up", "-d") + $RagServices)
    }

    "up-backend" {
        Invoke-Compose -Mode Dev -ComposeArgs (@("up", "-d") + $BackendServices)
    }

    "up-frontend" {
        Invoke-Compose -Mode Dev -ComposeArgs (@("up", "-d") + $FrontendServices)
    }

    { $_ -in "up-service", "local-up-service", "docker-local-up-service" } {
        Require-Service
        Invoke-Compose -Mode Dev -ComposeArgs @("up", "-d", $Service)
    }

    { $_ -in "gpu-up-service", "docker-gpu-up-service" } {
        Require-Service
        Invoke-Compose -Mode GpuDev -ComposeArgs @("up", "-d", $Service)
    }

    "up-milvus" {
        Invoke-Compose -Mode Dev -ComposeArgs @("up", "-d", "etcd", "minio", "milvus")
    }

    { $_ -in "down", "down-local", "local-down", "docker-local-down" } {
        Invoke-Compose -Mode Dev -ComposeArgs @("down")
    }

    { $_ -in "down-gpu", "gpu-down", "docker-gpu-down" } {
        Invoke-Compose -Mode Gpu -ComposeArgs @("down")
    }

    { $_ -in "down-server", "down-prod" } {
        Invoke-Compose -Mode Base -ComposeArgs @("down")
    }

    "down-v" {
        Write-Host "警告: 这会删除数据库、Redis、MinIO、Milvus 等数据卷。" -ForegroundColor Red
        $confirm = Read-Host "确认继续? (y/N)"
        if ($confirm -ne "y") { exit 1 }
        Invoke-Compose -Mode Dev -ComposeArgs @("down", "-v")
    }

    "stop" {
        Invoke-Compose -Mode Dev -ComposeArgs @("stop")
    }

    "stop-service" {
        Require-Service
        Invoke-Compose -Mode Dev -ComposeArgs @("stop", $Service)
    }

    { $_ -in "down-service", "local-down-service", "docker-local-down-service" } {
        Require-Service
        Invoke-Compose -Mode Dev -ComposeArgs @("stop", $Service)
        Invoke-Compose -Mode Dev -ComposeArgs @("rm", "-f", $Service)
    }

    { $_ -in "gpu-down-service", "docker-gpu-down-service" } {
        Require-Service
        Invoke-Compose -Mode Gpu -ComposeArgs @("stop", $Service)
        Invoke-Compose -Mode Gpu -ComposeArgs @("rm", "-f", $Service)
    }

    "down-frontend" {
        Invoke-Compose -Mode Dev -ComposeArgs (@("stop") + $FrontendServices)
        Invoke-Compose -Mode Dev -ComposeArgs (@("rm", "-f") + $FrontendServices)
    }

    { $_ -in "restart", "local-restart", "docker-local-restart" } {
        Invoke-Compose -Mode Dev -ComposeArgs @("restart")
    }

    { $_ -in "restart-gpu", "gpu-restart", "docker-gpu-restart" } {
        Invoke-Compose -Mode GpuDev -ComposeArgs @("restart")
    }

    { $_ -in "restart-server", "restart-prod" } {
        Invoke-Compose -Mode Base -ComposeArgs @("restart")
    }

    { $_ -in "restart-service", "local-restart-service", "docker-local-restart-service" } {
        Require-Service
        Invoke-Compose -Mode Dev -ComposeArgs @("restart", $Service)
    }

    { $_ -in "gpu-restart-service", "docker-gpu-restart-service" } {
        Require-Service
        Invoke-Compose -Mode GpuDev -ComposeArgs @("restart", $Service)
    }

    { $_ -in "recreate-service", "local-recreate-service", "docker-local-recreate-service" } {
        Require-Service
        Invoke-Compose -Mode Dev -ComposeArgs @("up", "-d", "--force-recreate", $Service)
    }

    { $_ -in "rebuild", "rebuild-service", "local-rebuild-service", "docker-local-rebuild-service" } {
        Require-Service
        if ($ServiceNameMap.ContainsKey($Service)) { $Service = $ServiceNameMap[$Service] }
        Build-PythonBase
        Enable-ComposeBake

        Push-Location $DeployDir
        try {

            Write-Host "=== 构建新镜像: $Service ===" -ForegroundColor Cyan
            & docker compose $ComposeDevFiles build --no-cache $Service
            if ($LASTEXITCODE -ne 0) { throw "构建失败（退出码 $LASTEXITCODE）" }


            Write-Host "=== 清理旧镜像 ===" -ForegroundColor Cyan
            & docker image prune -f --filter "dangling=true" 2>&1 | Out-Null


            Write-Host "=== 启动服务: $Service ===" -ForegroundColor Cyan
            & docker compose $ComposeDevFiles up -d --force-recreate $Service
        }
        finally {
            Pop-Location
        }
    }

    { $_ -in "gpu-rebuild-service", "docker-gpu-rebuild-service" } {
        Require-Service
        Build-PythonBase
        Invoke-Compose -Mode Base -ComposeArgs @("build", $Service)
        Invoke-Compose -Mode GpuDev -ComposeArgs @("up", "-d", $Service)
    }

    { $_ -in "ps", "local-ps", "docker-local-ps" } { Invoke-Compose -Mode Dev -ComposeArgs @("ps") }
    { $_ -in "ps-gpu", "gpu-ps", "docker-gpu-ps" } { Invoke-Compose -Mode Gpu -ComposeArgs @("ps") }
    { $_ -in "ps-server", "ps-prod" } { Invoke-Compose -Mode Base -ComposeArgs @("ps") }

    { $_ -in "logs", "local-logs", "docker-local-logs" } {
        Invoke-Compose -Mode Dev -ComposeArgs @("logs", "-f", "--tail=100")
    }

    { $_ -in "logs-gpu", "gpu-logs", "docker-gpu-logs" } {
        Invoke-Compose -Mode Gpu -ComposeArgs @("logs", "-f", "--tail=100")
    }

    { $_ -in "logs-server", "logs-prod" } {
        Invoke-Compose -Mode Base -ComposeArgs @("logs", "-f", "--tail=100")
    }

    { $_ -in "logs-service", "local-logs-service", "docker-local-logs-service" } {
        Require-Service
        Invoke-Compose -Mode Dev -ComposeArgs @("logs", "-f", "--tail=100", $Service)
    }

    { $_ -in "gpu-logs-service", "docker-gpu-logs-service" } {
        Require-Service
        Invoke-Compose -Mode Gpu -ComposeArgs @("logs", "-f", "--tail=100", $Service)
    }

    "logs-infra" {
        Invoke-Compose -Mode Dev -ComposeArgs (@("logs", "-f", "--tail=100") + $MiddlewareServices)
    }

    "logs-rag" {
        Invoke-Compose -Mode Dev -ComposeArgs (@("logs", "-f", "--tail=100") + $RagServices)
    }

    "logs-backend" {
        Invoke-Compose -Mode Dev -ComposeArgs (@("logs", "-f", "--tail=100") + $BackendServices)
    }

    "logs-frontend" {
        Invoke-Compose -Mode Dev -ComposeArgs (@("logs", "-f", "--tail=100") + $FrontendServices)
    }

    { $_ -in "dev", "dev-local" } {
        Invoke-Compose -Mode Dev -ComposeArgs (@("up", "-d") + $MiddlewareServices + $RagServices)
        Write-Host ""
        Write-Host "本地开发依赖已启动。"
        Write-Host "后端: .\jonex.ps1 dev-backend"
        Write-Host "前端: .\jonex.ps1 dev-frontend"
    }

    { $_ -in "dev-deps-up" } {
        Invoke-Compose -Mode Dev -ComposeArgs (@("up", "-d") + $MiddlewareServices + $RagServices)
    }

    { $_ -in "dev-deps-down" } {
        Invoke-Compose -Mode Dev -ComposeArgs (@("stop") + $MiddlewareServices + $RagServices)
    }

    { $_ -in "dev-deps-logs" } {
        Invoke-Compose -Mode Dev -ComposeArgs (@("logs", "-f", "--tail=100") + $MiddlewareServices + $RagServices)
    }

    { $_ -in "dev-backend" } {
        Invoke-Compose -Mode Dev -ComposeArgs (@("up", "-d") + $MiddlewareServices + $RagServices)
        Write-Host "=== 分窗口启动本机后端 ===" -ForegroundColor Cyan
        @(
            "dev-backend-sidecar",
            "dev-backend-gateway",
            "dev-backend-knowledge-base",
            "dev-backend-business-domain",
            "dev-backend-platform"
        ) | ForEach-Object { Start-BackendProcess $_ }
    }

    { $_ -in "dev-backend-server" } {
        Write-Host "=== 分窗口启动本机后端（服务器基础设施模式） ===" -ForegroundColor Cyan
        @(
            "dev-backend-server-sidecar",
            "dev-backend-server-gateway",
            "dev-backend-server-knowledge-base",
            "dev-backend-server-business-domain",
            "dev-backend-server-platform"
        ) | ForEach-Object { Start-BackendProcess $_ }
    }

    { $_ -in "dev-backend-gateway" } { Invoke-Backend "gateway" }
    { $_ -in "dev-backend-sidecar", "dev-sidecar" } { Invoke-Backend "sidecar" }
    { $_ -in "dev-backend-knowledge-base", "dev-knowledge-base" } { Invoke-Backend "knowledge-base" }
    { $_ -in "dev-backend-business-domain", "dev-business-domain" } { Invoke-Backend "business-domain" }
    { $_ -in "dev-backend-platform", "dev-platform" } { Invoke-Backend "platform" }
    { $_ -in "dev-backend-server-gateway" } { Invoke-BackendServerInfra "gateway" }
    { $_ -in "dev-backend-server-sidecar" } { Invoke-BackendServerInfra "sidecar" }
    { $_ -in "dev-backend-server-knowledge-base" } { Invoke-BackendServerInfra "knowledge-base" }
    { $_ -in "dev-backend-server-business-domain" } { Invoke-BackendServerInfra "business-domain" }
    { $_ -in "dev-backend-server-platform" } { Invoke-BackendServerInfra "platform" }

    { $_ -in "frontends-install", "frontend-install" } {
        Write-Host "=== 安装/同步 frontends workspace 依赖 ===" -ForegroundColor Cyan
        Invoke-Pnpm -PnpmArgs @("install")
    }

    { $_ -in "dev-gateway", "frontend-gateway-dev" } {
        Write-Host "=== 启动 Dev Gateway: http://localhost:8080 ===" -ForegroundColor Cyan
        Invoke-Pnpm -PnpmArgs @("run", "dev:gateway")
    }

    { $_ -in "dev-frontend", "frontend", "dev-all" } {
        Write-Host "=== 启动 shell + core/platform/ecosystem ===" -ForegroundColor Cyan
        Invoke-Pnpm -PnpmArgs (@("-r", "--parallel") + $MainFrontendFilters + @("run", "dev"))
    }

    { $_ -in "dev-frontend-all", "frontend-all" } {
        Write-Host "=== 启动全部当前前端 ===" -ForegroundColor Cyan
        Invoke-Pnpm -PnpmArgs (@("-r", "--parallel") + $MainFrontendFilters + @("run", "dev"))
    }

    { $_ -in "dev-frontend-shell", "frontend-shell", "dev-shell" } {
        Write-Host "=== 启动 Shell Dev Server: http://localhost:5173 ===" -ForegroundColor Cyan
        Invoke-Pnpm -PnpmArgs @("--filter", $ShellApp, "run", "dev")
    }

    { $_ -in "dev-frontend-core", "frontend-core", "dev-core-business" } {
        Write-Host "=== 启动 Core Business Dev Server: http://localhost:5175 ===" -ForegroundColor Cyan
        Invoke-Pnpm -PnpmArgs @("--filter", $CoreApp, "run", "dev")
    }

    { $_ -in "dev-frontend-platform", "frontend-platform", "dev-platform-management" } {
        Write-Host "=== 启动 Platform Management Dev Server: http://localhost:5177 ===" -ForegroundColor Cyan
        Invoke-Pnpm -PnpmArgs @("--filter", $PlatformApp, "run", "dev")
    }

    { $_ -in "dev-frontend-ecosystem", "frontend-ecosystem", "dev-ecosystem-management" } {
        Write-Host "=== 启动 Ecosystem Management Dev Server: http://localhost:5176 ===" -ForegroundColor Cyan
        Invoke-Pnpm -PnpmArgs @("--filter", $EcosystemApp, "run", "dev")
    }

    { $_ -in "preview-core", "preview-core-business" } {
        Invoke-Pnpm -PnpmArgs @("--filter", $CoreApp, "run", "build")
        Invoke-Pnpm -PnpmArgs @("--filter", $CoreApp, "run", "preview")
    }

    { $_ -in "preview-platform", "preview-platform-management" } {
        Invoke-Pnpm -PnpmArgs @("--filter", $PlatformApp, "run", "build")
        Invoke-Pnpm -PnpmArgs @("--filter", $PlatformApp, "run", "preview")
    }

    { $_ -in "preview-ecosystem", "preview-ecosystem-management" } {
        Invoke-Pnpm -PnpmArgs @("--filter", $EcosystemApp, "run", "build")
        Invoke-Pnpm -PnpmArgs @("--filter", $EcosystemApp, "run", "preview")
    }

    "preview-all" {
        Invoke-Pnpm -PnpmArgs (@("-r") + $MainFrontendFilters + @("run", "build"))
        Invoke-Pnpm -PnpmArgs (@("-r", "--parallel") + $MainFrontendFilters + @("run", "preview"))
    }

    "restart-frontend" {
        Invoke-Compose -Mode Dev -ComposeArgs (@("restart") + $FrontendServices)
    }

    "scale-knowledge-base" {
        Invoke-Compose -Mode Dev -ComposeArgs @("up", "-d", "--scale", "knowledge-base-service=$N", "knowledge-base-service")
    }

    "pull-lightrag" {
        Invoke-Compose -Mode Gpu -ComposeArgs @("pull", "lightrag")
    }

    "init-db" {
        Set-LocalBackendEnv
        Invoke-Compose -Mode Dev -ComposeArgs @("exec", "postgres", "psql", "-U", $env:DB_USERNAME, "-d", $env:DB_NAME, "-f", "/docker-entrypoint-initdb.d/init.sql")
    }

    "exec-postgres" {
        Set-LocalBackendEnv
        Invoke-Compose -Mode Dev -ComposeArgs @("exec", "postgres", "psql", "-U", $env:DB_USERNAME, "-d", $env:DB_NAME)
    }

    "shell-postgres" {
        Set-LocalBackendEnv
        Invoke-Compose -Mode Dev -ComposeArgs @("exec", "postgres", "psql", "-U", $env:DB_USERNAME, "-d", $env:DB_NAME)
    }

    "test" {
        Invoke-Compose -Mode Dev -ComposeArgs @("ps")
        Write-Host ""
        Write-Host "检查 API Gateway..."
        try { Invoke-WebRequest -UseBasicParsing http://localhost:8000/health | Select-Object -ExpandProperty Content } catch { Write-Host "API Gateway 未就绪或未启动" -ForegroundColor Yellow }
        Write-Host ""
        Write-Host "检查 Sidecar..."
        try { Invoke-WebRequest -UseBasicParsing http://localhost:8001/health | Select-Object -ExpandProperty Content } catch { Write-Host "Sidecar 未就绪或未启动" -ForegroundColor Yellow }
    }

    "clean" {
        Write-Host "警告: 这会删除本项目容器、数据卷和相关镜像。" -ForegroundColor Red
        $confirm = Read-Host "确认继续? (y/N)"
        if ($confirm -ne "y") { exit 1 }
        Invoke-Compose -Mode Dev -ComposeArgs @("down", "-v", "--rmi", "all")
        & docker image prune -f
    }

    { $_ -in "perf", "perf-all" } {
        Write-Host "=== ingest_timing (atomic-rag, worker 分阶段耗时) ===" -ForegroundColor Cyan
        Invoke-PerfLog "atomic-rag" "ingest_timing"
        Write-Host ""
        Write-Host "=== reconcile_timing (knowledge-base-service, 入图库/端到端耗时) ===" -ForegroundColor Cyan
        Invoke-PerfLog "knowledge-base-service" "reconcile_timing"
    }

    "perf-ingest" { Invoke-PerfLog "atomic-rag" "ingest_timing" }
    "perf-reconcile" { Invoke-PerfLog "knowledge-base-service" "reconcile_timing" }
    "perf-chunk" { Invoke-PerfLog "lightrag" "chunk_timing" }
    "perf-thinking" { Invoke-PerfLog "llm-gateway" "thinking.disabled" }
    "perf-extract" { Invoke-PerfLog "llm-gateway" "lightrag_extract" }
    "perf-search" { Invoke-PerfLog "knowledge-base-service" "ontology_search_timing" }

    "perf-audit" {
        Set-LocalBackendEnv
        Invoke-Compose -Mode Dev -ComposeArgs @("exec", "postgres", "psql", "-U", $env:DB_USERNAME, "-d", $env:DB_NAME, "-c", "SELECT created_at, action, outcome, duration_ms, resource_id, request_params FROM platform.audit_logs WHERE action IN ('document.parse_done','document.parse_failed','document.parse_recover') ORDER BY created_at DESC LIMIT 20;")
    }

    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host "Use: .\jonex.ps1 help"
        exit 1
    }
}
