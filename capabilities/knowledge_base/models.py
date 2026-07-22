#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Knowledge base business capability data model
"""

import hashlib
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from jonex_core.common.database import Base


class DocStatus(str, Enum):
    """Document state machine

    State transition:
        PENDING -> PARSING -> READY
                       \\-> FAILED
        READY -> DELETING -> DELETED
    """
    PENDING = "pending"          # Uploaded, pending parsing
    PARSING = "parsing"          # Parsing
    READY = "ready"              # Indexing completed, searchable
    FAILED = "failed"            # Parsing failed
    DELETING = "deleting"        # Soft deleting (lightrag async deletion)
    DELETED = "deleted"          # Deleted (final state)


class OntologyStatus(str, Enum):
    """Ontology extraction state machine

    State transition:
        ON_PENDING -> ON_EXTRACTING -> ON_READY
                                \\-> ON_FAILED
    """
    ON_PENDING = "pending"           # Pending ontology extraction
    ON_EXTRACTING = "extracting"     # Extracting
    ON_READY = "ready"               # Ontology ready
    ON_FAILED = "failed"             # Extraction failed


class KnowledgeDocument(Base):
    """Business document model (business layer specific)

    Responsibilities:
    - Document CRUD metadata
    - Tenant isolation
    - State machine
    - Reconciliation mapping with atomic-rag tasks (rag_task_id / rag_doc_ids)
    """
    __tablename__ = "knowledge_documents"
    __table_args__ = {"schema": "knowledge_base"}

    id = Column(String(64), primary_key=True, comment="Document ID (UUID)")
    tenant_id = Column(String(64), nullable=False, index=True, comment="Tenant ID")

    # File metadata
    file_name = Column(String(512), nullable=False, comment="Original file name")
    file_path = Column(String(1024), nullable=False, comment="Storage path (MinIO key or local path)")
    file_size = Column(BigInteger, default=0, comment="File size (bytes)")
    mime_type = Column(String(128), nullable=True, comment="MIME type")

    # State machine
    status = Column(
        String(32),
        default=DocStatus.PENDING,
        nullable=False,
        index=True,
        comment="Document status",
    )

    # RAG reconciliation fields
    rag_task_id = Column(String(64), nullable=True, comment="task_id returned by atomic-rag")
    rag_doc_ids = Column(JSONB, default=list, comment="chunk doc_id list returned by lightrag")

    # Error information
    error_message = Column(Text, nullable=True, comment="Parsing failure reason")

    # Ontology extraction status
    ontology_status = Column(
        String(32),
        default=OntologyStatus.ON_PENDING,
        nullable=False,
        comment="Ontology extraction status",
    )
    ontology_error = Column(Text, nullable=True, comment="Ontology extraction failure reason")
    ontology_retry_count = Column(Integer, default=0, comment="Ontology extraction retry count")

    # Extension fields
    extra_metadata = Column(JSONB, default=dict, comment="Extension fields (source, tags, custom attributes)")

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, comment="Created at")
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Updated at",
    )
    is_deleted = Column(Integer, default=0, comment="Hard delete (0-no, 1-yes)")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "status": getattr(self.status, 'value', self.status),
            "rag_task_id": self.rag_task_id,
            "rag_doc_ids": self.rag_doc_ids or [],
            "error_message": self.error_message,
            "ontology_status": getattr(self.ontology_status, 'value', self.ontology_status),
            "ontology_error": self.ontology_error,
            "ontology_retry_count": self.ontology_retry_count or 0,
            "extra_metadata": self.extra_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def normalize_query(query: str) -> str:
    return " ".join((query or "").strip().split())


def build_query_hash(query: str) -> str:
    return hashlib.sha256(normalize_query(query).encode("utf-8")).hexdigest()


class KnowledgeSearchHistory(Base):
    """Search history model

    Deduplicate by (tenant_id, user_id, query_hash, domain_id),
    when same query is searched again, update updated_at and move to top.
    """

    __tablename__ = "knowledge_search_history"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "user_id", "query_hash", "domain_id",
            name="uq_knowledge_search_history_query_domain",
        ),
        Index(
            "idx_knowledge_search_history_tenant_user_time",
            "tenant_id", "user_id", "searched_at",
        ),
        Index(
            "idx_knowledge_search_history_tenant_user_deleted",
            "tenant_id", "user_id", "is_deleted",
        ),
        {"schema": "knowledge_base"},
    )

    id = Column(String(64), primary_key=True, comment="History record ID")
    tenant_id = Column(String(64), nullable=False, index=True, comment="Tenant ID")
    user_id = Column(String(128), nullable=False, index=True, comment="User ID")

    query = Column(Text, nullable=False, comment="Original query text")
    query_hash = Column(String(64), nullable=False, comment="SHA256 of normalized query")
    domain_id = Column(String(128), nullable=False, default="all", comment="Domain ID")
    domain_name = Column(String(128), nullable=True, comment="Domain name")
    mode = Column(String(32), nullable=False, default="hybrid", comment="Search mode")
    top_k = Column(Integer, nullable=False, default=5, comment="Search count")

    status = Column(String(32), nullable=False, default="done", comment="status: done/stopped/error")
    answer_preview = Column(Text, nullable=True, comment="Answer summary (without think and references)")
    reference_count = Column(Integer, nullable=False, default=0, comment="Reference count")
    result_count = Column(Integer, nullable=False, default=0, comment="Result count")
    duration_ms = Column(Integer, nullable=True, comment="Search duration (milliseconds)")

    extra_metadata = Column(JSONB, nullable=False, default=dict, comment="Extension fields")

    searched_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), comment="Search time")
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), comment="Created at")
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        comment="Updated at",
    )
    is_deleted = Column(Boolean, nullable=False, default=False, comment="Soft delete flag")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "query": self.query,
            "searchedAt": self.searched_at.isoformat() if self.searched_at else None,
            "resultCount": self.result_count,
            "domain": self.domain_name,
            "domainId": self.domain_id,
            "status": self.status,
            "answerPreview": self.answer_preview,
            "referenceCount": self.reference_count,
            "durationMs": self.duration_ms,
            "mode": self.mode,
            "topK": self.top_k,
        }
