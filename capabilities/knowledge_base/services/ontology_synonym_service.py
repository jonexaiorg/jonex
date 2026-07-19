#!/usr/bin/python3


import uuid

from jonex_core.common import get_db_session
from jonex_core.common.exceptions import InvalidParameterError, ResourceConflictError
from jonex_core.common.tenant import require_tenant

from ..dtos.ontology_synonym import (
    MAX_IMPORT_GROUPS,
    MAX_TERM_LENGTH,
    MAX_TERMS_PER_GROUP,
)
from ..repository.knowledge_info_repository import KnowledgeInfoRepository
from ..repository.ontology_synonym_repository import OntologySynonymRepository


def _to_halfwidth(text: str) -> str:

    out = []
    for ch in text:
        code = ord(ch)
        if code == 0x3000:
            code = 0x20
        elif 0xFF01 <= code <= 0xFF5E:
            code -= 0xFEE0
        out.append(chr(code))
    return "".join(out)


def _normalize_display(term: str) -> str:

    return _to_halfwidth((term or "").strip())


def _normalize_key(term: str) -> str:

    return _normalize_display(term).casefold()


def _normalize_group(terms: list) -> tuple[list[str], list[str]]:

    display_terms: list[str] = []
    keys: list[str] = []
    seen: set[str] = set()
    for raw in terms or []:
        disp = _normalize_display(str(raw))
        if not disp:
            continue
        if len(disp) > MAX_TERM_LENGTH:
            raise InvalidParameterError(message=f"Synonym exceeds the maximum length ({MAX_TERM_LENGTH}): {disp[:20]}...")
        key = disp.casefold()
        if key in seen:
            continue
        seen.add(key)
        display_terms.append(disp)
        keys.append(key)
    return display_terms, keys


def _resolve_canonical(canonical, display_terms: list[str], keys: list[str]) -> str:

    if canonical is None or not str(canonical).strip():
        return display_terms[0]
    c_key = _normalize_key(str(canonical))
    if c_key not in keys:
        raise InvalidParameterError(message="canonical must be included in terms")
    return display_terms[keys.index(c_key)]


