#!/usr/bin/python3



import uuid

from jonex_core.common import get_db_session
from jonex_core.common.exceptions import ResourceConflictError, ResourceNotFoundError
from jonex_core.common.tenant import require_tenant

from ..repository.document_repository import KnowledgeDocumentRepository
from ..repository.folder_repository import FolderRepository
from ..repository.knowledge_info_repository import KnowledgeInfoRepository


class FolderService:


    async def _ensure_kb(self, session, kb_id: str, tenant_id: str) -> None:

        await KnowledgeInfoRepository(session).get_required(kb_id, tenant_id)

    async def list_folders(self, tenant_id: str, knowledge_base_id: str) -> dict:

        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            await self._ensure_kb(session, knowledge_base_id, tenant_id)
            repo = FolderRepository(session)
            items = await repo.list_by_kb(tenant_id, knowledge_base_id)
            return {
                "items": [f.to_dict() for f in items],
                "total": len(items),
            }

    async def create_folder(self, tenant_id: str, data: dict) -> dict:

        tenant_id = require_tenant(tenant_id)
        kb_id = data["knowledge_base_id"]
        name = data["name"]
        async with get_db_session() as session:
            await self._ensure_kb(session, kb_id, tenant_id)
            repo = FolderRepository(session)

            existing = await repo.get_by_name(tenant_id, kb_id, name)
            if existing:
                raise ResourceConflictError(message=f"文件夹名称已存在: {name}")

            obj = await repo.create(
                id=uuid.uuid4().hex,
                tenant_id=tenant_id,
                knowledge_base_id=kb_id,
                name=name,
                is_preset=0,
                sort_order=0,
            )
            await session.commit()
            return obj.to_dict()

    async def rename_folder(
        self, tenant_id: str, folder_id: str, knowledge_base_id: str, new_name: str
    ) -> dict:

        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = FolderRepository(session)


            obj = await repo.get_required(folder_id, tenant_id)
            if obj.knowledge_base_id != knowledge_base_id:
                raise ResourceNotFoundError(
                    message="文件夹不属于指定的知识库",
                    details={"folder_id": folder_id, "knowledge_base_id": knowledge_base_id},
                )


            existing = await repo.get_by_name(tenant_id, obj.knowledge_base_id, new_name)
            if existing and existing.id != folder_id:
                raise ResourceConflictError(message=f"文件夹名称已存在: {new_name}")

            obj.name = new_name
            await session.commit()
            return obj.to_dict()

    async def delete_folder(
        self, tenant_id: str, folder_id: str, knowledge_base_id: str
    ) -> bool:

        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = FolderRepository(session)
            doc_repo = KnowledgeDocumentRepository(session)

            obj = await repo.get_required(folder_id, tenant_id)
            if obj.knowledge_base_id != knowledge_base_id:
                raise ResourceNotFoundError(
                    message="文件夹不属于指定的知识库",
                    details={"folder_id": folder_id, "knowledge_base_id": knowledge_base_id},
                )


            docs = await doc_repo.list_by_folder(tenant_id, folder_id)
            for doc in docs:
                doc.folder_id = None

            await repo.delete_soft(obj)
            await session.commit()
            return True


__all__ = ["FolderService"]
