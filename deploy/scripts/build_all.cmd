@echo off
REM ============================================================
REM Jonex Platform - optimized compose build (Windows cmd)
REM ------------------------------------------------------------
REM ASCII-only on purpose (cmd parses batch files in the OEM code
REM page; UTF-8 multibyte chars can break quoting/parsing).
REM
REM What it does:
REM   1) Build the shared base image jonex/python-base:local and
REM      load it into the local docker image store.
REM   2) Run COMPOSE_BAKE=1 docker compose build  -> parallel build
REM      (buildx bake delegation) producing the deploy-* images that
REM      `docker compose up` actually runs. The 7 backend services
REM      consume python-base via additional_contexts (FROM base).
REM
REM Run from anywhere; the script cd's to the repo root.
REM ============================================================

setlocal enableextensions
pushd "%~dp0..\.."

set "PYTHON_BASE_TAG=jonex/python-base:local"
set "COMPOSE_FILE=deploy/docker-compose.yml"

REM ---- concurrency cap = min(max(logical_cores,1),8) ----
set /a NPROC=%NUMBER_OF_PROCESSORS%
if %NPROC% LSS 1 set /a NPROC=1
if %NPROC% GTR 8 set /a NPROC=8
set "BUILDKIT_MAX_PARALLELISM=%NPROC%"

REM ---- delegate compose build to buildx bake (parallel + cache) ----
set "COMPOSE_BAKE=1"
REM bake filesystem entitlements (non-interactive)
set "BUILDX_BAKE_ENTITLEMENTS_FS=0"

echo [build_all] BUILDKIT_MAX_PARALLELISM=%NPROC%
echo [build_all] Step 1/2: building shared base image %PYTHON_BASE_TAG% ...

REM PowerShell wraps both steps to print total seconds (>=2 decimals)
REM and to propagate the failing exit code back to cmd.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s = Get-Date; docker buildx build --load -t '%PYTHON_BASE_TAG%' -f deploy/docker/python-base.Dockerfile .; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; Write-Host '[build_all] Step 2/2: parallel compose build (deploy-* images) ...'; docker compose -f '%COMPOSE_FILE%' build; $code = $LASTEXITCODE; $sec = ((Get-Date) - $s).TotalSeconds; Write-Host ('[build_all] total build time: {0:N2} s' -f $sec); exit $code"

if errorlevel 1 goto fail

echo [build_all] Build completed. Images are the compose deploy-* set; run: docker compose -f %COMPOSE_FILE% up -d
popd
endlocal & exit /b 0

:fail
echo [build_all] Build FAILED. See output above. 1>&2
popd
endlocal & exit /b 1