class OntologySynonymService:


    async def _ensure_kb(self, session, kb_id: str, tenant_id: str) -> None:

        await KnowledgeInfoRepository(session).get_required(kb_id, tenant_id)

    async def list(self, tenant_id: str, kb_id: str, page: int = 1, page_size: int = 20) -> dict:
        tenant_id = require_tenant(tenant_id)
        page = max(1, int(page or 1))
        page_size = max(1, min(200, int(page_size or 20)))
        async with get_db_session() as session:
            await self._ensure_kb(session, kb_id, tenant_id)
            repo = OntologySynonymRepository(session)
            items, total = await repo.list_by_kb(
                tenant_id, kb_id, offset=(page - 1) * page_size, limit=page_size
            )
            return {
                "items": [o.to_dict() for o in items],
                "total": total,
                "page": page,
                "page_size": page_size,
            }

    async def create(self, tenant_id: str, data: dict) -> dict:
        tenant_id = require_tenant(tenant_id)
        kb_id = data["knowledge_base_id"]
        async with get_db_session() as session:
            await self._ensure_kb(session, kb_id, tenant_id)
            repo = OntologySynonymRepository(session)

            display_terms, keys = _normalize_group(data.get("terms") or [])
            if len(display_terms) < 2:
                raise InvalidParameterError(message="Each synonym group must contain at least 2 unique terms")
            if len(display_terms) > MAX_TERMS_PER_GROUP:
                raise InvalidParameterError(message=f"Synonym group exceeds the maximum size ({MAX_TERMS_PER_GROUP})")
            canonical = _resolve_canonical(data.get("canonical"), display_terms, keys)


            used = await self._used_term_keys(repo, tenant_id, kb_id)
            clash = [k for k in keys if k in used]
            if clash:
                raise ResourceConflictError(message=f"Term appears in multiple groups: {clash[0]}")

            obj = await repo.create(
                id=uuid.uuid4().hex,
                tenant_id=tenant_id,
                knowledge_base_id=kb_id,
                terms=display_terms,
                canonical=canonical,
            )
            await session.commit()
            return obj.to_dict()

    async def update(self, tenant_id: str, synonym_id: str, data: dict) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = OntologySynonymRepository(session)
            obj = await repo.get_required(synonym_id, tenant_id)

            new_terms = data.get("terms")
            if new_terms is not None:
                display_terms, keys = _normalize_group(new_terms)
                if len(display_terms) < 2:
                    raise InvalidParameterError(message="Each synonym group must contain at least 2 unique terms")
                if len(display_terms) > MAX_TERMS_PER_GROUP:
                    raise InvalidParameterError(message=f"Synonym group exceeds the maximum size ({MAX_TERMS_PER_GROUP})")
                used = await self._used_term_keys(
                    repo, tenant_id, obj.knowledge_base_id, exclude_id=obj.id
                )
                clash = [k for k in keys if k in used]
                if clash:
                    raise ResourceConflictError(message=f"Term appears in multiple groups: {clash[0]}")
                obj.terms = display_terms

                canonical_src = data.get("canonical", obj.canonical)
                obj.canonical = _resolve_canonical(canonical_src, display_terms, keys)
            elif "canonical" in data:
                display_terms, keys = _normalize_group(obj.terms or [])
                obj.canonical = _resolve_canonical(data.get("canonical"), display_terms, keys)

            await session.commit()
            return obj.to_dict()

    async def delete(self, tenant_id: str, synonym_id: str) -> bool:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = OntologySynonymRepository(session)
            obj = await repo.get_required(synonym_id, tenant_id)
            await repo.delete_soft(obj)
            await session.commit()
            return True

    async def batch_import(self, tenant_id: str, kb_id: str, groups: list) -> dict:

        tenant_id = require_tenant(tenant_id)
        groups = groups or []
        if len(groups) > MAX_IMPORT_GROUPS:
            raise InvalidParameterError(message=f"Import exceeds the maximum number of groups ({MAX_IMPORT_GROUPS})")

        async with get_db_session() as session:
            await self._ensure_kb(session, kb_id, tenant_id)
            repo = OntologySynonymRepository(session)

            existing = await repo.list_all_by_kb(tenant_id, kb_id)
            existing_signatures: set[frozenset] = set()
            existing_keys: set[str] = set()
            for g in existing:
                _, ekeys = _normalize_group(g.terms or [])
                existing_signatures.add(frozenset(ekeys))
                existing_keys.update(ekeys)

            skipped = 0
            failed: list[dict] = []
            to_create: list[tuple[list[str], list[str]]] = []
            batch_keys: set[str] = set()
            batch_signatures: set[frozenset] = set()

            for index, group in enumerate(groups):
                try:
                    display_terms, keys = _normalize_group(group)
                except InvalidParameterError as e:
                    failed.append({"index": index, "reason": e.message})
                    continue
                if len(display_terms) < 2:
                    failed.append({"index": index, "reason": "去重后少于 2 个词"})
                    continue
                if len(display_terms) > MAX_TERMS_PER_GROUP:
                    failed.append({"index": index, "reason": f"词数超过上限({MAX_TERMS_PER_GROUP})"})
                    continue

                signature = frozenset(keys)

                if signature in existing_signatures or signature in batch_signatures:
                    skipped += 1
                    continue

                clash = [k for k in keys if k in existing_keys or k in batch_keys]
                if clash:
                    failed.append({"index": index, "reason": f"跨组重复词: {clash[0]}"})
                    continue

                batch_signatures.add(signature)
                batch_keys.update(keys)
                to_create.append((display_terms, keys))


            if failed:
                return {"created": 0, "skipped": skipped, "failed": failed}

            for display_terms, keys in to_create:
                await repo.create(
                    id=uuid.uuid4().hex,
                    tenant_id=tenant_id,
                    knowledge_base_id=kb_id,
                    terms=display_terms,
                    canonical=display_terms[0],
                )
            if to_create:
                await session.commit()

            return {"created": len(to_create), "skipped": skipped, "failed": []}

    async def _used_term_keys(
        self, repo: OntologySynonymRepository, tenant_id: str, kb_id: str, exclude_id: str = None
    ) -> set:
        used: set[str] = set()
        for g in await repo.list_all_by_kb(tenant_id, kb_id):
            if exclude_id and g.id == exclude_id:
                continue
            _, keys = _normalize_group(g.terms or [])
            used.update(keys)
        return used


__all__ = ["OntologySynonymService"]
