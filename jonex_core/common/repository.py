#!/usr/bin/python3



from typing import Any, Generic, Iterable, Optional, Sequence, TypeVar

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from jonex_core.common.exceptions import ResourceNotFoundError
from jonex_core.common.tenant import TenantContext, require_tenant

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):


    model: type[ModelT]

    def __init__(self, session: AsyncSession):
        self.session = session

    def _has_column(self, name: str) -> bool:
        return hasattr(self.model, name)

    def _primary_key(self):
        return getattr(self.model, "id")

    def _tenant_id(self, tenant_id: str | None) -> str:
        explicit = tenant_id if tenant_id is not None else TenantContext.get()
        return require_tenant(explicit)

    def _soft_delete_conditions(self) -> list[Any]:
        if self._has_column("is_deleted"):
            return [getattr(self.model, "is_deleted") == 0]
        return []

    def _tenant_conditions(self, tenant_id: str | None) -> list[Any]:
        if not self._has_column("tenant_id"):
            return []
        return [getattr(self.model, "tenant_id") == self._tenant_id(tenant_id)]

    def _default_order_by(self):
        if self._has_column("created_at"):
            return getattr(self.model, "created_at").desc()
        return self._primary_key()

    @staticmethod
    def _as_list(values: Iterable[Any] | None) -> list[Any]:
        return list(values or [])

    async def get_by_id(self, id_val: Any, tenant_id: str | None = None) -> Optional[ModelT]:
        conditions = [self._primary_key() == id_val, *self._soft_delete_conditions()]
        if tenant_id is not None or self._has_column("tenant_id"):
            conditions.extend(self._tenant_conditions(tenant_id))

        result = await self.session.execute(select(self.model).where(*conditions))
        return result.scalar_one_or_none()

    async def get_required(self, id_val: Any, tenant_id: str) -> ModelT:
        obj = await self.get_by_id(id_val, tenant_id)
        if obj is None:
            raise ResourceNotFoundError(
                message=f"{self.model.__name__} not found: {id_val}",
                details={"id": id_val, "tenant_id": tenant_id},
            )
        return obj

    async def list_all(
        self,
        tenant_id: str | None = None,
        offset: int = 0,
        limit: int = 20,
        extra_conditions: Sequence[Any] | None = None,
    ) -> list[ModelT]:
        conditions = [
            *self._tenant_conditions(tenant_id),
            *self._soft_delete_conditions(),
            *self._as_list(extra_conditions),
        ]
        stmt = (
            select(self.model)
            .where(*conditions)
            .order_by(self._default_order_by())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def count(
        self,
        tenant_id: str | None = None,
        *filters: Any,
        extra_conditions: Sequence[Any] | None = None,
    ) -> int:
        conditions = [*self._soft_delete_conditions(), *self._as_list(extra_conditions)]
        if self._has_column("tenant_id"):
            conditions.extend(self._tenant_conditions(tenant_id))
        elif tenant_id is not None and not isinstance(tenant_id, str):
            conditions.insert(0, tenant_id)
        conditions.extend(filters)

        result = await self.session.execute(
            select(func.count()).select_from(self.model).where(*conditions)
        )
        return result.scalar_one()

    async def create(self, *args: Any, **kwargs: Any) -> ModelT:
        if args:
            obj = args[0]
        else:
            obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update(
        self,
        id_or_obj: Any,
        tenant_id: str | None = None,
        **values: Any,
    ) -> Optional[ModelT]:
        obj = id_or_obj
        if not isinstance(id_or_obj, self.model):
            obj = await self.get_by_id(id_or_obj, tenant_id)
        if obj is None:
            return None
        for key, val in values.items():
            setattr(obj, key, val)
        await self.session.flush()
        return obj

    async def delete_soft(self, id_or_obj: Any, tenant_id: str | None = None) -> bool:
        obj = id_or_obj
        if not isinstance(id_or_obj, self.model):
            obj = await self.get_by_id(id_or_obj, tenant_id)
        if obj is None:
            return False
        if self._has_column("is_deleted"):
            setattr(obj, "is_deleted", 1)
        else:
            await self.session.delete(obj)
        await self.session.flush()
        return True

    async def delete_hard(self, id_or_obj: Any, tenant_id: str | None = None) -> bool:
        if isinstance(id_or_obj, self.model):
            await self.session.delete(id_or_obj)
            await self.session.flush()
            return True

        conditions = [self._primary_key() == id_or_obj]
        if tenant_id is not None or self._has_column("tenant_id"):
            conditions.extend(self._tenant_conditions(tenant_id))
        result = await self.session.execute(delete(self.model).where(*conditions))
        await self.session.flush()
        return result.rowcount > 0

    async def get_by_id_shared(self, id_val: Any) -> Optional[ModelT]:
        conditions = [self._primary_key() == id_val, *self._soft_delete_conditions()]
        result = await self.session.execute(select(self.model).where(*conditions))
        return result.scalar_one_or_none()

    async def get_required_shared(self, id_val: Any) -> ModelT:
        obj = await self.get_by_id_shared(id_val)
        if obj is None:
            raise ResourceNotFoundError(
                message=f"{self.model.__name__} not found: {id_val}",
                details={"id": id_val},
            )
        return obj

    async def list_all_shared(
        self,
        offset: int = 0,
        limit: int = 20,
        extra_conditions: Sequence[Any] | None = None,
    ) -> list[ModelT]:
        conditions = [*self._soft_delete_conditions(), *self._as_list(extra_conditions)]
        stmt = (
            select(self.model)
            .where(*conditions)
            .order_by(self._default_order_by())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def count_shared(
        self,
        extra_conditions: Sequence[Any] | None = None,
    ) -> int:
        conditions = [*self._soft_delete_conditions(), *self._as_list(extra_conditions)]
        result = await self.session.execute(
            select(func.count()).select_from(self.model).where(*conditions)
        )
        return result.scalar_one()

    async def update_shared(self, id_or_obj: Any, **values: Any) -> Optional[ModelT]:
        obj = id_or_obj
        if not isinstance(id_or_obj, self.model):
            obj = await self.get_by_id_shared(id_or_obj)
        if obj is None:
            return None
        for key, val in values.items():
            setattr(obj, key, val)
        await self.session.flush()
        return obj

    async def delete_soft_shared(self, id_or_obj: Any) -> bool:
        obj = id_or_obj
        if not isinstance(id_or_obj, self.model):
            obj = await self.get_by_id_shared(id_or_obj)
        if obj is None:
            return False
        if self._has_column("is_deleted"):
            setattr(obj, "is_deleted", 1)
        else:
            await self.session.delete(obj)
        await self.session.flush()
        return True

    async def delete_hard_shared(self, id_or_obj: Any) -> bool:
        if isinstance(id_or_obj, self.model):
            await self.session.delete(id_or_obj)
            await self.session.flush()
            return True
        result = await self.session.execute(
            delete(self.model).where(self._primary_key() == id_or_obj)
        )
        await self.session.flush()
        return result.rowcount > 0


__all__ = ["BaseRepository"]
