
import uuid

from jonex_core.common import get_db_session

from capabilities.business_domain.repository import AdapterRepository
from capabilities.business_domain.services import _check_tenant


class AdapterService:


    async def list(self, tenant_id: str, offset: int = 0, limit: int = 20) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = AdapterRepository(session)
            items = await repo.list_all(tenant_id, offset, limit)
            total = await repo.count(tenant_id)
            return {"items": [o.to_dict() for o in items], "total": total, "offset": offset, "limit": limit}

    async def create(self, tenant_id: str, data: dict) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = AdapterRepository(session)
            obj = await repo.create(
                id=uuid.uuid4().hex, tenant_id=tenant_id,
                name=data["name"], adapter_type=data["adapter_type"],
                config_json=data.get("config_json", {}),
            )
            await session.commit()
            return obj.to_dict()

    async def update(self, adapter_id: str, tenant_id: str, data: dict) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = AdapterRepository(session)
            obj = await repo.update(adapter_id, tenant_id, **{
                k: v for k, v in data.items()
                if k in ("name", "config_json", "status") and v is not None
            })
            if obj is None:
                obj = await repo.get_required(adapter_id, tenant_id)
            await session.commit()
            return obj.to_dict()

    async def connect(self, adapter_id: str, tenant_id: str) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = AdapterRepository(session)
            await repo.get_required(adapter_id, tenant_id)
            await repo.update(adapter_id, tenant_id, status="connected")
            await session.commit()
            return {"status": "connected"}

    async def disconnect(self, adapter_id: str, tenant_id: str) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = AdapterRepository(session)
            await repo.get_required(adapter_id, tenant_id)
            await repo.update(adapter_id, tenant_id, status="disconnected")
            await session.commit()
            return {"status": "disconnected"}
