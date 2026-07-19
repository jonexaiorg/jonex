#!/usr/bin/python3



from sqlalchemy import select

from jonex_core.common.repository import BaseRepository

from ..models.parser_setting import KnowledgeParserSetting


class KnowledgeParserSettingRepository(BaseRepository[KnowledgeParserSetting]):
    model = KnowledgeParserSetting

    async def list_by_kb(
        self, tenant_id: str, knowledge_base_id: str, offset: int = 0, limit: int = 100,
    ) -> list[KnowledgeParserSetting]:
        return await self.list_all(
            tenant_id=tenant_id, offset=offset, limit=limit,
            extra_conditions=[KnowledgeParserSetting.knowledge_base_id == knowledge_base_id],
        )

    async def get_by_kb_file_type(
        self, tenant_id: str, knowledge_base_id: str, file_type: str,
    ) -> KnowledgeParserSetting | None:
        result = await self.session.execute(
            select(KnowledgeParserSetting).where(
                KnowledgeParserSetting.tenant_id == tenant_id,
                KnowledgeParserSetting.knowledge_base_id == knowledge_base_id,
                KnowledgeParserSetting.file_type == file_type,
                KnowledgeParserSetting.is_deleted == 0,
            )
        )
        return result.scalar_one_or_none()


__all__ = ["KnowledgeParserSettingRepository"]
