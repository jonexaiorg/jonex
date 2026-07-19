
from fastapi import APIRouter, Depends, Query, Request

from jonex_core.common.database import get_db
from jonex_core.common.response import success_response
from jonex_core.common.tenant import extract_tenant_id
from capabilities.platform.services.user_service import UserService
from capabilities.platform.services.role_service import RoleService
from capabilities.platform.services.menu_service import MenuService
from capabilities.platform.services.misc_services import (
    ApplicationService,
    PermissionService,
    SystemConfigService,
    TaskScheduleService,
    TenantService,
)
from capabilities.platform.dtos.platform import (
    UserCreateRequest,
    UserUpdateRequest,
    RoleCreateRequest,
    RoleUpdateRequest,
    RolePermissionsRequest,
    UserRolesRequest,
    MenuCreateRequest,
    MenuUpdateRequest,
    ApplicationCreateRequest,
    ApplicationUpdateRequest,
)
from capabilities.platform.dtos.misc import (
    SystemConfigUpdateRequest,
    TaskScheduleCreateRequest,
    TaskScheduleUpdateRequest,
    TenantCreateRequest,
    TenantUpdateRequest,
)

router = APIRouter()




@router.get("/tenants")
async def list_tenants(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    svc = TenantService(db)
    offset = (page - 1) * page_size
    result = await svc.list(offset, page_size)
    return success_response(data=result)


@router.get("/tenants/user-counts")
async def get_tenant_user_counts(db=Depends(get_db)):

    from capabilities.platform.services.user_service import UserService
    svc = UserService(db)
    counts = await svc.get_user_counts()
    return success_response(data=counts)


@router.post("/tenants")
async def create_tenant(
    req: TenantCreateRequest,
    db=Depends(get_db),
):
    svc = TenantService(db)
    result = await svc.create(req)
    return success_response(data=result, message="Tenant created successfully")


@router.get("/tenants/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    db=Depends(get_db),
):
    svc = TenantService(db)
    result = await svc.get(tenant_id)
    return success_response(data=result)


@router.patch("/tenants/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    req: TenantUpdateRequest,
    db=Depends(get_db),
):
    svc = TenantService(db)
    result = await svc.update(tenant_id, req)
    return success_response(data=result, message="Tenant updated successfully")


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    db=Depends(get_db),
):
    svc = TenantService(db)
    await svc.delete(tenant_id)
    return success_response(message="Tenant deleted successfully")




@router.get("/users/all")
async def list_all_users(db=Depends(get_db)):

    from capabilities.platform.services.user_service import UserService
    svc = UserService(db)
    result = await svc.list_all_users()
    return success_response(data={"items": [r.dict() for r in result], "total": len(result)})


