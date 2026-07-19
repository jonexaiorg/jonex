#!/usr/bin/python3



from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import BigInteger, Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from jonex_core.common.database import Base
from jonex_core.common.entity import SoftDeleteMixin, TenantMixin, TimestampMixin


class DocStatus(str, Enum):


    PENDING = "pending"
    PARSING = "parsing"
    READY = "ready"
    FAILED = "failed"
    DELETING = "deleting"
    DELETED = "deleted"


class OntologyStatus(str, Enum):


    PENDING = "pending"
    EXTRACTING = "extracting"
    READY = "ready"
    FAILED = "failed"


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


class KnowledgeDocument(Base, TenantMixin, TimestampMixin, SoftDeleteMixin):


    __tablename__ = "knowledge_documents"
    __table_args__ = {"schema": "knowledge_base"}

    id = Column(String(64), primary_key=True, default=lambda: str(uuid4()))
    file_name = Column(String(512), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_size = Column(BigInteger, nullable=False, default=0)
    mime_type = Column(String(128), nullable=True)
    knowledge_base_id = Column(String(128), nullable=False, index=True)

    storage_backend = Column(String(16), nullable=False, default="local")
    storage_key = Column(String(1024), nullable=True)

    status = Column(String(32), nullable=False, default=DocStatus.PENDING.value, index=True)
    rag_task_id = Column(String(128), nullable=True, index=True)
    rag_doc_ids = Column(JSONB, nullable=False, default=list)
    error_message = Column(Text, nullable=True)

    ontology_status = Column(
        String(32),
        nullable=False,
        default=OntologyStatus.PENDING.value,
        index=True,
    )
    ontology_error = Column(Text, nullable=True)
    ontology_retry_count = Column(Integer, nullable=False, default=0)

    extra_metadata = Column(JSONB, nullable=False, default=dict)


    folder_id = Column(String(64), nullable=True, index=True)

    data_source_type = Column(String(32), nullable=True, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "knowledge_base_id": self.knowledge_base_id,
            "status": self.status,
            "storage_backend": self.storage_backend,
            "storage_key": self.storage_key,
            "rag_task_id": self.rag_task_id,
            "rag_doc_ids": self.rag_doc_ids or [],
            "error_message": self.error_message,
            "ontology_status": self.ontology_status,
            "ontology_error": self.ontology_error,
            "ontology_retry_count": self.ontology_retry_count or 0,
            "folder_id": self.folder_id,
            "data_source_type": self.data_source_type,
            "metadata": self.extra_metadata or {},
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
        }


__all__ = ["DocStatus", "KnowledgeDocument", "OntologyStatus"]
