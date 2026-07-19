

import logging

from jonex_core.capability.atomic.rag.client import get_rag_client
from jonex_core.common.database import get_db_session
from jonex_core.common.exceptions import ResourceNotFoundError
from jonex_core.common.tenant import require_tenant

from ..models import OntologyStatus
from ..repository import KnowledgeDocumentRepository

logger = logging.getLogger(__name__)


class OntologyService:
    async def retry_extract(
        self,
        tenant_id: str,
        document_id: str,
        knowledge_base_id: str,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)


        try:
            from .ontology_compiler import OntologyCompiler
            schema = await OntologyCompiler().get_compiled_schema(tenant_id, knowledge_base_id, auto_compile=True)
            if schema is None:
                logger.warning(
                    "Ontology retry skipped for doc %s - no compiled schema (KB %s)",
                    document_id, knowledge_base_id,
                )
        except Exception as e:
            logger.warning("Compiled schema check failed for doc %s: %s", document_id, e)

        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_by_id(document_id, tenant_id)
            if doc is None or doc.knowledge_base_id != knowledge_base_id:
                raise ResourceNotFoundError(message="Knowledge document not found")
            await repo.set_ontology_status(doc, OntologyStatus.EXTRACTING, increment_retry=True)
            file_path = doc.file_path

        result = await get_rag_client().retry_ontology_extract(
            document_id=document_id,
            knowledge_base_id=knowledge_base_id,
            tenant_id=tenant_id,
            file_path=file_path,
        )

        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_required(document_id, tenant_id)
            status = OntologyStatus.READY if result.get("success", True) else OntologyStatus.FAILED
            await repo.set_ontology_status(doc, status, error=result.get("error"))
            doc.extra_metadata = {**(doc.extra_metadata or {}), "ontology_retry_result": result}
            return doc.to_dict()


__all__ = ["OntologyService"]
