"""
Neo4j ontology graph DAO (replaces PG version OntologyDAO)

All write operations enforce tenant_id + kb_id, and use Cypher MERGE to achieve cross-document auto connectivity.
"""

import json
import logging
from typing import Any, Optional

from neo4j import AsyncDriver

logger = logging.getLogger(__name__)


class OntologyGraphDAO:
    """Ontology graph data access object — Neo4j implementation"""

    def __init__(self, driver: AsyncDriver):
        self._driver = driver

    async def merge_entity(
        self, tenant_id: str, kb_id: str, doc_id: str, entity: dict
    ) -> None:
        """MERGE entity by composite unique key; if exists, merge attributes, clear stub flag.

        Atomic operations:
        - doc_ids / source_chunks / lightrag_doc_ids deduplicated via apoc.coll.toSet
        - attributes shallow merged via apoc.map.merge
        """
        cypher = """
        MERGE (e:OntologyEntity {
            tenant_id:$tenant_id, kb_id:$kb_id,
            entity_type:$entity_type, canonical_name:$canonical_name
        })
        ON CREATE SET
            e.aliases=$aliases, e.aliases_text=$aliases_text,
            e.attributes=$attributes, e.confidence=$confidence,
            e.doc_ids=[$doc_id],
            e.source_chunks=$source_chunks,
            e.lightrag_doc_ids=$lightrag_doc_ids,
            e.extraction_method=$extraction_method,
            e.stub=false,
            e.created_at=timestamp(), e.updated_at=timestamp()
        ON MATCH SET
            e.aliases=$aliases, e.aliases_text=$aliases_text,
            e.attributes=$attributes,
            e.confidence=CASE
                WHEN $confidence>coalesce(e.confidence,0) THEN $confidence
                ELSE e.confidence
            END,
            e.doc_ids=apoc.coll.toSet(coalesce(e.doc_ids,[])+[$doc_id]),
            e.source_chunks=apoc.coll.toSet(coalesce(e.source_chunks,[])+$source_chunks),
            e.lightrag_doc_ids=apoc.coll.toSet(coalesce(e.lightrag_doc_ids,[])+$lightrag_doc_ids),
            e.stub=false,
            e.updated_at=timestamp()
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
            "confidence": entity.get("confidence", 1.0),
            "source_chunks": entity.get("source_chunks", []),
            "lightrag_doc_ids": entity.get("lightrag_doc_ids", []),
            "extraction_method": entity.get("extraction_method", "llm_guided"),
        }
        async with self._driver.session() as session:
            await session.run(cypher, params)

    async def merge_relation(
        self, tenant_id: str, kb_id: str, doc_id: str, rel: dict
    ) -> None:
        """MERGE relation; if endpoint type missing, query DB for fallback, still missing then create stub.

        Two-step fallback:
          1. When source/target type is empty, query existing entity to get type
          2. If not found, use 'Unknown' (create stub node)
        """
        src_type = await self._resolve_entity_type(
            tenant_id, kb_id, rel["source_name"], rel.get("source_type")
        )
        tgt_type = await self._resolve_entity_type(
            tenant_id, kb_id, rel["target_name"], rel.get("target_type")
        )

        cypher = """
        MERGE (s:OntologyEntity {
            tenant_id:$t, kb_id:$k,
            entity_type:$src_type, canonical_name:$src_name
        })
        ON CREATE SET
            s.stub=true, s.confidence=0.1,
            s.aliases=[], s.aliases_text='',
            s.attributes='{}', s.source_chunks=[], s.lightrag_doc_ids=[],
            s.extraction_method='stub', s.doc_ids=[$doc_id],
            s.created_at=timestamp(), s.updated_at=timestamp()
        ON MATCH SET
            s.source_chunks=apoc.coll.toSet(coalesce(s.source_chunks,[])+$source_chunks),
            s.updated_at=timestamp()

        MERGE (o:OntologyEntity {
            tenant_id:$t, kb_id:$k,
            entity_type:$tgt_type, canonical_name:$tgt_name
        })
        ON CREATE SET
            o.stub=true, o.confidence=0.1,
            o.aliases=[], o.aliases_text='',
            o.attributes='{}', o.source_chunks=[], o.lightrag_doc_ids=[],
            o.extraction_method='stub', o.doc_ids=[$doc_id],
            o.created_at=timestamp(), o.updated_at=timestamp()
        ON MATCH SET
            o.source_chunks=apoc.coll.toSet(coalesce(o.source_chunks,[])+$source_chunks),
            o.updated_at=timestamp()

        MERGE (s)-[r:ONT_REL {relation_type:$rel_type}]->(o)
        ON CREATE SET
            r.confidence=$confidence, r.attributes=$attributes,
            r.lightrag_doc_ids=$lightrag_doc_ids, r.doc_ids=[$doc_id],
            r.created_at=timestamp(), r.updated_at=timestamp()
        ON MATCH SET
            r.doc_ids=apoc.coll.toSet(coalesce(r.doc_ids,[])+[$doc_id]),
            r.lightrag_doc_ids=apoc.coll.toSet(coalesce(r.lightrag_doc_ids,[])+$lightrag_doc_ids),
            r.attributes=$attributes,
            r.confidence=CASE
                WHEN $confidence>coalesce(r.confidence,0) THEN $confidence
                ELSE r.confidence
            END,
            r.updated_at=timestamp()
        """
        params = {
            "t": tenant_id,
            "k": kb_id,
            "doc_id": doc_id,
            "src_type": src_type,
            "src_name": rel["source_name"],
            "tgt_type": tgt_type,
            "tgt_name": rel["target_name"],
            "rel_type": rel["relation_type"],
            "confidence": rel.get("confidence", 1.0),
            "attributes": json.dumps(rel.get("attributes", {}), ensure_ascii=False),
            "lightrag_doc_ids": rel.get("lightrag_doc_ids", []),
            "source_chunks": rel.get("source_chunks", []),
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
        """Endpoint type fallback parsing:
        1. type_hint non-empty use directly
        2. Query DB by name to get existing type (prefer non stub nodes)
        3. If not found return 'Unknown'
        """
        if type_hint:
            return type_hint
        # Prefer querying non stub nodes
        cypher = """
        MATCH (e:OntologyEntity {tenant_id:$t, kb_id:$k, canonical_name:$name})
        WHERE coalesce(e.stub,false)=false
        RETURN e.entity_type AS entity_type LIMIT 1
        """
        params = {"t": tenant_id, "k": kb_id, "name": name}
        async with self._driver.session() as session:
            result = await session.run(cypher, params)
            record = await result.single()
            if record:
                return record["entity_type"]
        # No non stub node found, fallback to query stub
        cypher_stub = """
        MATCH (e:OntologyEntity {tenant_id:$t, kb_id:$k, canonical_name:$name})
        RETURN e.entity_type AS entity_type LIMIT 1
        """
        async with self._driver.session() as session:
            result = await session.run(cypher_stub, params)
            record = await result.single()
            if record:
                return record["entity_type"]
        return "Unknown"

    async def delete_by_document(self, tenant_id: str, doc_id: str) -> None:
        """Three-step delete document contributed ontology data, avoid accidentally deleting cross-document shared entities.

        Steps:
          1. Remove document from relation doc_ids; only delete relations that become empty
          2. Remove document from entity doc_ids
          3. Delete orphan entities (doc_ids empty and no relation edges)
        """
        cypher = """
        // Step 1: Relation doc_ids remove -> delete edge if empty
        MATCH (s:OntologyEntity {tenant_id:$t})-[r:ONT_REL]->(o:OntologyEntity {tenant_id:$t})
        WHERE $doc_id IN r.doc_ids
        SET r.doc_ids = [x IN r.doc_ids WHERE x <> $doc_id]
        WITH r WHERE size(r.doc_ids)=0
        DELETE r;

        // Step 2: Entity doc_ids remove
        MATCH (e:OntologyEntity {tenant_id:$t}) WHERE $doc_id IN e.doc_ids
        SET e.doc_ids = [x IN e.doc_ids WHERE x <> $doc_id];

        // Step 3: Delete orphan entities
        MATCH (e:OntologyEntity {tenant_id:$t})
        WHERE size(coalesce(e.doc_ids,[]))=0 AND NOT (e)--()
        DELETE e;
        """
        params = {"t": tenant_id, "doc_id": doc_id}
        async with self._driver.session() as session:
            await session.run(cypher, params)

    # -- Read path (added in second batch Phase C) ------------------------------

    async def search_entities(
        self, tenant_id: str, kb_id: str, query: str, limit: int = 5
    ) -> list[dict]:
        """Neo4j full-text index search (replaces ILIKE)."""
        cypher = """
        CALL db.index.fulltext.queryNodes('ont_entity_ft', $q) YIELD node, score
        WHERE node.tenant_id=$t AND node.kb_id=$k AND coalesce(node.stub,false)=false
        RETURN node.canonical_name AS name, node.entity_type AS type,
               node.aliases AS aliases, node.attributes AS attributes,
               node.confidence AS confidence, score
        ORDER BY score DESC LIMIT $limit
        """
        params = {"t": tenant_id, "k": kb_id, "q": query, "limit": limit}
        async with self._driver.session() as session:
            result = await session.run(cypher, params)
            rows = [dict(record) async for record in result]
        for row in rows:
            if isinstance(row.get("attributes"), str):
                try:
                    row["attributes"] = json.loads(row["attributes"])
                except (json.JSONDecodeError, TypeError):
                    row["attributes"] = {}
        return rows

    async def neighbors(
        self,
        tenant_id: str,
        kb_id: str,
        entity_name: str,
        hops: int = 1,
        limit: int = 20,
    ) -> dict:
        """Get entity 1-hop neighborhood (for fact/relation type questions)."""
        cypher = """
        MATCH (e:OntologyEntity {tenant_id:$t, kb_id:$k, canonical_name:$name})
        MATCH (e)-[r:ONT_REL]-(n:OntologyEntity {kb_id:$k})
        WITH e, r, n,
             CASE WHEN startNode(r) = e THEN 'outgoing' ELSE 'incoming' END AS rel_dir
        RETURN e.canonical_name AS source,
               collect({
                   source:e.canonical_name,
                   relation_type:r.relation_type,
                   direction:rel_dir,
                   target:n.canonical_name,
                   target_type:n.entity_type
               })[..$limit] AS facts
        """
        params = {"t": tenant_id, "k": kb_id, "name": entity_name, "limit": limit}
        async with self._driver.session() as session:
            result = await session.run(cypher, params)
            record = await result.single()
            if record:
                return dict(record)
            return {"source": entity_name, "facts": []}

    async def list_entity_types(
        self, tenant_id: str, kb_id: str, names: list[str]
    ) -> dict[str, str]:
        """Batch query entity types by name collection (for parse-result overlay)."""
        if not names:
            return {}
        cypher = """
        MATCH (e:OntologyEntity {tenant_id:$t, kb_id:$k})
        WHERE e.canonical_name IN $names AND coalesce(e.stub,false)=false
        RETURN e.canonical_name AS name, e.entity_type AS type
        """
        params = {"t": tenant_id, "k": kb_id, "names": names}
        async with self._driver.session() as session:
            result = await session.run(cypher, params)
            return {record["name"]: record["type"] async for record in result}