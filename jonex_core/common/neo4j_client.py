

import logging
import os
from typing import Optional

from neo4j import AsyncGraphDatabase, AsyncDriver

logger = logging.getLogger(__name__)


_driver: Optional[AsyncDriver] = None


def get_neo4j_driver() -> AsyncDriver:

    global _driver
    if _driver is None:
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        if not password:
            raise RuntimeError("NEO4J_PASSWORD must be set before connecting to Neo4j")
        _driver = AsyncGraphDatabase.driver(uri, auth=(username, password))
        logger.info("Neo4j driver created: %s", uri)
    return _driver


async def close_neo4j_driver() -> None:

    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None
        logger.info("Neo4j driver closed")


async def ensure_ontology_schema() -> None:

    driver = get_neo4j_driver()
    async with driver.session() as session:

        await session.run(
            "CREATE CONSTRAINT ont_entity_key IF NOT EXISTS "
            "FOR (e:OntologyEntity) "
            "REQUIRE (e.tenant_id, e.kb_id, e.entity_type, e.canonical_name) IS UNIQUE"
        )


        index_exists = False
        existing_analyzer: Optional[str] = None
        result = await session.run(
            "SHOW INDEXES YIELD name, options "
            "WHERE name = 'ont_entity_ft' "
            "RETURN options AS options"
        )
        record = await result.single()
        if record is not None:
            index_exists = True
            options = record["options"] or {}
            index_config = options.get("indexConfig") or {}
            existing_analyzer = index_config.get("fulltext.analyzer")


        if index_exists and existing_analyzer != "cjk":
            logger.warning(
                "Full-text index ont_entity_ft currently uses analyzer=%s instead of cjk; dropping and recreating it",
                existing_analyzer,
            )
            await session.run("DROP INDEX ont_entity_ft IF EXISTS")
            index_exists = False

        if not index_exists:

            await session.run(
                "CREATE FULLTEXT INDEX ont_entity_ft IF NOT EXISTS "
                "FOR (e:OntologyEntity) ON EACH [e.canonical_name, e.aliases_text] "
                "OPTIONS {indexConfig: {`fulltext.analyzer`: 'cjk'}}"
            )
            logger.info("Neo4j ontology schema initialized (constraints + cjk full-text index, created/rebuilt)")
        else:
            logger.info("Neo4j ontology full-text index already uses the cjk analyzer; skipping rebuild")


        ontology_vector_enabled = os.getenv("ONTOLOGY_VECTOR_ENABLED", "true").lower() in ("1", "true", "yes", "on")
        if ontology_vector_enabled:
            dim = int(os.getenv("EMBEDDING_DIM", "1024"))


            vindex_exists = False
            existing_dim = None
            result = await session.run(
                "SHOW INDEXES YIELD name, options "
                "WHERE name = 'ont_entity_embedding' RETURN options AS options"
            )
            record = await result.single()
            if record is not None:
                vindex_exists = True
                index_config = (record["options"] or {}).get("indexConfig") or {}
                existing_dim = index_config.get("vector.dimensions")


            if vindex_exists and existing_dim is not None and int(existing_dim) != dim:
                logger.warning(
                    "Vector index ont_entity_embedding dimension=%s does not match EMBEDDING_DIM=%d; dropping and recreating it",
                    existing_dim, dim,
                )
                await session.run("DROP INDEX ont_entity_embedding IF EXISTS")
                vindex_exists = False



            if not vindex_exists:
                await session.run(
                    "CREATE VECTOR INDEX ont_entity_embedding IF NOT EXISTS "
                    "FOR (e:OntologyEntity) ON (e.embedding) "
                    "OPTIONS {indexConfig: {"
                    f"  `vector.dimensions`: {dim}, "
                    "  `vector.similarity_function`: 'cosine'"
                    "}}"
                )
                logger.info("Neo4j ontology vector index is ready: ont_entity_embedding dim=%d cosine", dim)
            else:
                logger.info("Neo4j ontology vector index dimension matches (dim=%d); skipping rebuild", dim)