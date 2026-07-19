#!/usr/bin/python3



import json
import logging
import os
from typing import Optional

from neo4j import AsyncDriver

from jonex_core.common.ontology_embedding import build_embed_text, embed, embed_hash
from jonex_core.common.tenant import require_tenant

logger = logging.getLogger(__name__)


class OntologyGraphRepository:


    def __init__(self, driver: AsyncDriver):
        self._driver = driver


        self._endpoint_cache: dict[tuple, tuple[str, str]] = {}

    def reset_endpoint_cache(self) -> None:

        self._endpoint_cache.clear()

    async def merge_entity(self, tenant_id: str, kb_id: str, doc_id: str, entity: dict,
                          hash_cache: dict | None = None) -> None:
        tenant_id = require_tenant(tenant_id)


        embedding = None
        embedding_hash_val = None
        if os.getenv("ONTOLOGY_VECTOR_ENABLED", "true").lower() in ("1", "true", "yes", "on"):
            text = build_embed_text(
                entity["canonical_name"], entity.get("aliases", []), entity.get("description", ""),
            )
            new_hash = embed_hash(text)
            key = (entity["entity_type"], entity["canonical_name"])
            if hash_cache is not None:
                existing_hash = hash_cache.get(key)
            else:
                existing_hash = await self._get_embedding_hash(tenant_id, kb_id, *key)
            if text and existing_hash != new_hash:


                vec = await embed(
                    text, tenant_id=tenant_id, kb_id=kb_id, doc_id=doc_id,
                    trace_id=f"ontology_ingest:{doc_id}" if doc_id else None,
                )
                if vec is not None:
                    embedding = vec
                    embedding_hash_val = new_hash

        cypher = """
        MERGE (e:OntologyEntity {
            tenant_id:$tenant_id, kb_id:$kb_id,
            entity_type:$entity_type, canonical_name:$canonical_name
        })
        ON CREATE SET
            e.aliases=$aliases, e.aliases_text=$aliases_text,
            e.attributes=$attributes, e.confidence=$confidence,
            e.description=$description,
            e.doc_ids=[$doc_id], e.source_chunks=$source_chunks,
            e.lightrag_doc_ids=$lightrag_doc_ids, e.extraction_method=$extraction_method,
            e.embedding=$embedding, e.embedding_hash=$embedding_hash,
            e.stub=false, e.created_at=timestamp(), e.updated_at=timestamp()
        ON MATCH SET
            e.aliases=$aliases, e.aliases_text=$aliases_text, e.attributes=$attributes,
            e.description=CASE WHEN size($description) > size(coalesce(e.description,''))
                THEN $description ELSE e.description END,
            e.confidence=CASE WHEN $confidence>coalesce(e.confidence,0) THEN $confidence ELSE e.confidence END,
            e.doc_ids=apoc.coll.toSet(coalesce(e.doc_ids,[])+[$doc_id]),
            e.source_chunks=$source_chunks,
            e.lightrag_doc_ids=apoc.coll.toSet(coalesce(e.lightrag_doc_ids,[])+$lightrag_doc_ids),
            e.embedding=CASE WHEN $embedding IS NOT NULL THEN $embedding ELSE e.embedding END,
            e.embedding_hash=CASE WHEN $embedding IS NOT NULL THEN $embedding_hash ELSE e.embedding_hash END,
            e.stub=false, e.updated_at=timestamp()
        """
        params = {
            "tenant_id": tenant_id,
            "kb_id": kb_id,
            "doc_id": doc_id,
            "canonical_name": entity["canonical_name"],
            "entity_type": entity["entity_type"],
            "aliases": entity.get("aliases", []),
            "aliases_text": " ".join(entity.get("aliases", [])),
            "attributes": json.dumps(entity.get("attributes", {}), ensure_ascii=False),
            "description": entity.get("description", ""),
            "confidence": entity.get("confidence", 1.0),
            "source_chunks": json.dumps(entity.get("source_chunks", []), ensure_ascii=False),
            "lightrag_doc_ids": entity.get("lightrag_doc_ids", []),
            "extraction_method": entity.get("extraction_method", "llm_guided"),
            "embedding": embedding,
            "embedding_hash": embedding_hash_val,
        }
        async with self._driver.session() as session:
            await session.run(cypher, params)

    async def merge_relation(self, tenant_id: str, kb_id: str, doc_id: str, rel: dict) -> None:
        tenant_id = require_tenant(tenant_id)
        use_endpoint_resolve = os.getenv("ONTOLOGY_REL_ENDPOINT_RESOLVE", "true").lower() in ("1", "true", "yes", "on")
        if use_endpoint_resolve:
            src_type, src_name = await self._resolve_endpoint(
                tenant_id, kb_id, rel["source_name"], rel.get("source_type"))
            tgt_type, tgt_name = await self._resolve_endpoint(
                tenant_id, kb_id, rel["target_name"], rel.get("target_type"))
        else:
            src_type = await self._resolve_entity_type(
                tenant_id, kb_id, rel["source_name"], rel.get("source_type"))
            tgt_type = await self._resolve_entity_type(
                tenant_id, kb_id, rel["target_name"], rel.get("target_type"))
            src_name = rel["source_name"]
            tgt_name = rel["target_name"]
        cypher = """
        MERGE (s:OntologyEntity {tenant_id:$t, kb_id:$k, entity_type:$src_type, canonical_name:$src_name})
        ON CREATE SET s.stub=true, s.confidence=0.1, s.aliases=[], s.aliases_text='',
            s.attributes='{}', s.source_chunks=[], s.lightrag_doc_ids=[],
            s.extraction_method='stub', s.doc_ids=[$doc_id], s.created_at=timestamp(), s.updated_at=timestamp()
        MERGE (o:OntologyEntity {tenant_id:$t, kb_id:$k, entity_type:$tgt_type, canonical_name:$tgt_name})
        ON CREATE SET o.stub=true, o.confidence=0.1, o.aliases=[], o.aliases_text='',
            o.attributes='{}', o.source_chunks=[], o.lightrag_doc_ids=[],
            o.extraction_method='stub', o.doc_ids=[$doc_id], o.created_at=timestamp(), o.updated_at=timestamp()
        MERGE (s)-[r:ONT_REL {relation_type:$rel_type}]->(o)
        ON CREATE SET r.confidence=$confidence, r.attributes=$attributes,
            r.lightrag_doc_ids=$lightrag_doc_ids, r.doc_ids=[$doc_id],
            r.created_at=timestamp(), r.updated_at=timestamp()
        ON MATCH SET r.doc_ids=apoc.coll.toSet(coalesce(r.doc_ids,[])+[$doc_id]),
            r.lightrag_doc_ids=apoc.coll.toSet(coalesce(r.lightrag_doc_ids,[])+$lightrag_doc_ids),
            r.attributes=$attributes,
            r.confidence=CASE WHEN $confidence>coalesce(r.confidence,0) THEN $confidence ELSE r.confidence END,
            r.updated_at=timestamp()
        """
        params = {
            "t": tenant_id,
            "k": kb_id,
            "doc_id": doc_id,
            "src_type": src_type,
            "src_name": src_name,
            "tgt_type": tgt_type,
            "tgt_name": tgt_name,
            "rel_type": rel["relation_type"],
            "confidence": rel.get("confidence", 1.0),
            "attributes": json.dumps(rel.get("attributes", {}), ensure_ascii=False),
            "lightrag_doc_ids": rel.get("lightrag_doc_ids", []),
        }
        async with self._driver.session() as session:
            await session.run(cypher, params)

    async def _resolve_entity_type(
        self,
        tenant_id: str,
        kb_id: str,
        name: str,
        type_hint: Optional[str],
    ) -> str:
        tenant_id = require_tenant(tenant_id)
        if type_hint:
            return type_hint
        cypher = """
        MATCH (e:OntologyEntity {tenant_id:$t, kb_id:$k, canonical_name:$name})
        RETURN e.entity_type AS entity_type
        ORDER BY coalesce(e.stub,false) ASC
        LIMIT 1
        """
        async with self._driver.session() as session:
            result = await session.run(cypher, {"t": tenant_id, "k": kb_id, "name": name})
            record = await result.single()
            return record["entity_type"] if record else "Unknown"

    async def _resolve_endpoint(
        self,
        tenant_id: str,
        kb_id: str,
        name: str,
        type_hint: Optional[str],
    ) -> tuple[str, str]:

        tenant_id = require_tenant(tenant_id)
        hint = type_hint or None
        cache_key = (kb_id, name, hint or "")
        if cache_key in self._endpoint_cache:
            return self._endpoint_cache[cache_key]
        cypher = """
        MATCH (e:OntologyEntity {tenant_id:$t, kb_id:$k})
        WHERE coalesce(e.stub,false)=false
          AND (e.canonical_name=$name OR $name IN coalesce(e.aliases,[]))
          AND ($hint IS NULL OR e.canonical_name=$name OR e.entity_type=$hint)
        RETURN e.entity_type AS et, e.canonical_name AS cn
        ORDER BY (CASE WHEN e.canonical_name=$name THEN 0 ELSE 1 END),
                 (CASE WHEN $hint IS NOT NULL AND e.entity_type=$hint THEN 0 ELSE 1 END),
                 coalesce(e.confidence,0) DESC
        LIMIT 1
        """
        async with self._driver.session() as session:
            result = await session.run(cypher, {"t": tenant_id, "k": kb_id, "name": name, "hint": hint})
            record = await result.single()
            if record:
                resolved = (record["et"], record["cn"])
            else:
                resolved = (type_hint or "Unknown"), name
        self._endpoint_cache[cache_key] = resolved
        return resolved

    async def delete_by_document(self, tenant_id: str, doc_id: str) -> None:

        tenant_id = require_tenant(tenant_id)
        async with self._driver.session() as session:

            await session.run(
                """
                MATCH (:OntologyEntity {tenant_id:$t})-[r:ONT_REL]->(:OntologyEntity {tenant_id:$t})
                WHERE $doc_id IN r.doc_ids
                SET r.doc_ids = [x IN r.doc_ids WHERE x <> $doc_id]
                """,
                {"t": tenant_id, "doc_id": doc_id},
            )

            await session.run(
                """
                MATCH (:OntologyEntity {tenant_id:$t})-[r:ONT_REL]->(:OntologyEntity {tenant_id:$t})
                WHERE size(coalesce(r.doc_ids,[]))=0
                DELETE r
                """,
                {"t": tenant_id},
            )

            await session.run(
                """
                MATCH (e:OntologyEntity {tenant_id:$t})
                WHERE $doc_id IN e.doc_ids
                SET e.doc_ids = [x IN e.doc_ids WHERE x <> $doc_id]
                """,
                {"t": tenant_id, "doc_id": doc_id},
            )

            await session.run(
                """
                MATCH (e:OntologyEntity {tenant_id:$t})
                WHERE size(coalesce(e.doc_ids,[]))=0 AND NOT (e)--()
                DELETE e
                """,
                {"t": tenant_id},
            )

    async def search_entities(self, tenant_id: str, kb_ids: list[str], query: str, limit: int = 5) -> list[dict]:
        tenant_id = require_tenant(tenant_id)
        cypher = """
        CALL db.index.fulltext.queryNodes('ont_entity_ft', $q) YIELD node, score
        WHERE node.tenant_id=$t AND node.kb_id IN $kbs AND coalesce(node.stub,false)=false
        RETURN node.canonical_name AS name, node.entity_type AS type,
               node.aliases AS aliases, node.attributes AS attributes,
               node.description AS description,
               node.confidence AS confidence, node.kb_id AS kb_id,
               node.doc_ids AS doc_ids, score
        ORDER BY score DESC LIMIT $limit
        """
        async with self._driver.session() as session:
            result = await session.run(cypher, {"t": tenant_id, "kbs": kb_ids, "q": query, "limit": limit})
            rows = [dict(record) async for record in result]
        for row in rows:
            if isinstance(row.get("attributes"), str):
                try:
                    row["attributes"] = json.loads(row["attributes"])
                except (json.JSONDecodeError, TypeError):
                    row["attributes"] = {}
        return rows

    async def neighbors(self, tenant_id: str, kb_id: str, entity_name: str, limit: int = 20) -> dict:
        tenant_id = require_tenant(tenant_id)
        cypher = """
        MATCH (e:OntologyEntity {tenant_id:$t, kb_id:$k, canonical_name:$name})
        MATCH (e)-[r:ONT_REL]-(n:OntologyEntity {tenant_id:$t, kb_id:$k})
        WITH e, r, n, CASE WHEN startNode(r) = e THEN 'outgoing' ELSE 'incoming' END AS rel_dir
        RETURN e.canonical_name AS source,
               collect({source:e.canonical_name, relation_type:r.relation_type,
                        direction:rel_dir, target:n.canonical_name,
                        target_type:n.entity_type})[..$limit] AS facts
        """
        async with self._driver.session() as session:
            result = await session.run(cypher, {"t": tenant_id, "k": kb_id, "name": entity_name, "limit": limit})
            record = await result.single()
            return dict(record) if record else {"source": entity_name, "facts": []}

    async def exact_match_entities(self, tenant_id: str, kb_ids: list[str], name: str) -> list[dict]:

        tenant_id = require_tenant(tenant_id)
        cypher = """
        MATCH (e:OntologyEntity {tenant_id:$t})
        WHERE e.kb_id IN $kbs AND coalesce(e.stub,false)=false
          AND (e.canonical_name=$name OR $name IN coalesce(e.aliases,[]))
        RETURN e.canonical_name AS name, e.entity_type AS type,
               e.aliases AS aliases, e.attributes AS attributes,
               e.description AS description, e.confidence AS confidence,
               e.kb_id AS kb_id, e.doc_ids AS doc_ids, 1.0 AS score
        """
        async with self._driver.session() as session:
            result = await session.run(cypher, {"t": tenant_id, "kbs": kb_ids, "name": name})
            rows = [dict(record) async for record in result]
        for row in rows:
            if isinstance(row.get("attributes"), str):
                try:
                    row["attributes"] = json.loads(row["attributes"])
                except (json.JSONDecodeError, TypeError):
                    row["attributes"] = {}
        return rows

    async def prefix_match_entities(self, tenant_id: str, kb_ids: list[str], prefix: str, limit: int = 5) -> list[dict]:

        tenant_id = require_tenant(tenant_id)
        cypher = """
        MATCH (e:OntologyEntity {tenant_id:$t})
        WHERE e.kb_id IN $kbs AND e.canonical_name STARTS WITH $prefix AND coalesce(e.stub,false)=false
        RETURN e.canonical_name AS name, e.entity_type AS type,
               e.aliases AS aliases, e.attributes AS attributes,
               e.description AS description, e.confidence AS confidence,
               e.kb_id AS kb_id, e.doc_ids AS doc_ids, 1.0 AS score
        ORDER BY size(e.canonical_name) ASC
        LIMIT $limit
        """
        async with self._driver.session() as session:
            result = await session.run(cypher, {"t": tenant_id, "kbs": kb_ids, "prefix": prefix, "limit": limit})
            rows = [dict(record) async for record in result]
        for row in rows:
            if isinstance(row.get("attributes"), str):
                try:
                    row["attributes"] = json.loads(row["attributes"])
                except (json.JSONDecodeError, TypeError):
                    row["attributes"] = {}
        return rows


    async def count_entities(self, tenant_id: str, kb_id: str) -> int:

        tenant_id = require_tenant(tenant_id)
        cypher = """
        MATCH (e:OntologyEntity {tenant_id:$t, kb_id:$k})
        WHERE coalesce(e.stub,false)=false
        RETURN count(e) AS c
        """
        async with self._driver.session() as session:
            result = await session.run(cypher, {"t": tenant_id, "k": kb_id})
            record = await result.single()
            return record["c"] if record else 0

    async def count_relations(self, tenant_id: str, kb_id: str) -> int:

        tenant_id = require_tenant(tenant_id)
        cypher = """
        MATCH (s:OntologyEntity {tenant_id:$t, kb_id:$k})-[r:ONT_REL]->(o:OntologyEntity {tenant_id:$t, kb_id:$k})
        WHERE coalesce(s.stub,false)=false AND coalesce(o.stub,false)=false
        RETURN count(r) AS c
        """
        async with self._driver.session() as session:
            result = await session.run(cypher, {"t": tenant_id, "k": kb_id})
            record = await result.single()
            return record["c"] if record else 0

    async def count_entities_by_type(self, tenant_id: str, kb_id: str) -> dict[str, int]:

        tenant_id = require_tenant(tenant_id)
        cypher = """
        MATCH (e:OntologyEntity {tenant_id:$t, kb_id:$k})
        WHERE coalesce(e.stub,false)=false
        RETURN e.entity_type AS type, count(e) AS c
        """
        async with self._driver.session() as session:
            result = await session.run(cypher, {"t": tenant_id, "k": kb_id})
            return {rec["type"]: rec["c"] async for rec in result}

    async def count_relations_by_type(self, tenant_id: str, kb_id: str) -> dict[str, int]:

        tenant_id = require_tenant(tenant_id)
        cypher = """
        MATCH (s:OntologyEntity {tenant_id:$t, kb_id:$k})-[r:ONT_REL]->(o:OntologyEntity {tenant_id:$t, kb_id:$k})
        WHERE coalesce(s.stub,false)=false AND coalesce(o.stub,false)=false
        RETURN r.relation_type AS type, count(r) AS c
        """
        async with self._driver.session() as session:
            result = await session.run(cypher, {"t": tenant_id, "k": kb_id})
            return {rec["type"]: rec["c"] async for rec in result}

    async def list_entities(
        self,
        tenant_id: str,
        kb_id: str,
        offset: int = 0,
        limit: int = 20,
        entity_type: Optional[str] = None,
        keyword: Optional[str] = None,
        include_unknown: bool = True,
    ) -> tuple[list[dict], int]:

        tenant_id = require_tenant(tenant_id)
        where = ["coalesce(e.stub,false)=false"]
        params = {"t": tenant_id, "k": kb_id, "offset": offset, "limit": limit}
        if entity_type:
            where.append("e.entity_type=$etype")
            params["etype"] = entity_type
        elif not include_unknown:

            where.append("e.entity_type <> 'unknown'")
        if keyword:
            where.append(
                "(toLower(e.canonical_name) CONTAINS toLower($kw) "
                "OR toLower(e.aliases_text) CONTAINS toLower($kw))"
            )
            params["kw"] = keyword
        where_clause = " AND ".join(where)

        count_cypher = f"""
        MATCH (e:OntologyEntity {{tenant_id:$t, kb_id:$k}})
        WHERE {where_clause}
        RETURN count(e) AS c
        """
        page_cypher = f"""
        MATCH (e:OntologyEntity {{tenant_id:$t, kb_id:$k}})
        WHERE {where_clause}
        RETURN e.canonical_name AS name, e.entity_type AS type,
               e.aliases AS aliases, e.attributes AS attributes,
               e.description AS description, e.confidence AS confidence,
               e.doc_ids AS doc_ids
        ORDER BY e.updated_at DESC, elementId(e)
        SKIP $offset LIMIT $limit
        """
        async with self._driver.session() as session:
            total_rec = await (await session.run(count_cypher, params)).single()
            total = total_rec["c"] if total_rec else 0
            result = await session.run(page_cypher, params)
            rows = [dict(rec) async for rec in result]
        for row in rows:
            if isinstance(row.get("attributes"), str):
                try:
                    row["attributes"] = json.loads(row["attributes"])
                except (json.JSONDecodeError, TypeError):
                    row["attributes"] = {}
        return rows, total

    async def list_relations(
        self,
        tenant_id: str,
        kb_id: str,
        offset: int = 0,
        limit: int = 20,
        relation_type: Optional[str] = None,
        source_name: Optional[str] = None,
        target_name: Optional[str] = None,
        source_type: Optional[str] = None,
        target_type: Optional[str] = None,
    ) -> tuple[list[dict], int]:

        tenant_id = require_tenant(tenant_id)
        where = ["coalesce(s.stub,false)=false", "coalesce(o.stub,false)=false"]
        params = {"t": tenant_id, "k": kb_id, "offset": offset, "limit": limit}
        if relation_type:
            where.append("r.relation_type=$rtype")
            params["rtype"] = relation_type
        if source_name:
            where.append("s.canonical_name=$sname")
            params["sname"] = source_name
        if target_name:
            where.append("o.canonical_name=$tname")
            params["tname"] = target_name
        if source_type:
            where.append("s.entity_type=$stype")
            params["stype"] = source_type
        if target_type:
            where.append("o.entity_type=$ttype")
            params["ttype"] = target_type
        where_clause = ("WHERE " + " AND ".join(where)) if where else ""

        match_clause = (
            "MATCH (s:OntologyEntity {tenant_id:$t, kb_id:$k})"
            "-[r:ONT_REL]->"
            "(o:OntologyEntity {tenant_id:$t, kb_id:$k})"
        )
        count_cypher = f"{match_clause} {where_clause} RETURN count(r) AS c"
        page_cypher = f"""
        {match_clause}
        {where_clause}
        RETURN s.canonical_name AS source, s.entity_type AS source_type,
               r.relation_type AS relation_type, r.confidence AS confidence,
               r.attributes AS attributes,
               o.canonical_name AS target, o.entity_type AS target_type
        ORDER BY r.created_at DESC, elementId(r)
        SKIP $offset LIMIT $limit
        """
        async with self._driver.session() as session:
            total_rec = await (await session.run(count_cypher, params)).single()
            total = total_rec["c"] if total_rec else 0
            result = await session.run(page_cypher, params)
            rows = [dict(rec) async for rec in result]
        for row in rows:
            if isinstance(row.get("attributes"), str):
                try:
                    row["attributes"] = json.loads(row["attributes"])
                except (json.JSONDecodeError, TypeError):
                    row["attributes"] = {}
        return rows, total


    @staticmethod
    def _deserialize_attrs(rows: list[dict]) -> None:

        for row in rows:
            if isinstance(row.get("attributes"), str):
                try:
                    row["attributes"] = json.loads(row["attributes"])
                except (json.JSONDecodeError, TypeError):
                    row["attributes"] = {}

    async def get_kb_graph(
        self,
        tenant_id: str,
        kb_id: str,
        limit: int = 500,
        entity_types: Optional[list[str]] = None,
    ) -> dict:

        tenant_id = require_tenant(tenant_id)

        type_filter = ""
        params: dict = {"t": tenant_id, "k": kb_id, "limit": limit}
        if entity_types:
            type_filter = "AND e.entity_type IN $types"
            params["types"] = entity_types


        type_counts = await self.count_entities_by_type(tenant_id, kb_id)
        if entity_types:
            total_nodes = sum(type_counts.get(t, 0) for t in entity_types)
        else:
            total_nodes = sum(type_counts.values())


        node_cypher = f"""
        MATCH (e:OntologyEntity {{tenant_id:$t, kb_id:$k}})
        WHERE coalesce(e.stub,false)=false {type_filter}
        OPTIONAL MATCH (e)-[r:ONT_REL]-(:OntologyEntity {{tenant_id:$t, kb_id:$k}})
        WITH e, count(r) AS degree
        RETURN e.entity_type + ':' + e.canonical_name AS id,
               e.canonical_name AS name,
               e.entity_type AS type,
               e.aliases AS aliases,
               e.attributes AS attributes,
               e.description AS description,
               e.confidence AS confidence,
               e.doc_ids AS doc_ids,
               degree
        ORDER BY degree DESC, e.updated_at DESC
        LIMIT $limit
        """
        async with self._driver.session() as session:
            result = await session.run(node_cypher, params)
            nodes = [dict(rec) async for rec in result]

        node_ids = [n["id"] for n in nodes]


        rel_where = "coalesce(s.stub,false)=false AND coalesce(o.stub,false)=false"
        rel_params: dict = {"t": tenant_id, "k": kb_id}
        if entity_types:
            rel_where += " AND s.entity_type IN $types AND o.entity_type IN $types"
            rel_params["types"] = entity_types
        count_rel_cypher = f"""
        MATCH (s:OntologyEntity {{tenant_id:$t, kb_id:$k}})-[r:ONT_REL]->(o:OntologyEntity {{tenant_id:$t, kb_id:$k}})
        WHERE {rel_where}
        RETURN count(r) AS c
        """
        async with self._driver.session() as session:
            rec = await (await session.run(count_rel_cypher, rel_params)).single()
            total_relations = rec["c"] if rec else 0


        edges: list[dict] = []
        if node_ids:
            edge_cypher = """
            MATCH (s:OntologyEntity {tenant_id:$t, kb_id:$k})
                  -[r:ONT_REL]->
                  (o:OntologyEntity {tenant_id:$t, kb_id:$k})
            WHERE coalesce(s.stub,false)=false AND coalesce(o.stub,false)=false
              AND (s.entity_type + ':' + s.canonical_name) IN $ids
              AND (o.entity_type + ':' + o.canonical_name) IN $ids
            RETURN s.canonical_name AS source,
                   s.entity_type AS source_type,
                   o.canonical_name AS target,
                   o.entity_type AS target_type,
                   r.relation_type AS label,
                   r.confidence AS confidence
            """
            async with self._driver.session() as session:
                result = await session.run(edge_cypher, {"t": tenant_id, "k": kb_id, "ids": node_ids})
                edges = [dict(rec) async for rec in result]

        self._deserialize_attrs(nodes)
        for n in nodes:
            n.pop("degree", None)

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": total_nodes,
            "total_relations": total_relations,
            "type_counts": type_counts,
            "returned_nodes": len(nodes),
            "returned_edges": len(edges),
            "truncated": total_nodes > len(nodes),
            "limit": limit,
        }

    async def expand_neighbors(
        self,
        tenant_id: str,
        kb_id: str,
        entity_type: str,
        canonical_name: str,
        limit: int = 50,
    ) -> dict:

        tenant_id = require_tenant(tenant_id)
        cypher = """
        MATCH (e:OntologyEntity {tenant_id:$t, kb_id:$k, entity_type:$etype, canonical_name:$name})
        MATCH (e)-[r:ONT_REL]-(n:OntologyEntity {tenant_id:$t, kb_id:$k})
        WHERE coalesce(n.stub,false)=false
        WITH e, r, n, startNode(r) AS sn, endNode(r) AS en
        RETURN n.entity_type + ':' + n.canonical_name AS id,
               n.canonical_name AS name,
               n.entity_type AS type,
               n.aliases AS aliases,
               n.attributes AS attributes,
               n.description AS description,
               n.confidence AS confidence,
               n.doc_ids AS doc_ids,
               sn.canonical_name AS source,
               sn.entity_type AS source_type,
               en.canonical_name AS target,
               en.entity_type AS target_type,
               r.relation_type AS label,
               r.confidence AS rel_confidence
        LIMIT $limit
        """
        params = {
            "t": tenant_id, "k": kb_id,
            "etype": entity_type, "name": canonical_name, "limit": limit,
        }
        async with self._driver.session() as session:
            result = await session.run(cypher, params)
            rows = [dict(rec) async for rec in result]

        nodes_by_id: dict[str, dict] = {}
        edges: list[dict] = []
        for row in rows:
            nid = row["id"]
            if nid not in nodes_by_id:
                nodes_by_id[nid] = {
                    "id": nid,
                    "name": row["name"],
                    "type": row["type"],
                    "aliases": row["aliases"],
                    "attributes": row["attributes"],
                    "description": row["description"],
                    "confidence": row["confidence"],
                    "doc_ids": row["doc_ids"],
                }
            edges.append({
                "source": row["source"],
                "source_type": row["source_type"],
                "target": row["target"],
                "target_type": row["target_type"],
                "label": row["label"],
                "confidence": row["rel_confidence"],
            })

        nodes = list(nodes_by_id.values())
        self._deserialize_attrs(nodes)
        return {"nodes": nodes, "edges": edges}


    async def _get_embedding_hash(self, tenant_id: str, kb_id: str, entity_type: str, canonical_name: str) -> Optional[str]:

        tenant_id = require_tenant(tenant_id)
        cypher = """
        MATCH (e:OntologyEntity {tenant_id:$t, kb_id:$k, entity_type:$et, canonical_name:$cn})
        RETURN e.embedding_hash AS h
        """
        async with self._driver.session() as session:
            result = await session.run(cypher, {"t": tenant_id, "k": kb_id, "et": entity_type, "cn": canonical_name})
            record = await result.single()
            return record["h"] if record and record["h"] else None

    async def get_embedding_hashes(self, tenant_id: str, kb_id: str) -> dict[tuple, str]:

        tenant_id = require_tenant(tenant_id)
        cypher = """
        MATCH (e:OntologyEntity {tenant_id:$t, kb_id:$k})
        WHERE coalesce(e.stub,false)=false AND e.embedding_hash IS NOT NULL
        RETURN e.entity_type AS et, e.canonical_name AS cn, e.embedding_hash AS h
        """
        async with self._driver.session() as session:
            result = await session.run(cypher, {"t": tenant_id, "k": kb_id})
            return {(r["et"], r["cn"]): r["h"] async for r in result}

    async def vector_search_entities(self, tenant_id: str, kb_ids: list[str], query_embedding: list[float],
                                     limit: int = 10) -> list[dict]:

        tenant_id = require_tenant(tenant_id)
        cypher = """
        CALL db.index.vector.queryNodes('ont_entity_embedding', $topk, $vec)
        YIELD node, score
        WHERE node.tenant_id=$t AND node.kb_id IN $kbs AND coalesce(node.stub,false)=false
        RETURN node.canonical_name AS name, node.entity_type AS type,
               node.aliases AS aliases, node.attributes AS attributes,
               node.description AS description, node.confidence AS confidence,
               node.kb_id AS kb_id, node.doc_ids AS doc_ids, score AS vscore
        ORDER BY score DESC LIMIT $limit
        """
        topk = int(os.getenv("ONTOLOGY_VECTOR_TOPK", "200"))
        topk = max(topk, limit * 20)
        async with self._driver.session() as session:
            result = await session.run(cypher, {
                "t": tenant_id, "kbs": kb_ids, "vec": query_embedding,
                "topk": topk, "limit": limit,
            })
            rows = [dict(r) async for r in result]
        self._deserialize_attrs(rows)
        return rows

__all__ = ["OntologyGraphRepository"]
