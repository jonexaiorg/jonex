#!/usr/bin/python3


import uuid
from typing import Any

from sqlalchemy import text

from jonex_core.common import get_db_session
from jonex_core.common.exceptions import InvalidParameterError
from jonex_core.common.tenant import require_tenant

from ..repository.parser_setting_repository import KnowledgeParserSettingRepository


FILE_TYPE_ORDER = ["pdf", "doc", "xlsx", "pptx", "image", "audio", "video", "txt", "md", "html", "cad"]


class ParserSettingService:


    async def list_settings(self, tenant_id: str, knowledge_base_id: str) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = KnowledgeParserSettingRepository(session)
            items = await repo.list_by_kb(tenant_id, knowledge_base_id)
            parser_map = await self._load_parser_map(session, tenant_id)
            enriched = [self._enrich(item.to_dict(), parser_map) for item in items]
            enriched.sort(key=lambda row: self._sort_index(row["file_type"]))
            return {"items": enriched, "total": len(enriched), "offset": 0, "limit": 100}

    async def create_setting(self, tenant_id: str, data: dict) -> dict:
        tenant_id = require_tenant(tenant_id)
        knowledge_base_id = self._required(data, "knowledge_base_id")
        file_type = self._normalize_file_type(self._required(data, "file_type"))

        async with get_db_session() as session:
            repo = KnowledgeParserSettingRepository(session)
            existing = await repo.get_by_kb_file_type(tenant_id, knowledge_base_id, file_type)
            if existing is not None:
                raise InvalidParameterError(message="该文件类型已存在，请使用编辑修改")

            obj = await repo.create(
                id=uuid.uuid4().hex,
                tenant_id=tenant_id,
                knowledge_base_id=knowledge_base_id,
                file_type=file_type,
                file_type_label=data.get("file_type_label") or data.get("type") or file_type.upper(),
                parser_config_id=data.get("parser_config_id"),
                preprocessing_json=self._list_value(data.get("preprocessing_json")),
                postprocessing_json=self._list_value(data.get("postprocessing_json")),
                prompt_text=data.get("prompt_text") or "",
                prompt_template_id=data.get("prompt_template_id"),
                prompt_template_version=data.get("prompt_template_version"),
                summary_prompt_text=data.get("summary_prompt_text") or "",
                summary_template_id=data.get("summary_template_id"),
                summary_template_version=data.get("summary_template_version"),
                tag_prompt_text=data.get("tag_prompt_text") or "",
                tag_template_id=data.get("tag_template_id"),
                tag_template_version=data.get("tag_template_version"),
                status=data.get("status") or "active",
            )
            await session.commit()
            parser_map = await self._load_parser_map(session, tenant_id)
            return self._enrich(obj.to_dict(), parser_map)

    async def update_setting(self, tenant_id: str, setting_id: str, data: dict) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = KnowledgeParserSettingRepository(session)
            obj = await repo.get_required(setting_id, tenant_id)

            next_file_type = data.get("file_type")
            if next_file_type is not None:
                next_file_type = self._normalize_file_type(next_file_type)
                duplicate = await repo.get_by_kb_file_type(tenant_id, obj.knowledge_base_id, next_file_type)
                if duplicate is not None and duplicate.id != obj.id:
                    raise InvalidParameterError(message="该文件类型已存在，请使用编辑修改")
                obj.file_type = next_file_type

            updatable = {
                "knowledge_base_id", "file_type_label", "parser_config_id", "prompt_text",
                "prompt_template_id", "prompt_template_version", "summary_prompt_text",
                "summary_template_id", "summary_template_version", "tag_prompt_text",
                "tag_template_id", "tag_template_version", "status",
            }
            for key in updatable:
                if key in data:
                    setattr(obj, key, data[key])
            if "preprocessing_json" in data:
                obj.preprocessing_json = self._list_value(data.get("preprocessing_json"))
            if "postprocessing_json" in data:
                obj.postprocessing_json = self._list_value(data.get("postprocessing_json"))

            await session.flush()
            await session.commit()
            parser_map = await self._load_parser_map(session, tenant_id)
            return self._enrich(obj.to_dict(), parser_map)

    async def delete_setting(self, tenant_id: str, setting_id: str) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = KnowledgeParserSettingRepository(session)
            deleted = await repo.delete_soft(setting_id, tenant_id)
            await session.commit()
        return {"deleted": deleted, "id": setting_id}

    async def _load_parser_map(self, session, tenant_id: str) -> dict[str, dict[str, Any]]:
        return {item["id"]: item for item in await self._load_parsers(session, tenant_id, active_only=False)}

    async def _load_parsers(self, session, tenant_id: str, *, active_only: bool) -> list[dict[str, Any]]:
        status_clause = "AND status = 'active'" if active_only else ""
        result = await session.execute(text(f), {"tenant_id": tenant_id})
        return [dict(row._mapping) for row in result]

    @staticmethod
    def _enrich(row: dict, parser_map: dict[str, dict[str, Any]]) -> dict:
        parser = parser_map.get(row.get("parser_config_id") or "")
        row["parser_name"] = parser.get("name") if parser else ""
        row["parser_type"] = parser.get("parser_type") if parser else ""
        row["parser_file_types"] = parser.get("file_types") if parser else []
        row["parser_status"] = parser.get("status") if parser else None
        return row

    @staticmethod
    def _sort_index(file_type: str) -> int:
        order = {item: idx for idx, item in enumerate(FILE_TYPE_ORDER)}
        return order.get(file_type, len(order))

    @staticmethod
    def _normalize_file_type(file_type: str) -> str:
        return str(file_type).strip().lower().replace(" ", "_").replace("/", "_")

    @staticmethod
    def _list_value(value: Any) -> list:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    @staticmethod
    def _required(data: dict, key: str) -> str:
        value = data.get(key)
        if not value:
            raise InvalidParameterError(message=f"缺少参数: {key}")
        return str(value)


__all__ = ["ParserSettingService"]