@router.get("/users")
async def list_users(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    tenant_id = extract_tenant_id(request)
    svc = UserService(db)
    offset = (page - 1) * page_size
    result = await svc.list_users(tenant_id, offset, page_size)
    return success_response(data=result.dict())


@router.post("/users")
async def create_user(request: Request, req: UserCreateRequest, db=Depends(get_db)):
    tenant_id = extract_tenant_id(request)
    svc = UserService(db)
    result = await svc.create(tenant_id, req)
    return success_response(data=result.dict())


@router.get("/users/{user_id}")
async def get_user(request: Request, user_id: int, db=Depends(get_db)):
    tenant_id = extract_tenant_id(request)
    svc = UserService(db)
    result = await svc.get(tenant_id, user_id)
    return success_response(data=result.dict())


@router.patch("/users/{user_id}")
async def update_user(request: Request, user_id: int, req: UserUpdateRequest, db=Depends(get_db)):
    tenant_id = extract_tenant_id(request)
    svc = UserService(db)
    result = await svc.update(tenant_id, user_id, req)
    return success_response(data=result.dict())


@router.delete("/users/{user_id}")
async def delete_user(request: Request, user_id: int, db=Depends(get_db)):
    tenant_id = extract_tenant_id(request)
    svc = UserService(db)
    await svc.delete(tenant_id, user_id)
    return success_response(message="User deleted successfully")


@router.get("/users/{user_id}/roles")
async def get_user_roles(request: Request, user_id: int, db=Depends(get_db)):
    tenant_id = extract_tenant_id(request)
    svc = UserService(db)
    roles = await svc.get_roles(tenant_id, user_id)
    return success_response(data={"role_ids": roles})


@router.put("/users/{user_id}/roles")
async def set_user_roles(request: Request, user_id: int, req: UserRolesRequest, db=Depends(get_db)):
    tenant_id = extract_tenant_id(request)
    svc = UserService(db)
    await svc.set_roles(tenant_id, user_id, req.role_ids)
    return success_response(message="User roles updated successfully")




@router.get("/roles")
async def list_roles(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    tenant_id = extract_tenant_id(request)
    svc = RoleService(db)
    offset = (page - 1) * page_size
    result = await svc.list_roles(tenant_id, offset, page_size)
    return success_response(data=result.dict())


@router.post("/roles")
async def create_role(request: Request, req: RoleCreateRequest, db=Depends(get_db)):
    tenant_id = extract_tenant_id(request)
    svc = RoleService(db)
    result = await svc.create(tenant_id, req)
    return success_response(data=result.dict())


@router.get("/roles/{role_id}")
async def get_role(request: Request, role_id: int, db=Depends(get_db)):
    tenant_id = extract_tenant_id(request)
    svc = RoleService(db)
    result = await svc.get(tenant_id, role_id)
    return success_response(data=result.dict())


@router.patch("/roles/{role_id}")
async def update_role(request: Request, role_id: int, req: RoleUpdateRequest, db=Depends(get_db)):
    tenant_id = extract_tenant_id(request)
    svc = RoleService(db)
    result = await svc.update(tenant_id, role_id, req)
    return success_response(data=result.dict())


@router.delete("/roles/{role_id}")
async def delete_role(request: Request, role_id: int, db=Depends(get_db)):
    tenant_id = extract_tenant_id(request)
    svc = RoleService(db)
    await svc.delete(tenant_id, role_id)
    return success_response(message="Role deleted successfully")


@router.get("/roles/{role_id}/permissions")
async def get_role_permissions(request: Request, role_id: int, db=Depends(get_db)):
    tenant_id = extract_tenant_id(request)
    svc = RoleService(db)
    perms = await svc.get_permissions(tenant_id, role_id)
    return success_response(data={"permission_ids": perms})


@router.get("/roles/{role_id}/users")
async def get_role_users(request: Request, role_id: int, db=Depends(get_db)):
    tenant_id = extract_tenant_id(request)
    svc = RoleService(db)
    users = await svc.get_users(tenant_id, role_id)
    return success_response(data={"user_ids": users})


@router.put("/roles/{role_id}/permissions")
async def set_role_permissions(
    request: Request,
    role_id: int,
    req: RolePermissionsRequest,
    db=Depends(get_db),
):
    tenant_id = extract_tenant_id(request)
    svc = RoleService(db)
    await svc.set_permissions(tenant_id, role_id, req.permission_ids)
    return success_response(message="Role permissions updated successfully")




@router.get("/permissions")
async def list_permissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db=Depends(get_db),
):
    svc = PermissionService(db)
    offset = (page - 1) * page_size
    result = await svc.list_permissions(offset, page_size)
    return success_response(data=result.dict())




@router.get("/menus")
async def get_menus(db=Depends(get_db)):
    svc = MenuService(db)
    result = await svc.get_tree()
    return success_response(data=result.dict())


@router.post("/menus")
async def create_menu(req: MenuCreateRequest, db=Depends(get_db)):
    svc = MenuService(db)
    result = await svc.create(req)
    return success_response(data=result.dict())


@router.put("/menus/{menu_id}")
async def update_menu(menu_id: int, req: MenuUpdateRequest, db=Depends(get_db)):
    svc = MenuService(db)
    result = await svc.update(menu_id, req)
    return success_response(data=result.dict())


@router.delete("/menus/{menu_id}")
async def delete_menu(menu_id: int, db=Depends(get_db)):
    svc = MenuService(db)
    await svc.delete(menu_id)
    return success_response(message="Menu deleted successfully")




@router.get("/frontend/apps")
async def get_frontend_manifest(db=Depends(get_db)):
    svc = ApplicationService(db)
    result = await svc.get_frontend_manifest()
    return success_response(data=result.dict())


@router.get("/applications")
async def list_applications(db=Depends(get_db)):
    svc = ApplicationService(db)
    result = await svc.list_apps()
    return success_response(data=result.dict())


@router.post("/applications")
async def create_application(req: ApplicationCreateRequest, db=Depends(get_db)):
    svc = ApplicationService(db)
    result = await svc.create(req)
    return success_response(data=result.dict())


@router.get("/applications/{app_id}")
async def get_application(app_id: int, db=Depends(get_db)):
    svc = ApplicationService(db)
    result = await svc.get(app_id)
    return success_response(data=result.dict())


@router.patch("/applications/{app_id}")
async def update_application(app_id: int, req: ApplicationUpdateRequest, db=Depends(get_db)):
    svc = ApplicationService(db)
    result = await svc.update(app_id, req)
    return success_response(data=result.dict())


@router.delete("/applications/{app_id}")
async def delete_application(app_id: int, db=Depends(get_db)):
    svc = ApplicationService(db)
    await svc.delete(app_id)
    return success_response(message="Application deleted successfully")




@router.get("/system-configs")
async def list_system_configs(db=Depends(get_db)):
    svc = SystemConfigService(db)
    result = await svc.list_configs()
    return success_response(data=result.dict())


@router.put("/system-configs/{config_key}")
async def update_system_config(config_key: str, req: SystemConfigUpdateRequest, db=Depends(get_db)):
    svc = SystemConfigService(db)
    result = await svc.update_config(config_key, req)
    return success_response(data=result.dict())




@router.get("/task-schedules")
async def list_task_schedules(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    tenant_id = extract_tenant_id(request)
    svc = TaskScheduleService(db)
    offset = (page - 1) * page_size
    result = await svc.list_tasks(tenant_id, offset, page_size)
    return success_response(data=result.dict())


@router.post("/task-schedules")
async def create_task_schedule(request: Request, req: TaskScheduleCreateRequest, db=Depends(get_db)):
    tenant_id = extract_tenant_id(request)
    svc = TaskScheduleService(db)
    result = await svc.create(tenant_id, req)
    return success_response(data=result.dict())


@router.get("/task-schedules/{task_id}")
async def get_task_schedule(request: Request, task_id: int, db=Depends(get_db)):
    tenant_id = extract_tenant_id(request)
    svc = TaskScheduleService(db)
    result = await svc.get(tenant_id, task_id)
    return success_response(data=result.dict())


@router.patch("/task-schedules/{task_id}")
async def update_task_schedule(
    request: Request,
    task_id: int,
    req: TaskScheduleUpdateRequest,
    db=Depends(get_db),
):
    tenant_id = extract_tenant_id(request)
    svc = TaskScheduleService(db)
    result = await svc.update(tenant_id, task_id, req)
    return success_response(data=result.dict())


@router.delete("/task-schedules/{task_id}")
async def delete_task_schedule(request: Request, task_id: int, db=Depends(get_db)):
    tenant_id = extract_tenant_id(request)
    svc = TaskScheduleService(db)
    await svc.delete(tenant_id, task_id)
    return success_response(message="Task deleted successfully")


@router.post("/task-schedules/{task_id}/trigger")
async def trigger_task_schedule(request: Request, task_id: int, db=Depends(get_db)):
    tenant_id = extract_tenant_id(request)
    svc = TaskScheduleService(db)
    task = await svc.get(tenant_id, task_id)
    return success_response(
        data={"task_id": task.id, "name": task.name, "triggered": True},
        message=f"Task {task.name} triggered successfully"
    )
