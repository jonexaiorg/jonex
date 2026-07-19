
import httpx
from fastapi import APIRouter, Query, Request

from jonex_core.common.config import get_config
from jonex_core.common.exceptions import CapabilityInvokeError

router = APIRouter()


async def _proxy_platform(request: Request, path: str):

    config = get_config()
    sidecar_url = config.SIDECAR_URL

    body = None
    if request.method in ("POST", "PUT", "PATCH"):
        body = await request.json()

    headers = {
        "X-API-Key": config.SIDECAR_API_KEY,
        "X-Request-ID": getattr(request.state, "request_id", ""),
        "X-Forwarded-For": request.client.host if request.client else "",
    }
    auth_header = request.headers.get("Authorization")
    if auth_header:
        headers["Authorization"] = auth_header
    tenant_header = request.headers.get("X-Tenant-ID")
    if tenant_header:
        headers["X-Tenant-ID"] = tenant_header


    target = f"{sidecar_url}/platform/{path}"
    if request.query_params:
        target += f"?{request.query_params}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if request.method in ("GET", "DELETE"):
                resp = await client.request(request.method, target, headers=headers)
            else:
                resp = await client.request(request.method, target, json=body, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json()
            except Exception:
                detail = {"message": e.response.text}
            raise CapabilityInvokeError(
                message=detail.get("message", f"Platform service error: HTTP {e.response.status_code}"),
            )




@router.get("/tenants", summary="获取租户列表")
async def list_tenants(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
):

    return await _proxy_platform(request, "tenants")

@router.post("/tenants", summary="创建租户")
async def create_tenant(request: Request):

    return await _proxy_platform(request, "tenants")

@router.get("/tenants/user-counts", summary="获取租户用户数统计")
async def get_tenant_user_counts(request: Request):

    return await _proxy_platform(request, "tenants/user-counts")


@router.get("/tenants/{tenant_id}", summary="获取租户详情")
async def get_tenant(tenant_id: str, request: Request):

    return await _proxy_platform(request, f"tenants/{tenant_id}")

@router.patch("/tenants/{tenant_id}", summary="更新租户")
async def update_tenant(tenant_id: str, request: Request):

    return await _proxy_platform(request, f"tenants/{tenant_id}")

@router.delete("/tenants/{tenant_id}", summary="删除租户")
async def delete_tenant(tenant_id: str, request: Request):

    return await _proxy_platform(request, f"tenants/{tenant_id}")




@router.get("/users/all", summary="获取全量用户列表")
async def list_all_users(request: Request):

    return await _proxy_platform(request, "users/all")


@router.get("/users", summary="获取用户列表")
async def list_users(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
):

    return await _proxy_platform(request, "users")


@router.post("/users", summary="创建用户")
async def create_user(request: Request):

    return await _proxy_platform(request, "users")


@router.get("/users/{user_id}", summary="获取用户详情")
async def get_user(user_id: int, request: Request):

    return await _proxy_platform(request, f"users/{user_id}")


@router.patch("/users/{user_id}", summary="更新用户")
async def update_user(user_id: int, request: Request):

    return await _proxy_platform(request, f"users/{user_id}")


@router.delete("/users/{user_id}", summary="删除用户")
async def delete_user(user_id: int, request: Request):

    return await _proxy_platform(request, f"users/{user_id}")


@router.get("/users/{user_id}/roles", summary="获取用户角色")
async def get_user_roles(user_id: int, request: Request):

    return await _proxy_platform(request, f"users/{user_id}/roles")


@router.put("/users/{user_id}/roles", summary="设置用户角色")
async def set_user_roles(user_id: int, request: Request):

    return await _proxy_platform(request, f"users/{user_id}/roles")




@router.get("/roles", summary="获取角色列表")
async def list_roles(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
):

    return await _proxy_platform(request, "roles")


@router.post("/roles", summary="创建角色")
async def create_role(request: Request):

    return await _proxy_platform(request, "roles")


@router.get("/roles/{role_id}", summary="获取角色详情")
async def get_role(role_id: int, request: Request):

    return await _proxy_platform(request, f"roles/{role_id}")


@router.patch("/roles/{role_id}", summary="更新角色")
async def update_role(role_id: int, request: Request):

    return await _proxy_platform(request, f"roles/{role_id}")


@router.delete("/roles/{role_id}", summary="删除角色")
async def delete_role(role_id: int, request: Request):

    return await _proxy_platform(request, f"roles/{role_id}")


@router.get("/roles/{role_id}/permissions", summary="获取角色权限")
async def get_role_permissions(role_id: int, request: Request):

    return await _proxy_platform(request, f"roles/{role_id}/permissions")


@router.put("/roles/{role_id}/permissions", summary="设置角色权限")
async def set_role_permissions(role_id: int, request: Request):

    return await _proxy_platform(request, f"roles/{role_id}/permissions")




@router.get("/permissions", summary="获取权限列表")
async def list_permissions(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=500, description="每页条数"),
):

    return await _proxy_platform(request, "permissions")




