"""
Neo4j graph database connection management

Provides in-process singleton AsyncDriver + schema initialization (constraints + full-text indexes).
knowledge-base-service calls ensure_ontology_schema() on startup to complete initialization.
"""

import logging
import os
from typing import Optional

from neo4j import AsyncGraphDatabase, AsyncDriver

logger = logging.getLogger(__name__)

# In-process driver singleton
_driver: Optional[AsyncDriver] = None


def get_neo4j_driver() -> AsyncDriver:
    """Get AsyncDriver singleton (lazy loading)."""
    global _driver
    if _driver is None:
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "jonex_neo4j_123")
        _driver = AsyncGraphDatabase.driver(uri, auth=(username, password))
        logger.info("Neo4j driver created: %s", uri)
    return _driver


async def close_neo4j_driver() -> None:
    """Close driver singleton (called on process exit or shutdown).

    Note: AsyncDriver.close() is a coroutine, must be awaited.
    """
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None
        logger.info("Neo4j driver closed")


async def ensure_ontology_schema() -> None:
    """Initialize ontology schema: constraints + full-text indexes (idempotent).

    Called when knowledge-base-service starts, failure only warns and does not block service startup.
    """
    driver = get_neo4j_driver()
    async with driver.session() as session:
        # Composite unique key constraint (MERGE depends on it)
        await session.run(
            "CREATE CONSTRAINT ont_entity_key IF NOT EXISTS "
            "FOR (e:OntologyEntity) "
            "REQUIRE (e.tenant_id, e.kb_id, e.entity_type, e.canonical_name) IS UNIQUE"
        )
        # Full-text index (replaces ILIKE)
        await session.run(
            "CREATE FULLTEXT INDEX ont_entity_ft IF NOT EXISTS "
            "FOR (e:OntologyEntity) ON EACH [e.canonical_name, e.aliases_text]"
        )
        logger.info("Neo4j ontology schema initialization completed (constraints + full-text indexes)")