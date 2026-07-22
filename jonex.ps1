# Jonex Platform PowerShell Script

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

$DeployDir = "deploy"

switch ($Command) {
    "help" {
        Write-Host "=== Jonex Platform Commands ===" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Basic commands:"
        Write-Host "  .\jonex.ps1 init      - Copy .env file"
        Write-Host "  .\jonex.ps1 build     - Build all images"
        Write-Host "  .\jonex.ps1 up        - Start all services"
        Write-Host "  .\jonex.ps1 down      - Stop all services"
        Write-Host "  .\jonex.ps1 ps        - Show status"
        Write-Host "  .\jonex.ps1 logs      - View all logs"
        Write-Host ""
        Write-Host "Single service:"
        Write-Host "  .\jonex.ps1 up-postgres - Start PostgreSQL"
        Write-Host "  .\jonex.ps1 up-redis    - Start Redis"
        Write-Host "  .\jonex.ps1 up-milvus   - Start Milvus (+etcd, minio)"
        Write-Host "  .\jonex.ps1 up-lightrag - Start LightRAG RAG service"
        Write-Host "  .\jonex.ps1 pull-lightrag - Pull latest LightRAG image"
        Write-Host ""
        Write-Host "Logs:"
        Write-Host "  .\jonex.ps1 logs-milvus - View Milvus logs"
        Write-Host "  .\jonex.ps1 logs-postgres - View PostgreSQL logs"
        Write-Host "  .\jonex.ps1 logs-redis - View Redis logs"
        Write-Host "  .\jonex.ps1 logs-gateway - View API Gateway logs"
        Write-Host "  .\jonex.ps1 logs-frontend - View Frontend logs"
        Write-Host "  .\jonex.ps1 logs-lightrag - View LightRAG logs"
        Write-Host "  .\jonex.ps1 logs-knowledge-base - View Knowledge Base logs"
        Write-Host ""
        Write-Host "Frontend (dev):"
        Write-Host "  .\jonex.ps1 frontend-install "
        Write-Host "  .\jonex.ps1 frontend         "
        Write-Host "  .\jonex.ps1 frontend-all    "
        Write-Host "  .\jonex.ps1 frontend-shell  "
        Write-Host "  .\jonex.ps1 frontend-core    "
        Write-Host "  .\jonex.ps1 frontend-platform "
        Write-Host "  .\jonex.ps1 frontend-ecosystem"
        Write-Host ""
        Write-Host "Frontend (Docker):"
        Write-Host "  .\jonex.ps1 up-prod     - Start in production mode"
        Write-Host "  .\jonex.ps1 build-frontend - Build frontend image"
        Write-Host "  .\jonex.ps1 up-frontend - Start frontend service"
        Write-Host "  .\jonex.ps1 down-frontend - Stop frontend service"
        Write-Host "  .\jonex.ps1 shell-frontend - Enter frontend container"
    }

    "init" {
        Write-Host "=== Initialize Environment ===" -ForegroundColor Cyan
        $envFile = Join-Path $DeployDir ".env"
        $envExample = Join-Path $DeployDir ".env.example"
        if (-not (Test-Path $envFile)) {
            Copy-Item $envExample $envFile
            Write-Host "Created: $envFile" -ForegroundColor Green
        } else {
            Write-Host "Config file exists: $envFile" -ForegroundColor Yellow
        }
        $envRagFile = Join-Path $DeployDir ".env.rag"
        $envRagExample = Join-Path $DeployDir ".env.rag.example"
        if (-not (Test-Path $envRagFile)) {
            Copy-Item $envRagExample $envRagFile
            Write-Host "Created: $envRagFile" -ForegroundColor Green
        } else {
            Write-Host "RAG config exists: $envRagFile" -ForegroundColor Yellow
        }
        Write-Host "Please edit deploy\.env and deploy\.env.rag before starting services" -ForegroundColor Yellow
    }

    "build" {
        Write-Host "=== Building Docker Images ===" -ForegroundColor Cyan
        Push-Location $DeployDir
        docker-compose build
        Pop-Location
    }

    "build-knowledge-base" {
        Write-Host "=== Building Knowledge Base Image ===" -ForegroundColor Cyan
        Push-Location $DeployDir
        docker-compose build knowledge-base-service
        Pop-Location
    }

    "up" {
        Write-Host "=== Starting All Services ===" -ForegroundColor Cyan
        Push-Location $DeployDir
        docker-compose up -d
        Pop-Location
    }

    "down" {
        Write-Host "=== Stopping All Services ===" -ForegroundColor Cyan
        Push-Location $DeployDir
        docker-compose down
        Pop-Location
    }

    "ps" {
        Push-Location $DeployDir
        docker-compose ps
        Pop-Location
    }

    "logs" {
        Push-Location $DeployDir
        docker-compose logs -f --tail=100
        Pop-Location
    }

    "logs-milvus" {
        Push-Location $DeployDir
        docker-compose logs -f --tail=100 milvus
        Pop-Location
    }

    "logs-postgres" {
        Push-Location $DeployDir
        docker-compose logs -f --tail=100 postgres
        Pop-Location
    }

    "logs-redis" {
        Push-Location $DeployDir
        docker-compose logs -f --tail=100 redis
        Pop-Location
    }

    "logs-gateway" {
        Push-Location $DeployDir
        docker-compose logs -f --tail=100 gateway
        Pop-Location
    }

    "logs-frontend" {
        Push-Location $DeployDir
        docker-compose logs -f --tail=100 frontend
        Pop-Location
    }

    "build-frontend" {
        Write-Host "=== Building Frontend Image ===" -ForegroundColor Cyan
        Push-Location $DeployDir
        docker-compose build frontend
        Pop-Location
    }

    "up-prod" {
        Write-Host "=== Starting Production Mode ===" -ForegroundColor Green
        Push-Location $DeployDir
        docker-compose -f docker-compose.yml up -d
        Pop-Location
    }

    "up-frontend" {
        Push-Location $DeployDir
        docker-compose up -d frontend
        Pop-Location
    }

    "down-frontend" {
        Push-Location $DeployDir
        docker-compose stop frontend
        Pop-Location
    }

    "frontend-install" {
        Write-Host "=== Installing Frontend Dependencies ===" -ForegroundColor Cyan
        Push-Location "frontends"
        pnpm install
        Pop-Location
    }

    { $_ -in "frontend", "mac-frontend" } {
        Write-Host "=== Starting shell + 3 TS sub-apps ===" -ForegroundColor Cyan
        Push-Location "frontends"
        pnpm -r --parallel --filter @jonex/shell --filter @jonex/core-business --filter @jonex/platform-management --filter @jonex/ecosystem-management run dev
        Pop-Location
    }

    { $_ -in "frontend-all", "mac-frontend-all" } {
        Write-Host "=== Starting all configured frontends ===" -ForegroundColor Cyan
        Push-Location "frontends"
        pnpm -r --parallel --filter @jonex/shell --filter @jonex/core-business --filter @jonex/platform-management --filter @jonex/ecosystem-management run dev
        Pop-Location
    }

    { $_ -in "frontend-shell", "mac-frontend-shell" } {
        Write-Host "=== Starting Shell Dev Server (port 5174) ===" -ForegroundColor Cyan
        Push-Location "frontends"
        pnpm --filter @jonex/shell run dev
        Pop-Location
    }

    "dev-shell" {
        Write-Host "=== Starting Shell Dev Server (port 5174) ===" -ForegroundColor Cyan
        Push-Location "frontends\shell"
        pnpm install
        pnpm dev
        Pop-Location
    }

    { $_ -in "frontend-core", "mac-frontend-core" } {
        Write-Host "=== Starting Core Business Dev Server (port 5175) ===" -ForegroundColor Cyan
        Push-Location "frontends"
        pnpm --filter @jonex/core-business run dev
        Pop-Location
    }

    { $_ -in "frontend-platform", "mac-frontend-platform" } {
        Write-Host "=== Starting Platform Management Dev Server (port 5177) ===" -ForegroundColor Cyan
        Push-Location "frontends"
        pnpm --filter @jonex/platform-management run dev
        Pop-Location
    }

    { $_ -in "frontend-ecosystem", "mac-frontend-ecosystem" } {
        Write-Host "=== Starting Ecosystem Management Dev Server (port 5176) ===" -ForegroundColor Cyan
        Push-Location "frontends"
        pnpm --filter @jonex/ecosystem-management run dev
        Pop-Location
    }


    "shell-frontend" {
        Push-Location $DeployDir
        docker-compose exec frontend sh
        Pop-Location
    }

    "up-postgres" {
        Push-Location $DeployDir
        docker-compose up -d postgres
        Pop-Location
    }

    "up-redis" {
        Push-Location $DeployDir
        docker-compose up -d redis
        Pop-Location
    }

    "up-milvus" {
        Push-Location $DeployDir
        docker-compose up -d etcd minio milvus
        Pop-Location
    }

    "up-lightrag" {
        Write-Host "=== Starting LightRAG RAG Service ===" -ForegroundColor Cyan
        Push-Location $DeployDir
        docker-compose up -d lightrag
        Pop-Location
    }

    "up-knowledge-base" {
        Write-Host "=== Starting Knowledge Base Service ===" -ForegroundColor Cyan
        Push-Location $DeployDir
        docker-compose up -d knowledge-base-service
        Pop-Location
    }

    "down-knowledge-base" {
        Push-Location $DeployDir
        docker-compose stop knowledge-base-service
        Pop-Location
    }

    "pull-lightrag" {
        Write-Host "=== Pulling LightRAG Latest Image ===" -ForegroundColor Cyan
        Push-Location $DeployDir
        docker-compose pull lightrag
        Pop-Location
    }

    "logs-lightrag" {
        Push-Location $DeployDir
        docker-compose logs -f --tail=100 lightrag
        Pop-Location
    }

    "logs-knowledge-base" {
        Push-Location $DeployDir
        docker-compose logs -f --tail=100 knowledge-base-service
        Pop-Location
    }

    "shell-lightrag" {
        Push-Location $DeployDir
        docker-compose exec lightrag bash
        Pop-Location
    }

    "shell-knowledge-base" {
        Push-Location $DeployDir
        docker-compose exec knowledge-base-service bash
        Pop-Location
    }

    default {
        Write-Host "Unknown command. Use: .\jonex.ps1 help" -ForegroundColor Red
    }
}