@router.get("/menus", summary="获取菜单树")
async def get_menus(request: Request):

    return await _proxy_platform(request, "menus")


@router.post("/menus", summary="创建菜单")
async def create_menu(request: Request):

    return await _proxy_platform(request, "menus")


@router.put("/menus/{menu_id}", summary="更新菜单")
async def update_menu(menu_id: int, request: Request):

    return await _proxy_platform(request, f"menus/{menu_id}")


@router.delete("/menus/{menu_id}", summary="删除菜单")
async def delete_menu(menu_id: int, request: Request):

    return await _proxy_platform(request, f"menus/{menu_id}")




@router.get("/frontend/apps", summary="获取前端应用清单")
async def get_frontend_manifest(request: Request):

    return await _proxy_platform(request, "frontend/apps")


@router.get("/applications", summary="获取应用列表")
async def list_applications(request: Request):

    return await _proxy_platform(request, "applications")


@router.post("/applications", summary="注册应用")
async def create_application(request: Request):

    return await _proxy_platform(request, "applications")


@router.get("/applications/{app_id}", summary="获取应用详情")
async def get_application(app_id: int, request: Request):

    return await _proxy_platform(request, f"applications/{app_id}")


@router.patch("/applications/{app_id}", summary="更新应用")
async def update_application(app_id: int, request: Request):

    return await _proxy_platform(request, f"applications/{app_id}")


@router.delete("/applications/{app_id}", summary="删除应用")
async def delete_application(app_id: int, request: Request):

    return await _proxy_platform(request, f"applications/{app_id}")




@router.get("/system-configs", summary="获取系统配置列表")
async def list_system_configs(request: Request):

    return await _proxy_platform(request, "system-configs")


@router.put("/system-configs/{config_key}", summary="更新系统配置")
async def update_system_config(config_key: str, request: Request):

    return await _proxy_platform(request, f"system-configs/{config_key}")




@router.get("/audit-logs", summary="获取审计日志列表")
async def list_audit_logs(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    user_id: int = Query(None, description="用户 ID 过滤"),
    action: str = Query(None, description="操作类型过滤"),
):

    return await _proxy_platform(request, "audit-logs")


@router.get("/audit-logs/{log_id}", summary="获取审计日志详情")
async def get_audit_log(log_id: int, request: Request):

    return await _proxy_platform(request, f"audit-logs/{log_id}")




@router.get("/task-schedules", summary="获取任务调度列表")
async def list_task_schedules(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
):

    return await _proxy_platform(request, "task-schedules")


@router.post("/task-schedules", summary="创建任务调度")
async def create_task_schedule(request: Request):

    return await _proxy_platform(request, "task-schedules")


@router.get("/task-schedules/{task_id}", summary="获取任务调度详情")
async def get_task_schedule(task_id: int, request: Request):

    return await _proxy_platform(request, f"task-schedules/{task_id}")


@router.patch("/task-schedules/{task_id}", summary="更新任务调度")
async def update_task_schedule(task_id: int, request: Request):

    return await _proxy_platform(request, f"task-schedules/{task_id}")


@router.delete("/task-schedules/{task_id}", summary="删除任务调度")
async def delete_task_schedule(task_id: int, request: Request):

    return await _proxy_platform(request, f"task-schedules/{task_id}")


@router.post("/task-schedules/{task_id}/trigger", summary="触发任务调度")
async def trigger_task_schedule(task_id: int, request: Request):

    return await _proxy_platform(request, f"task-schedules/{task_id}/trigger")
