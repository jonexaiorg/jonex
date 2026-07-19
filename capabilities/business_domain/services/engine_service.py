
import uuid

from jonex_core.common import get_db_session

from capabilities.business_domain.repository import (
    DataAccessMethodRepository,
    ParserConfigRepository,
    ModelProviderRepository,
)
from capabilities.business_domain.services import _check_tenant


class EngineService:



    async def list_access_methods(self, tenant_id: str, offset: int = 0, limit: int = 20) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = DataAccessMethodRepository(session)
            items = await repo.list_all(tenant_id, offset, limit)
            total = await repo.count(tenant_id)
            return {"items": [o.to_dict() for o in items], "total": total, "offset": offset, "limit": limit}

    async def create_access_method(self, tenant_id: str, data: dict) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = DataAccessMethodRepository(session)
            obj = await repo.create(
                id=uuid.uuid4().hex, tenant_id=tenant_id,
                name=data["name"], access_type=data["access_type"],
                config_json=data.get("config_json", {}),
            )
            await session.commit()
            return obj.to_dict()

    async def update_access_method(self, method_id: str, tenant_id: str, data: dict) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = DataAccessMethodRepository(session)
            obj = await repo.update(method_id, tenant_id, **{
                k: v for k, v in data.items()
                if k in ("name", "config_json", "status") and v is not None
            })
            if obj is None:
                obj = await repo.get_required(method_id, tenant_id)
            await session.commit()
            return obj.to_dict()


    async def list_parsers(self, tenant_id: str, offset: int = 0, limit: int = 20) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = ParserConfigRepository(session)
            items = await repo.list_all(tenant_id, offset, limit)
            total = await repo.count(tenant_id)
            return {"items": [o.to_dict() for o in items], "total": total, "offset": offset, "limit": limit}

    async def create_parser(self, tenant_id: str, data: dict) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = ParserConfigRepository(session)
            obj = await repo.create(
                id=uuid.uuid4().hex, tenant_id=tenant_id,
                name=data["name"], parser_type=data["parser_type"],
                file_types=data.get("file_types", []),
                config_json=data.get("config_json", {}),
            )
            await session.commit()
            return obj.to_dict()

    async def update_parser(self, parser_id: str, tenant_id: str, data: dict) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = ParserConfigRepository(session)
            obj = await repo.update(parser_id, tenant_id, **{
                k: v for k, v in data.items()
                if k in ("name", "file_types", "config_json", "status") and v is not None
            })
            if obj is None:
                obj = await repo.get_required(parser_id, tenant_id)
            await session.commit()
            return obj.to_dict()


    async def list_providers(self, tenant_id: str, offset: int = 0, limit: int = 20) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = ModelProviderRepository(session)
            items = await repo.list_all(tenant_id, offset, limit)
            total = await repo.count(tenant_id)
            return {"items": [o.to_dict() for o in items], "total": total, "offset": offset, "limit": limit}

    async def create_provider(self, tenant_id: str, data: dict) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = ModelProviderRepository(session)
            obj = await repo.create(
                id=uuid.uuid4().hex, tenant_id=tenant_id,
                name=data["name"], provider_type=data["provider_type"],
                model_type=data.get("model_type"), endpoint=data.get("endpoint"),
                api_key_encrypted=data.get("api_key"), model_name=data.get("model_name"),
                config_json=data.get("config_json", {}),
            )
            await session.commit()
            return obj.to_dict()

    async def update_provider(self, provider_id: str, tenant_id: str, data: dict) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = ModelProviderRepository(session)
            updatable = {"name", "endpoint", "api_key_encrypted", "model_name", "config_json", "status"}
            obj = await repo.update(provider_id, tenant_id, **{
                k: v for k, v in data.items() if k in updatable and v is not None
            })
            if obj is None:
                obj = await repo.get_required(provider_id, tenant_id)
            await session.commit()
            return obj.to_dict()

    async def test_provider(self, provider_id: str, tenant_id: str) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = ModelProviderRepository(session)
            await repo.get_required(provider_id, tenant_id)
        return {"success": True, "message": "连接测试通过（mock）"}
