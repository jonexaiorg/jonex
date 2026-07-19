
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from jonex_core.common.exceptions import ResourceNotFoundError, ResourceConflictError
from jonex_core.common.tenant import require_tenant
from capabilities.platform.models.application import Application
from capabilities.platform.models.permission import Permission
from capabilities.platform.models.system_config import SystemConfig
from capabilities.platform.models.task_schedule import TaskSchedule
from capabilities.platform.repository.application_repository import ApplicationRepository
from capabilities.platform.repository.permission_repository import PermissionRepository
from capabilities.platform.repository.system_config_repository import SystemConfigRepository
from capabilities.platform.repository.task_schedule_repository import TaskScheduleRepository
from capabilities.platform.dtos.platform import (
    ApplicationCreateRequest,
    ApplicationUpdateRequest,
    ApplicationResponse,
    ApplicationListResponse,
    FrontendManifestEntry,
    FrontendManifestFallback,
    FrontendManifestHealth,
    FrontendManifestPermissions,
    FrontendManifestRemote,
    FrontendManifestResponse,
    FrontendManifestRoutes,
    FrontendManifestVersion,
    PermissionResponse,
    PermissionListResponse,
)
from capabilities.platform.dtos.misc import (
    SystemConfigUpdateRequest,
    SystemConfigResponse,
    SystemConfigListResponse,
    TaskScheduleCreateRequest,
    TaskScheduleUpdateRequest,
    TaskScheduleResponse,
    TaskScheduleListResponse,
)

logger = logging.getLogger(__name__)


FRONTEND_SCOPE_BY_APP_CODE = {
    "core-business": "coreBusiness",
    "platform-management": "platformManagement",
    "ecosystem-management": "ecosystemManagement",
}

FRONTEND_CATEGORY_BY_APP_CODE = {
    "core-business": "core-business",
    "platform-management": "platform-management",
    "ecosystem-management": "ecosystem-management",
}

FRONTEND_ICON_BY_APP_CODE = {
    "core-business": "SearchOutlined",
    "platform-management": "SettingOutlined",
    "ecosystem-management": "AppstoreOutlined",
}

FRONTEND_ROLES_BY_APP_CODE = {
    "platform-management": ["admin"],
}




class ApplicationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ApplicationRepository(session)

    async def create(self, req: ApplicationCreateRequest) -> ApplicationResponse:
        existing = await self.repo.get_by_code(req.app_code)
        if existing:
            raise ResourceConflictError(message=f"Application code already exists: {req.app_code}")
        app = Application(
            app_code=req.app_code,
            name=req.name,
            entry_path=req.entry_path,
            icon=req.icon,
            description=req.description,
            sort_order=req.sort_order,
        )
        self.session.add(app)
        await self.session.flush()
        return ApplicationResponse.from_orm(app)

    async def get(self, app_id: int) -> ApplicationResponse:
        app = await self.repo.get_by_id_shared(app_id)
        if not app or app.is_deleted:
            raise ResourceNotFoundError(message=f"Application not found: {app_id}")
        return ApplicationResponse.from_orm(app)

    async def list_apps(self) -> ApplicationListResponse:
        items = await self.repo.list_active()
        total = len(items)
        return ApplicationListResponse(
            total=total,
            items=[ApplicationResponse.from_orm(a) for a in items],
        )

    async def get_frontend_manifest(self) -> FrontendManifestResponse:
        items = await self.repo.list_active()
        apps = [
            self._to_frontend_manifest_entry(app)
            for app in items
            if app.app_code != "shell"
        ]
        return FrontendManifestResponse(
            updatedAt=datetime.now(timezone.utc).isoformat(),
            apps=apps,
        )

    async def update(self, app_id: int, req: ApplicationUpdateRequest) -> ApplicationResponse:
        app = await self.repo.get_by_id_shared(app_id)
        if not app or app.is_deleted:
            raise ResourceNotFoundError(message=f"Application not found: {app_id}")
        update_data = req.dict(exclude_unset=True)
        for key, val in update_data.items():
            setattr(app, key, val)
        await self.session.flush()
        return ApplicationResponse.from_orm(app)

    async def delete(self, app_id: int) -> None:
        app = await self.repo.get_by_id_shared(app_id)
        if not app or app.is_deleted:
            raise ResourceNotFoundError(message=f"Application not found: {app_id}")
        await self.repo.delete_soft_shared(app)

    def _to_frontend_manifest_entry(self, app: Application) -> FrontendManifestEntry:
        code = app.app_code
        base_path = app.entry_path if app.entry_path and app.entry_path.startswith("/apps/") else f"/apps/{code}"
        standalone_base = f"/{code}"
        standalone_url = f"{standalone_base}/"
        remote_entry = f"/remotes/{code}/assets/remoteEntry.js"
        version_url = f"/remotes/{code}/version.json"
        roles = FRONTEND_ROLES_BY_APP_CODE.get(code, ["admin", "user"])
        scope = FRONTEND_SCOPE_BY_APP_CODE.get(code, self._to_camel_case(code))

        return FrontendManifestEntry(
            id=code,
            name=app.name,
            description=app.description,
            enabled=app.status == 1,
            order=app.sort_order,
            category=FRONTEND_CATEGORY_BY_APP_CODE.get(code, "business"),
            icon=app.icon or FRONTEND_ICON_BY_APP_CODE.get(code),
            routes=FrontendManifestRoutes(
                hostedBase=base_path,
                standaloneBase=standalone_base,
            ),
            remote=FrontendManifestRemote(
                scope=scope,
                module="./Mount",
                entry=remote_entry,
            ),
            standaloneUrl=standalone_url,
            basePath=base_path,
            entry=remote_entry,
            scope=scope,
            module="./Mount",
            apiPrefix=f"/api/v1/{code}",
            roles=roles,
            health=FrontendManifestHealth(url=version_url),
            permissions=FrontendManifestPermissions(visibleRoles=roles),
            fallback=FrontendManifestFallback(url=standalone_url),
            version=FrontendManifestVersion(source=version_url),
        )

    @staticmethod
    def _to_camel_case(value: str) -> str:
        parts = [p for p in value.split("-") if p]
        if not parts:
            return value
        return parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])




class PermissionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PermissionRepository(session)

    async def list_permissions(self, offset: int = 0, limit: int = 100) -> PermissionListResponse:
        items = await self.repo.list_all_sorted(offset, limit)
        total = await self.repo.count_shared()
        return PermissionListResponse(
            total=total,
            items=[PermissionResponse.from_orm(p) for p in items],
        )




class SystemConfigService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SystemConfigRepository(session)

    async def list_configs(self) -> SystemConfigListResponse:
        items = await self.repo.list_all_shared(limit=1000)
        return SystemConfigListResponse(
            items=[SystemConfigResponse.from_orm(c) for c in items],
        )

    async def update_config(self, config_key: str, req: SystemConfigUpdateRequest) -> SystemConfigResponse:
        cfg = await self.repo.get_by_key(config_key)
        if not cfg:
            raise ResourceNotFoundError(message=f"Configuration not found: {config_key}")
        if req.config_value is not None:
            cfg.config_value = req.config_value
        if req.description is not None:
            cfg.description = req.description
        await self.session.flush()
        return SystemConfigResponse.from_orm(cfg)




class TaskScheduleService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TaskScheduleRepository(session)

    async def create(self, tenant_id: str, req: TaskScheduleCreateRequest) -> TaskScheduleResponse:
        tenant_id = require_tenant(tenant_id)
        task = TaskSchedule(
            tenant_id=tenant_id,
            name=req.name,
            task_type=req.task_type,
            cron_expr=req.cron_expr,
            config_json=req.config_json,
        )
        self.session.add(task)
        await self.session.flush()
        return TaskScheduleResponse.from_orm(task)

    async def get(self, tenant_id: str, task_id: int) -> TaskScheduleResponse:
        tenant_id = require_tenant(tenant_id)
        task = await self.repo.get_by_id(task_id, tenant_id)
        if not task or task.is_deleted:
            raise ResourceNotFoundError(message=f"Task not found: {task_id}")
        return TaskScheduleResponse.from_orm(task)

    async def list_tasks(
        self, tenant_id: str, offset: int = 0, limit: int = 20
    ) -> TaskScheduleListResponse:
        tenant_id = require_tenant(tenant_id)
        items = await self.repo.list_by_tenant(tenant_id, offset, limit)
        total = await self.repo.count_by_tenant(tenant_id)
        return TaskScheduleListResponse(
            total=total,
            items=[TaskScheduleResponse.from_orm(t) for t in items],
        )

    async def update(
        self, tenant_id: str, task_id: int, req: TaskScheduleUpdateRequest
    ) -> TaskScheduleResponse:
        tenant_id = require_tenant(tenant_id)
        task = await self.repo.get_by_id(task_id, tenant_id)
        if not task or task.is_deleted:
            raise ResourceNotFoundError(message=f"Task not found: {task_id}")
        update_data = req.dict(exclude_unset=True)
        for key, val in update_data.items():
            setattr(task, key, val)
        await self.session.flush()
        return TaskScheduleResponse.from_orm(task)

    async def delete(self, tenant_id: str, task_id: int) -> None:
        tenant_id = require_tenant(tenant_id)
        task = await self.repo.get_by_id(task_id, tenant_id)
        if not task or task.is_deleted:
            raise ResourceNotFoundError(message=f"Task not found: {task_id}")
        await self.repo.delete_soft(task, tenant_id)




class TenantService:
    def __init__(self, db: AsyncSession):
        from capabilities.platform.repository.tenant_repository import TenantRepository
        from capabilities.platform.models.tenant import Tenant
        self.repo = TenantRepository(db)
        self.Tenant = Tenant

    @staticmethod
    def _to_dict(t) -> dict:
        return {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "status": t.status,
            "plan_type": t.plan_type,
            "expire_time": t.expire_time.isoformat() if t.expire_time else None,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }

    async def list(self, offset: int = 0, limit: int = 20) -> dict:
        items = await self.repo.list_all_shared(offset, limit)
        total = await self.repo.count_shared()
        return {"items": [self._to_dict(t) for t in items], "total": total}

    async def get(self, tenant_id: str) -> dict:
        t = await self.repo.get_required_shared(tenant_id)
        return self._to_dict(t)

    async def create(self, req) -> dict:
        t = self.Tenant(
            id=req.id, name=req.name, description=req.description,
            plan_type=req.plan_type, expire_time=req.expire_time,
        )
        self.repo.session.add(t)
        await self.repo.session.flush()
        return self._to_dict(t)

    async def update(self, tenant_id: str, req) -> dict:
        t = await self.repo.get_required_shared(tenant_id)
        updates = req.dict(exclude_unset=True)
        for k, v in updates.items():
            setattr(t, k, v)
        await self.repo.session.flush()
        return self._to_dict(t)

    async def delete(self, tenant_id: str) -> None:
        t = await self.repo.get_required_shared(tenant_id)
        await self.repo.delete_soft_shared(t)
