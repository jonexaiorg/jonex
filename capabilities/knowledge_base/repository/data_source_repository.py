#!/usr/bin/python3



from jonex_core.common.repository import BaseRepository

from ..models.data_source import KnowledgeDataSource


class KnowledgeDataSourceRepository(BaseRepository[KnowledgeDataSource]):
    model = KnowledgeDataSource

    async def list_by_kb(
        self, tenant_id: str, knowledge_base_id: str, offset: int = 0, limit: int = 100,
    ) -> list[KnowledgeDataSource]:
        return await self.list_all(
            tenant_id=tenant_id, offset=offset, limit=limit,
            extra_conditions=[KnowledgeDataSource.knowledge_base_id == knowledge_base_id],
        )

    async def count_by_kb(self, tenant_id: str, knowledge_base_id: str) -> int:
        return await self.count(
            tenant_id,
            extra_conditions=[KnowledgeDataSource.knowledge_base_id == knowledge_base_id],
        )


__all__ = ["KnowledgeDataSourceRepository"]
