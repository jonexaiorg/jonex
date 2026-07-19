
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from jonex_core.common.exceptions import ResourceNotFoundError, ResourceConflictError
from jonex_core.common.tenant import require_tenant
from capabilities.platform.models.user import User
from capabilities.platform.repository.role_repository import RoleRepository
from capabilities.platform.repository.user_repository import UserRepository
from capabilities.platform.repository.user_role_repository import UserRoleRepository
from jonex_core.security.user_auth import get_user_auth
from capabilities.platform.dtos.platform import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserListResponse,
)

logger = logging.getLogger(__name__)


class UserService:


    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = UserRepository(session)
        self.role_repo = RoleRepository(session)
        self.user_role_repo = UserRoleRepository(session)
        self.user_auth = get_user_auth()

    async def create(self, tenant_id: str, req: UserCreateRequest) -> UserResponse:
        tenant_id = require_tenant(tenant_id)
        existing = await self.repo.get_by_username(tenant_id, req.username)
        if existing:
            raise ResourceConflictError(message=f"Username already exists: {req.username}")

        user = User(
            tenant_id=tenant_id,
            username=req.username,
            password_hash=self.user_auth.hash_password(req.password),
            display_name=req.display_name,
            email=req.email,
            role=req.role,
        )
        self.session.add(user)
        await self.session.flush()
        logger.info(f"Created user: {user.username} (id={user.id})")
        return UserResponse.from_orm(user)

    async def get(self, tenant_id: str, user_id: int) -> UserResponse:
        tenant_id = require_tenant(tenant_id)
        user = await self.repo.get_by_id(user_id, tenant_id)
        if not user or user.is_deleted:
            raise ResourceNotFoundError(message=f"User not found: {user_id}")
        return UserResponse.from_orm(user)

    async def list_users(
        self, tenant_id: str, offset: int = 0, limit: int = 20
    ) -> UserListResponse:
        tenant_id = require_tenant(tenant_id)
        items = await self.repo.list_by_tenant(tenant_id, offset, limit)
        total = await self.repo.count_by_tenant(tenant_id)
        return UserListResponse(
            total=total,
            items=[UserResponse.from_orm(u) for u in items],
        )

    async def update(self, tenant_id: str, user_id: int, req: UserUpdateRequest) -> UserResponse:
        tenant_id = require_tenant(tenant_id)
        user = await self.repo.get_by_id(user_id, tenant_id)
        if not user or user.is_deleted:
            raise ResourceNotFoundError(message=f"User not found: {user_id}")

        update_data = req.dict(exclude_unset=True)
        for key, val in update_data.items():
            setattr(user, key, val)
        await self.session.flush()
        logger.info(f"Updated user: {user.username} (id={user.id})")
        return UserResponse.from_orm(user)

    async def delete(self, tenant_id: str, user_id: int) -> None:
        tenant_id = require_tenant(tenant_id)
        user = await self.repo.get_by_id(user_id, tenant_id)
        if not user or user.is_deleted:
            raise ResourceNotFoundError(message=f"User not found: {user_id}")
        await self.repo.delete_soft(user, tenant_id)
        logger.info(f"Deleted user: {user.username} (id={user.id})")

    async def get_roles(self, tenant_id: str, user_id: int) -> list[int]:
        tenant_id = require_tenant(tenant_id)
        user = await self.repo.get_by_id(user_id, tenant_id)
        if not user or user.is_deleted:
            raise ResourceNotFoundError(message=f"User not found: {user_id}")
        return list(await self.user_role_repo.get_role_ids(tenant_id, user_id))

    async def set_roles(self, tenant_id: str, user_id: int, role_ids: list[int]) -> None:
        tenant_id = require_tenant(tenant_id)
        user = await self.repo.get_by_id(user_id, tenant_id)
        if not user or user.is_deleted:
            raise ResourceNotFoundError(message=f"User not found: {user_id}")

        normalized_role_ids = list(dict.fromkeys(role_ids))
        for role_id in normalized_role_ids:
            role = await self.role_repo.get_by_id(role_id, tenant_id)
            if not role or role.is_deleted:
                raise ResourceNotFoundError(message=f"Role not found: {role_id}")

        await self.user_role_repo.set_roles(tenant_id, user_id, normalized_role_ids)
        logger.info(f"Set user roles: user_id={user_id}, roles={normalized_role_ids}")

    async def list_all_users(self) -> list:

        users = await self.repo.list_all_shared(0, 10000)
        return [self._to_response(u) for u in users if not u.is_deleted]

    def _to_response(self, user) -> dict:
        from capabilities.platform.dtos.platform import UserResponse
        return UserResponse.from_orm(user)

    async def get_user_counts(self) -> dict[str, int]:

        users = await self.repo.list_all_shared(0, 10000)
        counts: dict[str, int] = {}
        for u in users:
            if not u.is_deleted:
                counts[u.tenant_id] = counts.get(u.tenant_id, 0) + 1
        return counts
