#!/usr/bin/python3



from jonex_core.common.repository import BaseRepository

from ..models.domain_service import (
    DomainService,
    ServiceApiKey,
    ServiceKnowledgeBase,
    ServicePermission,
)


class DomainServiceRepository(BaseRepository[DomainService]):
    model = DomainService


class ServiceKnowledgeBaseRepository(BaseRepository[ServiceKnowledgeBase]):
    model = ServiceKnowledgeBase


class ServiceApiKeyRepository(BaseRepository[ServiceApiKey]):
    model = ServiceApiKey


class ServicePermissionRepository(BaseRepository[ServicePermission]):
    model = ServicePermission
