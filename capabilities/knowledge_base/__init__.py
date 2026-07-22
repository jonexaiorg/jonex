#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Knowledge base business capability module (business.knowledge_base.v1)

Responsible for:
- Document CRUD management
- Tenant isolation
- State machine management (pending -> parsing -> ready / failed)
- Async task orchestration (submit atomic-rag task + async reconciliation)
- Soft delete flow
"""

from .capability import KnowledgeBaseCapability
from .dao import KnowledgeDocumentDAO
from .models import DocStatus, KnowledgeDocument
from .service import KnowledgeBaseService

__all__ = [
    "DocStatus",
    "KnowledgeBaseCapability",
    "KnowledgeBaseService",
    "KnowledgeDocument",
    "KnowledgeDocumentDAO",
]
