@echo off

















setlocal enableextensions
pushd "%~dp0..\.."

set "PYTHON_BASE_TAG=jonex/python-base:local"
set "COMPOSE_FILE=deploy/docker-compose.yml"


set /a NPROC=%NUMBER_OF_PROCESSORS%
if %NPROC% LSS 1 set /a NPROC=1
if %NPROC% GTR 8 set /a NPROC=8
set "BUILDKIT_MAX_PARALLELISM=%NPROC%"


set "COMPOSE_BAKE=1"

set "BUILDX_BAKE_ENTITLEMENTS_FS=0"

echo [build_all] BUILDKIT_MAX_PARALLELISM=%NPROC%
echo [build_all] Step 1/2: building shared base image %PYTHON_BASE_TAG% ...



powershell -NoProfile -ExecutionPolicy Bypass -Command "$s = Get-Date; docker buildx build --load -t '%PYTHON_BASE_TAG%' -f deploy/docker/python-base.Dockerfile .; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; Write-Host '[build_all] Step 2/2: parallel compose build (deploy-* images) ...'; docker compose -f '%COMPOSE_FILE%' build; $code = $LASTEXITCODE; $sec = ((Get-Date) - $s).TotalSeconds; Write-Host ('[build_all] total build time: {0:N2} s' -f $sec); exit $code"

if errorlevel 1 goto fail

echo [build_all] Build completed. Images are the compose deploy-* set; run: docker compose -f %COMPOSE_FILE% up -d
popd
endlocal & exit /b 0

:fail
echo [build_all] Build FAILED. See output above. 1>&2
popd
endlocal & exit /b 1
